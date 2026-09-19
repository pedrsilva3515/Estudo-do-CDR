"""Protótipo somente leitura para validar seleção visual de objetos do Corel."""
from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path

from .container import abrir_cdr
from .ocr import executar_ocr
from .pedido import (
    _candidatos_arte,
    _evidencias_textuais,
    _inventario_geometrico,
    parse_dimensoes,
    parse_quantidade,
)
from .visao_api import extrair_imagem_analise


def _caixa_de_centros(item: dict) -> dict:
    largura = float(item["largura_cm"])
    altura = float(item["altura_cm"])
    centros = item.get("posicoes_centro_cm") or []
    return {
        "esquerda": min(c["x"] - largura / 2 for c in centros),
        "direita": max(c["x"] + largura / 2 for c in centros),
        "base": min(c["y"] - altura / 2 for c in centros),
        "topo": max(c["y"] + altura / 2 for c in centros),
    }


def _area_caixa(caixa: dict) -> float:
    return max(0.0, caixa["direita"] - caixa["esquerda"]) * max(0.0, caixa["topo"] - caixa["base"])


def _contem_caixa(externa: dict, interna: dict, tolerancia_cm: float = 0.05) -> bool:
    return (
        externa["esquerda"] <= interna["esquerda"] + tolerancia_cm
        and externa["direita"] >= interna["direita"] - tolerancia_cm
        and externa["base"] <= interna["base"] + tolerancia_cm
        and externa["topo"] >= interna["topo"] - tolerancia_cm
    )


def _anotar_hierarquia(candidatos: list[dict]) -> None:
    """Separa composições externas de detalhes internos sem apagar hipóteses."""
    for candidato in candidatos:
        caixa = candidato["caixa_cm"]
        area = _area_caixa(caixa)
        contenedores = [
            outro for outro in candidatos
            if outro is not candidato
            and _area_caixa(outro["caixa_cm"]) > area * 1.05
            and _contem_caixa(outro["caixa_cm"], caixa)
        ]
        pai = min(contenedores, key=lambda item: _area_caixa(item["caixa_cm"]), default=None)
        candidato["pai_id"] = pai["id"] if pai else None

    por_id = {item["id"]: item for item in candidatos}
    for candidato in candidatos:
        profundidade = 0
        pai_id = candidato["pai_id"]
        visitados = set()
        while pai_id and pai_id not in visitados:
            visitados.add(pai_id)
            profundidade += 1
            pai_id = por_id[pai_id]["pai_id"]
        candidato["camada"] = profundidade

    for candidato in candidatos:
        pai = por_id.get(candidato["pai_id"])
        mesma_medida_repetida = bool(
            pai
            and pai["quantidade_geometrica"] > 1
            and abs(pai["largura_cm"] - candidato["largura_cm"]) <= 0.05
            and abs(pai["altura_cm"] - candidato["altura_cm"]) <= 0.05
        )
        proporcao_item = (
            (candidato["largura_cm"] * candidato["altura_cm"])
            / max(1e-9, pai["largura_cm"] * pai["altura_cm"])
            if pai else 1.0
        )
        candidato["visivel_inicialmente"] = candidato["camada"] == 0 or (
            candidato["camada"] == 1
            and not mesma_medida_repetida
            and proporcao_item >= 0.12
        )

    for candidato in candidatos:
        candidato["filhos_ids"] = [
            outro["id"] for outro in candidatos if outro["pai_id"] == candidato["id"]
        ]


def _caixa_texto_cm(evidencia: dict) -> dict:
    caixa = evidencia["caixa_mm"]
    return {chave: float(caixa[chave]) / 10 for chave in ("esquerda", "direita", "base", "topo")}


def detectar_blocos_producao(candidatos: list[dict], evidencias: list[dict]) -> list[dict]:
    """Deriva seleções operacionais que não estavam agrupadas no CDR.

    A primeira regra validada cobre um quadro que contém uma instrução de
    adesivos recortados "do mesmo tamanho" e, abaixo dela, os objetos soltos que
    o operador enviará juntos para recorte. A medida vem da união dos objetos,
    nunca da moldura nem do texto de instrução.
    """
    evidencias_caixa = [(item, _caixa_texto_cm(item)) for item in evidencias if item.get("caixa_mm")]
    materiais = [
        (item, caixa) for item, caixa in evidencias_caixa
        if item.get("material") and "recort" in str(item["material"].get("acabamento") or "").casefold()
    ]
    mesmo_tamanho = [
        (item, caixa) for item, caixa in evidencias_caixa
        if "mesmo tamanho" in item.get("texto", "").casefold()
    ]
    blocos = []
    for instrucao, caixa_instrucao in materiais:
        complementos = [
            (item, caixa) for item, caixa in mesmo_tamanho
            if abs((caixa["esquerda"] + caixa["direita"]) / 2 - (caixa_instrucao["esquerda"] + caixa_instrucao["direita"]) / 2) <= 20
            and abs(caixa["topo"] - caixa_instrucao["base"]) <= 20
        ]
        if not complementos:
            continue
        complemento, caixa_complemento = min(
            complementos, key=lambda par: abs(par[1]["topo"] - caixa_instrucao["base"])
        )
        cabecalhos = [(instrucao, caixa_instrucao), (complemento, caixa_complemento)]
        molduras = []
        for candidato in candidatos:
            caixa = candidato["caixa_cm"]
            if all(_contem_caixa(caixa, caixa_cabecalho, tolerancia_cm=0.2) for _, caixa_cabecalho in cabecalhos):
                contidos = [item for item, caixa_texto in evidencias_caixa if _contem_caixa(caixa, caixa_texto, 0.2)]
                if len(contidos) >= 5:
                    molduras.append(candidato)
        if not molduras:
            continue
        moldura = min(molduras, key=lambda item: _area_caixa(item["caixa_cm"]))
        limite_superior = min(caixa["base"] for _, caixa in cabecalhos)
        ids_cabecalho = {id(item) for item, _ in cabecalhos}
        conteudo = [
            (item, caixa) for item, caixa in evidencias_caixa
            if id(item) not in ids_cabecalho
            and _contem_caixa(moldura["caixa_cm"], caixa, tolerancia_cm=0.2)
            and caixa["topo"] < limite_superior
            and not item.get("dimensoes")
            and not item.get("material")
        ]
        if len(conteudo) < 2:
            continue
        uniao = {
            "esquerda": min(caixa["esquerda"] for _, caixa in conteudo),
            "direita": max(caixa["direita"] for _, caixa in conteudo),
            "base": min(caixa["base"] for _, caixa in conteudo),
            "topo": max(caixa["topo"] for _, caixa in conteudo),
        }
        texto_instrucao = instrucao.get("texto", "")
        material = "adesivo branco" if "branco" in texto_instrucao.casefold() else instrucao["material"].get("material")
        blocos.append({
            "id": f"P{len(blocos) + 1:02d}", "origem": "bloco_producao_derivado",
            "quantidade_geometrica": 1,
            "largura_cm": round(uniao["direita"] - uniao["esquerda"], 3),
            "altura_cm": round(uniao["topo"] - uniao["base"], 3),
            "caixa_cm": uniao, "posicoes_centro_cm": [{
                "x": round((uniao["esquerda"] + uniao["direita"]) / 2, 3),
                "y": round((uniao["base"] + uniao["topo"]) / 2, 3),
            }],
            "tipos": ["selecao_operacional"], "moldura_id": moldura["id"],
            "instrucoes": [item.get("texto") for item, _ in cabecalhos],
            "objetos_incluidos": [item.get("texto") for item, _ in conteudo],
            "material_sugerido": material,
            "acabamento_sugerido": instrucao["material"].get("acabamento"),
            "regra": "mesmo_tamanho_em_moldura_com_uniao_dos_objetos_abaixo",
        })
    return blocos


def _sobreposicao_horizontal(a: dict, b: dict) -> float:
    intersecao = max(0.0, min(a["direita"], b["direita"]) - max(a["esquerda"], b["esquerda"]))
    return intersecao / max(1e-9, min(a["direita"] - a["esquerda"], b["direita"] - b["esquerda"]))


def associar_instrucoes_regionais(
    leituras_ocr: list[dict], candidatos: list[dict], limites: dict, tamanho_imagem: tuple[int, int],
) -> list[dict]:
    """Liga quantidade/dimensão do OCR a candidatos usando medida e posição."""
    largura_px, altura_px = tamanho_imagem
    intervalo_x = limites["direita"] - limites["esquerda"]
    intervalo_y = limites["topo"] - limites["base"]

    def caixa_ocr_cm(leitura: dict) -> dict:
        pontos = leitura["poligono_px"]
        xs = [p[0] for p in pontos]
        ys = [p[1] for p in pontos]
        return {
            "esquerda": limites["esquerda"] + min(xs) / largura_px * intervalo_x,
            "direita": limites["esquerda"] + max(xs) / largura_px * intervalo_x,
            "topo": limites["topo"] - min(ys) / altura_px * intervalo_y,
            "base": limites["topo"] - max(ys) / altura_px * intervalo_y,
        }

    principais = [item for item in candidatos if item.get("visivel_inicialmente", True)]
    associacoes = []
    for leitura in leituras_ocr:
        texto = leitura.get("texto", "")
        quantidade = parse_quantidade(texto)
        if quantidade is None:
            continue
        valor = quantidade[0]
        dimensoes = parse_dimensoes(texto)
        caixa_texto = caixa_ocr_cm(leitura)
        alvos: list[tuple[dict, str, float]] = []
        if dimensoes:
            largura_cm = dimensoes["largura_mm"] / 10
            altura_cm = dimensoes["altura_mm"] / 10
            compativeis = []
            for candidato in principais:
                cw, ch = candidato["largura_cm"], candidato["altura_cm"]
                erro = min(abs(cw - largura_cm) + abs(ch - altura_cm), abs(cw - altura_cm) + abs(ch - largura_cm))
                if erro > 0.5:
                    continue
                caixa = candidato["caixa_cm"]
                centro_x = (caixa["esquerda"] + caixa["direita"]) / 2
                centro_texto_x = (caixa_texto["esquerda"] + caixa_texto["direita"]) / 2
                distancia_x = abs(centro_x - centro_texto_x) / max(1.0, intervalo_x)
                abaixo = caixa["topo"] <= caixa_texto["base"] + intervalo_y * 0.03
                penalidade_posicao = distancia_x + (0 if abaixo else 0.2)
                bonus_quantidade = -0.3 if candidato.get("quantidade_geometrica") == valor else 0
                bonus_repeticao = -0.05 if candidato.get("quantidade_geometrica", 1) > 1 else 0
                compativeis.append((erro + penalidade_posicao + bonus_quantidade + bonus_repeticao, candidato))
            if compativeis:
                _, melhor = min(compativeis, key=lambda par: par[0])
                alvos = [(melhor, "dimensao_explicita", 0.99)]
        elif "de cada" in texto.casefold():
            margem = max(2.0, (caixa_texto["direita"] - caixa_texto["esquerda"]) * 0.08)
            faixa = {**caixa_texto, "esquerda": caixa_texto["esquerda"] - margem, "direita": caixa_texto["direita"] + margem}
            elegiveis = [
                candidato for candidato in principais
                if faixa["esquerda"] <= (candidato["caixa_cm"]["esquerda"] + candidato["caixa_cm"]["direita"]) / 2 <= faixa["direita"]
                and candidato["caixa_cm"]["topo"] < caixa_texto["base"]
            ]
            if elegiveis:
                topo_mais_proximo = max(item["caixa_cm"]["topo"] for item in elegiveis)
                tolerancia_vertical = max(5.0, intervalo_y * 0.08)
                alvos = [
                    (item, "quantidade_de_cada", 0.97) for item in elegiveis
                    if topo_mais_proximo - item["caixa_cm"]["topo"] <= tolerancia_vertical
                ]
        else:
            elegiveis = []
            for candidato in principais:
                caixa = candidato["caixa_cm"]
                if caixa["topo"] >= caixa_texto["base"]:
                    continue
                sobreposicao = _sobreposicao_horizontal(caixa_texto, caixa)
                centro_x = (caixa["esquerda"] + caixa["direita"]) / 2
                dentro = caixa_texto["esquerda"] <= centro_x <= caixa_texto["direita"]
                if sobreposicao >= 0.25 or dentro:
                    distancia_vertical = caixa_texto["base"] - caixa["topo"]
                    elegiveis.append((distancia_vertical, -sobreposicao, candidato))
            if elegiveis:
                _, _, melhor = min(elegiveis, key=lambda item: (item[0], item[1]))
                alvos = [(melhor, "quantidade_proxima", 0.9)]

        for candidato, regra, confianca in alvos:
            associacoes.append({
                "texto": texto, "confianca_ocr": leitura.get("confianca"),
                "quantidade": valor, "candidato_id": candidato["id"],
                "largura_cm": round(candidato["largura_cm"], 3),
                "altura_cm": round(candidato["altura_cm"], 3),
                "regra": regra, "confianca_associacao": confianca,
                "caixa_texto_cm": {chave: round(valor_caixa, 3) for chave, valor_caixa in caixa_texto.items()},
            })
    vistos = set()
    unicas = []
    for associacao in associacoes:
        chave = (associacao["texto"].casefold(), associacao["candidato_id"], associacao["quantidade"])
        if chave not in vistos:
            vistos.add(chave)
            unicas.append(associacao)
    return unicas


def extrair_associacoes_regionais(caminho: Path, catalogo: dict) -> dict:
    """Executa OCR na imagem limpa e devolve suas associações auditáveis."""
    from PIL import Image

    imagem_extraida = extrair_imagem_analise(caminho)
    limites = catalogo.get("limites_conteudo_cm")
    if imagem_extraida is None or not limites:
        return {"leituras_ocr": [], "associacoes": []}
    bytes_imagem = imagem_extraida[0]
    with Image.open(BytesIO(bytes_imagem)) as imagem:
        tamanho = imagem.size
    leituras = executar_ocr(bytes_imagem)
    hipoteses = catalogo["candidatos"] + catalogo.get("blocos_producao", [])
    return {
        "leituras_ocr": leituras,
        "associacoes": associar_instrucoes_regionais(leituras, hipoteses, limites, tamanho),
    }


def extrair_candidatos_agente(caminho: Path) -> dict:
    """Cria um catálogo de caixas medíveis sem decidir quais são produtos."""
    with abrir_cdr(caminho) as doc:
        estrutura = list(doc.estrutura())
        profundos = _inventario_geometrico(doc)
        rasos = _candidatos_arte(doc)
        evidencias = _evidencias_textuais(doc)

    candidatos = []
    for item in profundos:
        candidatos.append({
            "origem": item["origem"],
            "quantidade_geometrica": int(item.get("quantidade_sugerida") or 1),
            "largura_cm": float(item["largura_cm"]),
            "altura_cm": float(item["altura_cm"]),
            "posicoes_centro_cm": item.get("posicoes_centro_cm") or [],
            "tipos": item.get("tipos") or [],
            "caixa_cm": _caixa_de_centros(item),
        })
    for item in rasos:
        caixa = item["caixa"]
        centro = {
            "x": (caixa.esquerda + caixa.direita) / 200_000,
            "y": (caixa.base + caixa.topo) / 200_000,
        }
        proposta = {
            "origem": "caixa_externa_rasa", "quantidade_geometrica": 1,
            "largura_cm": item["largura_mm"] / 10,
            "altura_cm": item["altura_mm"] / 10,
            "posicoes_centro_cm": [centro], "tipos": [item["tipo"]],
            "caixa_cm": {
                "esquerda": caixa.esquerda / 100_000, "direita": caixa.direita / 100_000,
                "base": caixa.base / 100_000, "topo": caixa.topo / 100_000,
            },
        }
        duplicado = any(
            anterior["quantidade_geometrica"] == 1
            and abs(anterior["largura_cm"] - proposta["largura_cm"]) <= 0.03
            and abs(anterior["altura_cm"] - proposta["altura_cm"]) <= 0.03
            and abs(anterior["posicoes_centro_cm"][0]["x"] - centro["x"]) <= 0.03
            and abs(anterior["posicoes_centro_cm"][0]["y"] - centro["y"]) <= 0.03
            for anterior in candidatos if anterior["posicoes_centro_cm"]
        )
        if not duplicado:
            candidatos.append(proposta)

    candidatos.sort(key=lambda item: (
        item["caixa_cm"]["esquerda"], -item["caixa_cm"]["topo"],
        -(item["largura_cm"] * item["altura_cm"]),
    ))
    for indice, item in enumerate(candidatos, 1):
        item["id"] = f"A{indice:02d}"
    _anotar_hierarquia(candidatos)
    blocos_producao = detectar_blocos_producao(candidatos, evidencias)

    caixas_topo = [
        item.caixa for item in estrutura
        if item.caixa is not None and not item.ancestrais and item.tipo in {"obj", "grp"}
    ]
    limites = None
    if caixas_topo:
        limites = {
            "esquerda": min(c.esquerda for c in caixas_topo) / 100_000,
            "direita": max(c.direita for c in caixas_topo) / 100_000,
            "base": min(c.base for c in caixas_topo) / 100_000,
            "topo": max(c.topo for c in caixas_topo) / 100_000,
        }
    return {
        "arquivo": Path(caminho).name,
        "limites_conteudo_cm": limites,
        "candidatos": candidatos,
        "blocos_producao": blocos_producao,
        "evidencias_textuais": evidencias,
    }


def avaliar_cobertura_geometrica(candidatos: list[dict], esperado: dict, tolerancia_mm: float = 2.0) -> dict:
    """Mede o teto da arquitetura: existe algum candidato para cada item correto?"""
    detalhes = []
    usos = [0 for _ in candidatos]
    for item in esperado.get("itens", []):
        dimensoes = item.get("dimensoes") or {}
        quantidade = int((item.get("quantidade") or {}).get("valor") or 0)
        largura = float(dimensoes.get("largura_mm") or 0)
        altura = float(dimensoes.get("altura_mm") or 0)
        opcoes = []
        for indice, candidato in enumerate(candidatos):
            capacidade = max(1, int(candidato.get("quantidade_geometrica") or 1))
            custo = capacidade if quantidade == capacidade else 1
            if usos[indice] + custo > capacidade:
                continue
            cw, ch = candidato["largura_cm"] * 10, candidato["altura_cm"] * 10
            erro = min(abs(cw - largura) + abs(ch - altura), abs(cw - altura) + abs(ch - largura))
            if erro <= tolerancia_mm * 2:
                opcoes.append((erro, indice, candidato["id"]))
        if opcoes:
            erro, indice, candidato_id = min(opcoes)
            candidato = candidatos[indice]
            capacidade = max(1, int(candidato.get("quantidade_geometrica") or 1))
            usos[indice] += capacidade if quantidade == capacidade else 1
            detalhes.append({
                "encontrado": True, "candidato": candidato_id, "erro_total_mm": round(erro, 3),
                "quantidade_esperada": quantidade,
                "quantidade_geometrica": candidato["quantidade_geometrica"],
                "quantidade_geometrica_compativel": candidato["quantidade_geometrica"] == quantidade,
            })
        else:
            detalhes.append({
                "encontrado": False, "candidato": None,
                "esperado": {"quantidade": quantidade, "largura_mm": largura, "altura_mm": altura},
            })
    encontrados = sum(item["encontrado"] for item in detalhes)
    total = len(detalhes)
    return {
        "itens_encontrados": encontrados, "itens_esperados": total,
        "cobertura": encontrados / total if total else 1.0,
        "detalhes": detalhes,
    }


def gerar_atlas_candidatos(caminho: Path, catalogo: dict, pasta_saida: Path, por_pagina: int = 12) -> list[Path]:
    """Gera visão geral identificada e páginas de recortes para a IA/agente."""
    from PIL import Image, ImageDraw, ImageFont

    imagem_extraida = extrair_imagem_analise(caminho)
    if imagem_extraida is None:
        return []
    imagem = Image.open(BytesIO(imagem_extraida[0])).convert("RGB")
    limites = catalogo.get("limites_conteudo_cm")
    if not limites:
        return []
    pasta_saida.mkdir(parents=True, exist_ok=True)
    fonte = ImageFont.load_default(size=20)
    largura, altura = imagem.size
    intervalo_x = max(1e-9, limites["direita"] - limites["esquerda"])
    intervalo_y = max(1e-9, limites["topo"] - limites["base"])

    def pixel_x(x):
        return int(round((x - limites["esquerda"]) / intervalo_x * largura))

    def pixel_y(y):
        return int(round((limites["topo"] - y) / intervalo_y * altura))

    geral = imagem.copy()
    desenho = ImageDraw.Draw(geral)
    for candidato in catalogo["candidatos"]:
        caixa = candidato["caixa_cm"]
        retangulo = (pixel_x(caixa["esquerda"]), pixel_y(caixa["topo"]), pixel_x(caixa["direita"]), pixel_y(caixa["base"]))
        desenho.rectangle(retangulo, outline="#ff2020", width=4)
        desenho.text((retangulo[0] + 3, retangulo[1] + 3), candidato["id"], fill="#ff2020", font=fonte, stroke_width=2, stroke_fill="white")
    visao = pasta_saida / "visao-geral.png"
    geral.save(visao)
    saidas = [visao]

    principais = [item for item in catalogo["candidatos"] if item["visivel_inicialmente"]]
    entrada = imagem.copy()
    desenho_entrada = ImageDraw.Draw(entrada)
    for candidato in principais:
        caixa = candidato["caixa_cm"]
        retangulo = (pixel_x(caixa["esquerda"]), pixel_y(caixa["topo"]), pixel_x(caixa["direita"]), pixel_y(caixa["base"]))
        desenho_entrada.rectangle(retangulo, outline="#ff2020", width=4)
        desenho_entrada.text((retangulo[0] + 3, retangulo[1] + 3), candidato["id"], fill="#ff2020", font=fonte, stroke_width=2, stroke_fill="white")
    legenda_h = max(90, 34 * ((len(principais) + 2) // 3))
    folha = Image.new("RGB", (max(1260, entrada.width), entrada.height + legenda_h), "white")
    folha.paste(entrada, ((folha.width - entrada.width) // 2, 0))
    desenho_folha = ImageDraw.Draw(folha)
    coluna_w = folha.width // 3
    for indice, candidato in enumerate(principais):
        coluna, linha = indice % 3, indice // 3
        texto = (
            f"{candidato['id']}  geom={candidato['quantidade_geometrica']}  "
            f"{candidato['largura_cm']:.2f} x {candidato['altura_cm']:.2f} cm"
        )
        desenho_folha.text((coluna * coluna_w + 12, entrada.height + 12 + linha * 34), texto, fill="black", font=fonte)
    entrada_path = pasta_saida / "entrada-agente.png"
    folha.save(entrada_path)
    saidas.append(entrada_path)

    if catalogo.get("blocos_producao"):
        blocos = imagem.copy()
        desenho_blocos = ImageDraw.Draw(blocos)
        for bloco in catalogo["blocos_producao"]:
            caixa = bloco["caixa_cm"]
            retangulo = (pixel_x(caixa["esquerda"]), pixel_y(caixa["topo"]), pixel_x(caixa["direita"]), pixel_y(caixa["base"]))
            desenho_blocos.rectangle(retangulo, outline="#00a060", width=6)
            rotulo = f"{bloco['id']} {bloco['largura_cm']:.2f} x {bloco['altura_cm']:.2f} cm"
            desenho_blocos.text((retangulo[0] + 4, retangulo[1] + 4), rotulo, fill="#008050", font=fonte, stroke_width=2, stroke_fill="white")
        blocos_path = pasta_saida / "blocos-producao.png"
        blocos.save(blocos_path)
        saidas.append(blocos_path)

    associacoes = catalogo.get("ocr_regional", {}).get("associacoes", [])
    if associacoes:
        mapa = imagem.copy()
        desenho_mapa = ImageDraw.Draw(mapa)
        por_id = {
            item["id"]: item
            for item in catalogo["candidatos"] + catalogo.get("blocos_producao", [])
        }
        for associacao in associacoes:
            candidato = por_id.get(associacao["candidato_id"])
            if candidato is None:
                continue
            texto = associacao["caixa_texto_cm"]
            alvo = candidato["caixa_cm"]
            caixa_texto_px = (pixel_x(texto["esquerda"]), pixel_y(texto["topo"]), pixel_x(texto["direita"]), pixel_y(texto["base"]))
            caixa_alvo_px = (pixel_x(alvo["esquerda"]), pixel_y(alvo["topo"]), pixel_x(alvo["direita"]), pixel_y(alvo["base"]))
            desenho_mapa.rectangle(caixa_texto_px, outline="#ff8c00", width=5)
            desenho_mapa.rectangle(caixa_alvo_px, outline="#0068d9", width=5)
            origem = ((caixa_texto_px[0] + caixa_texto_px[2]) // 2, caixa_texto_px[3])
            destino = ((caixa_alvo_px[0] + caixa_alvo_px[2]) // 2, caixa_alvo_px[1])
            desenho_mapa.line((origem, destino), fill="#00a060", width=4)
            rotulo = f"{associacao['quantidade']} un -> {associacao['candidato_id']}"
            desenho_mapa.text((origem[0] + 4, origem[1] + 4), rotulo, fill="#006840", font=fonte, stroke_width=2, stroke_fill="white")
        mapa_path = pasta_saida / "associacoes-regionais.png"
        mapa.save(mapa_path)
        saidas.append(mapa_path)

    candidatos = catalogo["candidatos"]
    for pagina, inicio in enumerate(range(0, len(candidatos), por_pagina), 1):
        lote = candidatos[inicio:inicio + por_pagina]
        colunas, tile_w, tile_h = 3, 420, 330
        linhas = (len(lote) + colunas - 1) // colunas
        atlas = Image.new("RGB", (colunas * tile_w, linhas * tile_h), "white")
        for posicao, candidato in enumerate(lote):
            caixa = candidato["caixa_cm"]
            pad_x = max(candidato["largura_cm"] * 0.12, intervalo_x * 0.004)
            pad_y = max(candidato["altura_cm"] * 0.12, intervalo_y * 0.004)
            esquerda = max(0, pixel_x(caixa["esquerda"] - pad_x))
            direita = min(largura, pixel_x(caixa["direita"] + pad_x))
            topo = max(0, pixel_y(caixa["topo"] + pad_y))
            base = min(altura, pixel_y(caixa["base"] - pad_y))
            if direita <= esquerda or base <= topo:
                continue
            recorte = imagem.crop((esquerda, topo, direita, base))
            recorte.thumbnail((tile_w - 20, tile_h - 70))
            x0 = (posicao % colunas) * tile_w
            y0 = (posicao // colunas) * tile_h
            atlas.paste(recorte, (x0 + (tile_w - recorte.width) // 2, y0 + 50))
            rotulo = (
                f"{candidato['id']}  q={candidato['quantidade_geometrica']}  "
                f"{candidato['largura_cm']:.2f} x {candidato['altura_cm']:.2f} cm"
            )
            ImageDraw.Draw(atlas).text((x0 + 8, y0 + 12), rotulo, fill="black", font=fonte)
        destino = pasta_saida / f"candidatos-{pagina:02d}.png"
        atlas.save(destino)
        saidas.append(destino)
    return saidas


def gravar_manifesto(catalogo: dict, esperado: dict, cobertura: dict, destino: Path) -> None:
    destino.write_text(json.dumps({
        "catalogo": catalogo, "esperado": esperado, "cobertura_geometrica": cobertura,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
