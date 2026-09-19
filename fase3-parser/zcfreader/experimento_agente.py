"""Protótipo somente leitura para validar seleção visual de objetos do Corel."""
from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path

from .container import abrir_cdr
from .pedido import _candidatos_arte, _evidencias_textuais, _inventario_geometrico
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
