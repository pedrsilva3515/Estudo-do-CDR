"""Protótipo somente leitura para validar seleção visual de objetos do Corel."""
from __future__ import annotations

from io import BytesIO
import json
from pathlib import Path
import re
import unicodedata

from .container import abrir_cdr
from .ocr import executar_ocr
from .pedido import (
    _candidatos_arte,
    _estrutura_visivel,
    _evidencias_textuais,
    _inventario_geometrico,
    parse_dimensoes,
    parse_material,
    parse_quantidade,
    interpretar_nome_arquivo,
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


def _separar_regioes_contiguas(item: dict) -> list[dict]:
    """Separa ocorrências da mesma medida quando pertencem a ilhas espaciais."""
    posicoes = item.get("posicoes_centro_cm") or []
    if len(posicoes) <= 1:
        return [item]
    largura = float(item["largura_cm"])
    altura = float(item["altura_cm"])
    pendentes = set(range(len(posicoes)))
    componentes = []
    while pendentes:
        componente = {pendentes.pop()}
        fila = list(componente)
        while fila:
            atual = fila.pop()
            ligados = []
            for indice in pendentes:
                dx = abs(posicoes[atual]["x"] - posicoes[indice]["x"])
                dy = abs(posicoes[atual]["y"] - posicoes[indice]["y"])
                distancia_bordas_x = max(0.0, dx - largura)
                distancia_bordas_y = max(0.0, dy - altura)
                if (
                    distancia_bordas_x <= max(1.0, largura * 0.25)
                    and distancia_bordas_y <= max(1.0, altura * 0.25)
                ):
                    ligados.append(indice)
            for indice in ligados:
                pendentes.remove(indice)
                componente.add(indice)
                fila.append(indice)
        componentes.append(sorted(componente))
    if len(componentes) == 1:
        return [item]
    regioes = []
    for numero, componente in enumerate(componentes, 1):
        copia = dict(item)
        copia["posicoes_centro_cm"] = [posicoes[indice] for indice in componente]
        copia["quantidade_sugerida"] = len(componente)
        copia["regiao_medida"] = numero
        copia["total_regioes_mesma_medida"] = len(componentes)
        regioes.append(copia)
    return regioes


def _area_caixa(caixa: dict) -> float:
    return max(0.0, caixa["direita"] - caixa["esquerda"]) * max(0.0, caixa["topo"] - caixa["base"])


def _contem_caixa(externa: dict, interna: dict, tolerancia_cm: float = 0.05) -> bool:
    return (
        externa["esquerda"] <= interna["esquerda"] + tolerancia_cm
        and externa["direita"] >= interna["direita"] - tolerancia_cm
        and externa["base"] <= interna["base"] + tolerancia_cm
        and externa["topo"] >= interna["topo"] - tolerancia_cm
    )


def _coincide_caixa(a: dict, b: dict, tolerancia_cm: float = 0.15) -> bool:
    return all(abs(a[chave] - b[chave]) <= tolerancia_cm for chave in ("esquerda", "direita", "base", "topo"))


def _anotar_hierarquia(candidatos: list[dict], recipientes_powerclip: list[dict] | None = None) -> None:
    """Separa composições externas de detalhes internos sem apagar hipóteses.

    ``recipientes_powerclip`` são as caixas (cm) das máscaras de PowerClip. Um
    PowerClip é uma peça única: o que está dentro da máscara é parte dela, e não
    produto separado, ao contrário de uma montagem com vários produtos.
    """
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

    for recipiente in recipientes_powerclip or []:
        donos = [c for c in candidatos if _coincide_caixa(c["caixa_cm"], recipiente)]
        dono = min(donos, key=lambda c: (c.get("origem") != "caixa_externa_rasa", c["id"]), default=None)
        for candidato in donos:
            if candidato is not dono:  # mesma caixa da máscara: duplicata da própria peça
                candidato["visivel_inicialmente"] = False
                candidato["pai_id"] = dono["id"]
        for candidato in candidatos:
            if candidato in donos or not _contem_caixa(recipiente, candidato["caixa_cm"], 0.15):
                continue
            candidato["interno_powerclip"] = True
            candidato["visivel_inicialmente"] = False
            if dono is not None and (candidato["pai_id"] is None or por_id[candidato["pai_id"]].get("visivel_inicialmente")):
                candidato["pai_id"] = dono["id"]
    if recipientes_powerclip:
        # Peças internas continuam no catálogo (ver_detalhe mostra os filhos),
        # mas não disputam com o produto na lista principal.
        for candidato in candidatos:
            if candidato.get("interno_powerclip"):
                candidato["camada"] = max(candidato["camada"], 1)

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

    leituras_com_caixa = [(leitura, caixa_ocr_cm(leitura)) for leitura in leituras_ocr]
    principais = [item for item in candidatos if item.get("visivel_inicialmente", True)]
    associacoes = []
    for leitura, caixa_texto in leituras_com_caixa:
        texto = leitura.get("texto", "")
        quantidade = parse_quantidade(texto)
        if quantidade is None:
            continue
        valor = quantidade[0]
        dimensoes = parse_dimensoes(texto)
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
                "quantidade_ocorrencias_desenhadas": candidato.get("quantidade_geometrica", 1),
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
    areas = []
    for leitura, caixa in leituras_com_caixa:
        match = re.search(r"(?i)(\d+(?:[.,]\d+)?)\s*m\s*[²2]\b", leitura.get("texto", ""))
        if match:
            areas.append((float(match.group(1).replace(",", ".")), leitura, caixa))
    por_id = {item["id"]: item for item in principais}
    areas_usadas = set()
    for associacao in unicas:
        candidato = por_id.get(associacao["candidato_id"])
        if candidato is None:
            continue
        caixa = candidato["caixa_cm"]
        centro_x = (caixa["esquerda"] + caixa["direita"]) / 2
        opcoes = []
        for indice, (area_m2, leitura, caixa_area) in enumerate(areas):
            if indice in areas_usadas or caixa_area["topo"] > caixa["base"] + intervalo_y * 0.03:
                continue
            centro_area_x = (caixa_area["esquerda"] + caixa_area["direita"]) / 2
            distancia_x = abs(centro_area_x - centro_x)
            distancia_y = max(0.0, caixa["base"] - caixa_area["topo"])
            if distancia_x <= max(candidato["largura_cm"], caixa_area["direita"] - caixa_area["esquerda"]):
                opcoes.append((distancia_y + distancia_x * 0.25, indice, area_m2, leitura))
        if not opcoes:
            if associacao["regra"] == "quantidade_de_cada":
                associacao["interpretacao_quantidade"] = "quantidade_por_arte_explicita"
                associacao["requer_confirmacao_semantica"] = False
            elif associacao["quantidade_ocorrencias_desenhadas"] == 1 and associacao["quantidade"] > 1:
                associacao["interpretacao_quantidade"] = "repetir_arte_unica"
                associacao["requer_confirmacao_semantica"] = False
            elif associacao["quantidade"] == associacao["quantidade_ocorrencias_desenhadas"]:
                associacao["interpretacao_quantidade"] = "total_igual_as_ocorrencias_desenhadas_sem_area"
                associacao["requer_confirmacao_semantica"] = True
            else:
                associacao["interpretacao_quantidade"] = "repeticao_sem_area_comprovante"
                associacao["requer_confirmacao_semantica"] = True
            continue
        _, indice, area_m2, leitura_area = min(opcoes)
        areas_usadas.add(indice)
        area_individual_cm2 = associacao["largura_cm"] * associacao["altura_cm"]
        quantidade_area = area_m2 * 10_000 / max(1e-9, area_individual_cm2)
        quantidade_arredondada = round(quantidade_area)
        confere = abs(quantidade_area - quantidade_arredondada) <= 0.03 and quantidade_arredondada == associacao["quantidade"]
        associacao.update({
            "area_m2": area_m2, "texto_area": leitura_area.get("texto"),
            "quantidade_calculada_area": quantidade_arredondada,
            "area_confere_quantidade": confere,
            "requer_confirmacao_semantica": not confere,
        })
        if confere and associacao["quantidade_ocorrencias_desenhadas"] == associacao["quantidade"]:
            associacao["interpretacao_quantidade"] = "uma_unidade_por_ocorrencia_desenhada"
        elif confere and associacao["quantidade_ocorrencias_desenhadas"] == 1:
            associacao["interpretacao_quantidade"] = "repetir_arte_unica"
        elif confere:
            associacao["interpretacao_quantidade"] = "quantidade_total_confirmada_por_area"
        else:
            associacao["interpretacao_quantidade"] = "divergencia_entre_texto_area_e_desenho"
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
    intervalo_x = limites["direita"] - limites["esquerda"]
    intervalo_y = limites["topo"] - limites["base"]
    leituras_cm = []
    for leitura in leituras:
        xs = [ponto[0] for ponto in leitura["poligono_px"]]
        ys = [ponto[1] for ponto in leitura["poligono_px"]]
        leituras_cm.append({**leitura, "caixa_cm": {
            "esquerda": limites["esquerda"] + min(xs) / tamanho[0] * intervalo_x,
            "direita": limites["esquerda"] + max(xs) / tamanho[0] * intervalo_x,
            "topo": limites["topo"] - min(ys) / tamanho[1] * intervalo_y,
            "base": limites["topo"] - max(ys) / tamanho[1] * intervalo_y,
        }})
    hipoteses = catalogo["candidatos"] + catalogo.get("blocos_producao", [])
    return {
        "leituras_ocr": leituras_cm,
        "associacoes": associar_instrucoes_regionais(
            leituras_para_regras(leituras_cm, catalogo.get("evidencias_textuais") or [], limites, tamanho),
            hipoteses, limites, tamanho,
        ),
    }


def leituras_para_regras(leituras_cm: list[dict], evidencias_textuais: list[dict], limites: dict,
                         tamanho: tuple[int, int]) -> list[dict]:
    """Textos que as regras interpretam: nativos do CDR primeiro, OCR só para o resto.

    O texto nativo tem conteúdo e posição exatos. O OCR da mesma legenda pode
    sair quebrado conforme a escala do desenho ("1 UNI DE CADA" virou "1UNI" +
    "DE CADA"), e aí a regra "de cada" se perde. O OCR continua valendo para o
    que só existe na imagem, como texto convertido em curvas.
    """
    largura_cm = (limites["direita"] - limites["esquerda"]) or 1
    altura_cm = (limites["topo"] - limites["base"]) or 1

    def poligono(caixa: dict) -> list[list[float]]:
        x0 = (caixa["esquerda"] - limites["esquerda"]) / largura_cm * tamanho[0]
        x1 = (caixa["direita"] - limites["esquerda"]) / largura_cm * tamanho[0]
        y0 = (limites["topo"] - caixa["topo"]) / altura_cm * tamanho[1]
        y1 = (limites["topo"] - caixa["base"]) / altura_cm * tamanho[1]
        return [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]

    nativas = []
    for evidencia in evidencias_textuais:
        caixa_mm, texto = evidencia.get("caixa_mm"), (evidencia.get("texto") or "").strip()
        if not caixa_mm or not texto:
            continue
        caixa = {chave: caixa_mm[chave] / 10 for chave in ("esquerda", "direita", "base", "topo")}
        nativas.append({"texto": texto, "confianca": 1.0, "fonte": "texto_nativo",
                        "poligono_px": poligono(caixa), "caixa_cm": caixa})

    def dentro_de_nativo(leitura: dict) -> bool:
        a = leitura["caixa_cm"]
        area = max((a["direita"] - a["esquerda"]) * (a["topo"] - a["base"]), 1e-9)
        for nativa in nativas:
            b = nativa["caixa_cm"]
            largura = min(a["direita"], b["direita"]) - max(a["esquerda"], b["esquerda"])
            altura = min(a["topo"], b["topo"]) - max(a["base"], b["base"])
            if largura > 0 and altura > 0 and largura * altura / area >= 0.5:
                return True
        return False

    return nativas + [leitura for leitura in leituras_cm if not dentro_de_nativo(leitura)]


def _especificacao_material(texto: str) -> dict | None:
    normalizado = " ".join(texto.casefold().replace("+", " ").split())
    compacto = re.sub(r"\s+", "", normalizado)
    material = parse_material(texto)
    if material is None and re.search(r"\bads\b", normalizado):
        material = parse_material("adesivo " + texto)
    if "papelcouche" in compacto or "papelcouchê" in compacto:
        material = {"material": "papel couche", "acabamento": None}
    if material is None:
        return None
    valor_material = material["material"]
    if "branco" in normalizado and valor_material == "adesivo":
        valor_material = "adesivo branco"
    acabamento = material.get("acabamento")
    especiais = []
    if "frente e verso" in normalizado:
        especiais.append("frente e verso")
    if "ilh" in normalizado:
        especiais.append("ilhós")
    if "verniz" in normalizado:
        especiais.append("verniz")
    if especiais:
        acabamento = " + ".join(especiais)
    return {"material": valor_material, "acabamento": acabamento}


def _dimensoes_instrucao_material(texto: str, especificacao: dict) -> dict | None:
    dimensoes = parse_dimensoes(texto)
    if dimensoes is not None:
        return dimensoes
    match = re.search(r"(?i)(?<!\d)(\d+(?:[.,]\d+)?)\s*[x×]\s*(\d+(?:[.,]\d+)?)(?!\d)", texto)
    if match and especificacao.get("material"):
        return {
            "largura_mm": float(match.group(1).replace(",", ".")) * 10,
            "altura_mm": float(match.group(2).replace(",", ".")) * 10,
            "texto_origem": match.group(0),
        }
    return None


def _intersecao_caixas(a: dict, b: dict) -> float:
    largura = max(0.0, min(a["direita"], b["direita"]) - max(a["esquerda"], b["esquerda"]))
    altura = max(0.0, min(a["topo"], b["topo"]) - max(a["base"], b["base"]))
    return largura * altura


def _sobreposicao_da_menor_caixa(a: dict, b: dict) -> float:
    return _intersecao_caixas(a, b) / max(1e-9, min(_area_caixa(a), _area_caixa(b)))


def _medida_representa_caixa(candidato: dict) -> bool:
    caixa = candidato["caixa_cm"]
    largura_caixa = caixa["direita"] - caixa["esquerda"]
    altura_caixa = caixa["topo"] - caixa["base"]
    tolerancia = max(0.5, max(largura_caixa, altura_caixa) * 0.01)
    return min(
        abs(candidato["largura_cm"] - largura_caixa) + abs(candidato["altura_cm"] - altura_caixa),
        abs(candidato["largura_cm"] - altura_caixa) + abs(candidato["altura_cm"] - largura_caixa),
    ) <= tolerancia * 2


def _classificar_papeis_materiais(catalogo: dict, resultados: list[dict]) -> None:
    """Marca produto, conteúdo interno, montagem e ambiguidade sem apagar hipóteses."""
    candidatos = catalogo["candidatos"] + catalogo.get("blocos_producao", [])
    por_id = {item["id"]: item for item in candidatos}
    por_resultado = {item["candidato_id"]: item for item in resultados}
    ids_confirmados = {
        item["candidato_id"] for item in catalogo.get("ocr_regional", {}).get("associacoes", [])
    }
    ids_confirmados.update(item["id"] for item in catalogo.get("blocos_producao", []))

    for resultado in resultados:
        regras = {item.get("regra") for item in resultado.get("evidencias", [])}
        forte = resultado["candidato_id"] in ids_confirmados or bool(regras & {
            "material_com_dimensao", "material_com_quantidade", "nome_arquivo_com_dimensao",
            "instrucao_do_bloco",
        })
        resultado.update({
            "papel_candidato": "produto_confirmado" if forte else "produto_plausivel",
            "motivo_classificacao": "evidencia_explicita" if forte else "associacao_regional_sem_prova_estrutural",
            "exportavel_automaticamente": bool(forte and not resultado.get("conflitos")),
        })

    # Quando a caixa total é a mesma, a hipótese repetida de medida menor é
    # conteúdo da montagem; a hipótese cuja medida ocupa a caixa é o produto.
    ids = list(por_resultado)
    for indice, id_a in enumerate(ids):
        candidato_a = por_id.get(id_a)
        if candidato_a is None:
            continue
        for id_b in ids[indice + 1:]:
            candidato_b = por_id.get(id_b)
            if candidato_b is None or _sobreposicao_da_menor_caixa(candidato_a["caixa_cm"], candidato_b["caixa_cm"]) < 0.9:
                continue
            a_ocupa = _medida_representa_caixa(candidato_a)
            b_ocupa = _medida_representa_caixa(candidato_b)
            if a_ocupa == b_ocupa:
                continue
            detalhe_id, produto_id = (id_b, id_a) if a_ocupa else (id_a, id_b)
            detalhe = por_id[detalhe_id]
            if detalhe.get("quantidade_geometrica", 1) <= 1:
                continue
            por_resultado[detalhe_id].update({
                "papel_candidato": "conteudo_repetido_da_montagem",
                "motivo_classificacao": f"mesma_regiao_de_{produto_id}_com_medida_individual_repetida",
                "exportavel_automaticamente": False,
            })

    # Um contêiner com vários filhos propostos é uma montagem externa. Um
    # produto confirmado por medida/nome torna os filhos não confirmados detalhes.
    for id_externo, resultado_externo in por_resultado.items():
        externo = por_id.get(id_externo)
        if externo is None:
            continue
        filhos = [
            id_interno for id_interno in por_resultado
            if id_interno != id_externo
            and _area_caixa(por_id[id_interno]["caixa_cm"]) < _area_caixa(externo["caixa_cm"]) * 0.95
            and _contem_caixa(externo["caixa_cm"], por_id[id_interno]["caixa_cm"], 0.1)
        ]
        if len(filhos) >= 2 and resultado_externo["papel_candidato"] != "produto_confirmado":
            resultado_externo.update({
                "papel_candidato": "montagem_externa",
                "motivo_classificacao": "contem_multiplos_produtos_propostos",
                "exportavel_automaticamente": False,
            })
            for filho_id in filhos:
                filho = por_resultado[filho_id]
                if filho["papel_candidato"] == "conteudo_repetido_da_montagem":
                    filho.update({
                        "papel_candidato": "produto_plausivel",
                        "motivo_classificacao": f"filho_produtivo_da_montagem_{id_externo}",
                        "exportavel_automaticamente": False,
                    })
        elif resultado_externo["papel_candidato"] == "produto_confirmado":
            for filho_id in filhos:
                filho = por_resultado[filho_id]
                if filho["papel_candidato"] != "produto_confirmado":
                    filho.update({
                        "papel_candidato": "detalhe_interno_do_produto",
                        "motivo_classificacao": f"contido_no_produto_confirmado_{id_externo}",
                        "exportavel_automaticamente": False,
                    })

    # Duas molduras sobrepostas contendo a mesma hipótese interna não permitem
    # escolher deterministicamente qual nível representa o produto.
    for id_interno in ids:
        interno = por_id.get(id_interno)
        if interno is None:
            continue
        contenedores = [
            id_externo for id_externo in ids if id_externo != id_interno
            and _area_caixa(por_id[id_externo]["caixa_cm"]) > _area_caixa(interno["caixa_cm"]) * 1.05
            and _contem_caixa(por_id[id_externo]["caixa_cm"], interno["caixa_cm"], 0.1)
        ]
        if len(contenedores) < 2:
            continue
        for id_externo in contenedores:
            externo = por_resultado[id_externo]
            if externo["papel_candidato"] == "produto_plausivel":
                externo.update({
                    "papel_candidato": "estrutura_ambigua",
                    "motivo_classificacao": f"molduras_sobrepostas_contendo_{id_interno}",
                    "exportavel_automaticamente": False,
                })


def _texto_canonico(valor) -> str:
    texto = "".join(
        caractere for caractere in unicodedata.normalize("NFKD", str(valor or "").casefold())
        if not unicodedata.combining(caractere)
    )
    return " ".join(texto.split())


def comparar_materiais_com_revisao(catalogo: dict, esperado: dict, cobertura: dict) -> list[dict]:
    """Expõe divergências entre a evidência do arquivo e a confirmação humana."""
    previstos = {item["candidato_id"]: item for item in catalogo.get("materiais_regionais", [])}
    conflitos = []
    for indice, (detalhe, item_esperado) in enumerate(
        zip(cobertura.get("detalhes", []), esperado.get("itens", [])), 1
    ):
        candidato_id = detalhe.get("candidato")
        previsto = previstos.get(candidato_id)
        if not previsto:
            continue
        campos = {
            "material": (item_esperado.get("material") or {}).get("valor"),
            "acabamento": (item_esperado.get("acabamento") or {}).get("valor"),
        }
        for campo, confirmado in campos.items():
            valor_previsto = previsto.get(campo)
            if not valor_previsto or not confirmado:
                continue
            previsto_canonico = _texto_canonico(valor_previsto)
            confirmado_canonico = _texto_canonico(confirmado)
            compativel = previsto_canonico == confirmado_canonico
            if campo == "material":
                if {previsto_canonico, confirmado_canonico} <= {"banner", "lona"}:
                    compativel = True
                if confirmado_canonico == "adesivo" and previsto_canonico.startswith("adesivo "):
                    compativel = True
            if campo == "acabamento":
                termos = ("frente e verso", "ilho", "verniz")
                previstos_compostos = {termo for termo in termos if termo in previsto_canonico}
                confirmados_compostos = {termo for termo in termos if termo in confirmado_canonico}
                if previstos_compostos and previstos_compostos == confirmados_compostos:
                    compativel = True
            if not compativel:
                conflitos.append({
                    "codigo": "DIVERGENCIA_ENTRE_ARQUIVO_E_REVISAO",
                    "candidato_id": candidato_id, "item_revisado": indice,
                    "campo": campo, "valor_do_arquivo": valor_previsto,
                    "valor_confirmado": confirmado,
                    "evidencias": previsto.get("evidencias", []),
                    "requer_revisao": True,
                })
    return conflitos


def associar_materiais_acabamentos(catalogo: dict) -> list[dict]:
    """Associa especificações explícitas sem espalhá-las por documentos mistos."""
    candidatos = catalogo["candidatos"] + catalogo.get("blocos_producao", [])
    por_id = {item["id"]: item for item in candidatos}
    visiveis = [item for item in candidatos if item.get("visivel_inicialmente", True)]
    confirmados = {
        item["candidato_id"]
        for item in catalogo.get("ocr_regional", {}).get("associacoes", [])
    }
    confirmados.update(item["id"] for item in catalogo.get("blocos_producao", []))

    fontes = []
    for evidencia in catalogo.get("evidencias_textuais", []):
        especificacao = _especificacao_material(evidencia.get("texto", ""))
        if especificacao and evidencia.get("caixa_mm"):
            fontes.append({
                **especificacao, "texto": evidencia["texto"], "fonte": "texto_cdr",
                "caixa_cm": _caixa_texto_cm(evidencia),
                "quantidade": evidencia.get("quantidade"),
                "dimensoes": evidencia.get("dimensoes") or _dimensoes_instrucao_material(evidencia["texto"], especificacao),
            })
    for leitura in catalogo.get("ocr_regional", {}).get("leituras_ocr", []):
        especificacao = _especificacao_material(leitura.get("texto", ""))
        if especificacao and leitura.get("caixa_cm"):
            duplicada = any(
                fonte["material"] == especificacao["material"]
                and _sobreposicao_horizontal(fonte["caixa_cm"], leitura["caixa_cm"]) > 0.7
                for fonte in fontes
            )
            if not duplicada:
                fontes.append({
                    **especificacao, "texto": leitura["texto"], "fonte": "ocr",
                    "caixa_cm": leitura["caixa_cm"],
                    "quantidade": (parse_quantidade(leitura["texto"]) or (None,))[0],
                    "dimensoes": _dimensoes_instrucao_material(leitura["texto"], especificacao),
                })

    propostas: dict[str, list[dict]] = {}

    def propor(candidato_id: str, fonte: dict, regra: str, confianca: float) -> None:
        propostas.setdefault(candidato_id, []).append({
            "material": fonte.get("material"), "acabamento": fonte.get("acabamento"),
            "texto": fonte.get("texto"), "fonte": fonte.get("fonte"),
            "regra": regra, "confianca": confianca,
        })

    for bloco in catalogo.get("blocos_producao", []):
        propor(bloco["id"], {
            "material": bloco.get("material_sugerido"),
            "acabamento": bloco.get("acabamento_sugerido"),
            "texto": " / ".join(bloco.get("instrucoes", [])), "fonte": "bloco_producao",
        }, "instrucao_do_bloco", 0.99)

    for fonte in fontes:
        dimensoes = fonte.get("dimensoes") or {}
        largura = float(dimensoes.get("largura_mm") or 0) / 10
        altura = float(dimensoes.get("altura_mm") or 0) / 10
        compativeis_dimensao = []
        if largura and altura:
            for candidato in visiveis:
                erro = min(
                    abs(candidato["largura_cm"] - largura) + abs(candidato["altura_cm"] - altura),
                    abs(candidato["largura_cm"] - altura) + abs(candidato["altura_cm"] - largura),
                )
                if erro <= 0.5:
                    compativeis_dimensao.append(candidato)
        if compativeis_dimensao:
            for candidato in compativeis_dimensao:
                propor(candidato["id"], fonte, "material_com_dimensao", 0.99)
            continue
        quantidade = fonte.get("quantidade")
        if quantidade:
            compativeis_quantidade = [
                item for item in visiveis if item.get("quantidade_geometrica") == quantidade
            ]
            if len(compativeis_quantidade) == 1:
                propor(compativeis_quantidade[0]["id"], fonte, "material_com_quantidade", 0.96)
                continue
        caixa_texto = fonte["caixa_cm"]
        abaixo = []
        margem = max(2.0, (caixa_texto["direita"] - caixa_texto["esquerda"]) * 0.15)
        for candidato in visiveis:
            caixa = candidato["caixa_cm"]
            centro_x = (caixa["esquerda"] + caixa["direita"]) / 2
            if not (caixa_texto["esquerda"] - margem <= centro_x <= caixa_texto["direita"] + margem):
                continue
            if caixa["topo"] >= caixa_texto["base"]:
                continue
            abaixo.append((caixa_texto["base"] - caixa["topo"], candidato))
        if abaixo:
            menor_distancia = min(item[0] for item in abaixo)
            faixa_vertical = max(5.0, menor_distancia * 0.25)
            alvos = [item for distancia, item in abaixo if distancia - menor_distancia <= faixa_vertical]
            if len(alvos) <= 3:
                for candidato in alvos:
                    propor(candidato["id"], fonte, "cabecalho_regional", 0.92)
                continue
        acima = []
        for candidato in visiveis:
            caixa = candidato["caixa_cm"]
            centro_x = (caixa["esquerda"] + caixa["direita"]) / 2
            if not (caixa_texto["esquerda"] - margem <= centro_x <= caixa_texto["direita"] + margem):
                continue
            if caixa["base"] <= caixa_texto["topo"]:
                continue
            sobreposicao = _sobreposicao_horizontal(caixa_texto, caixa)
            centro_texto_x = (caixa_texto["esquerda"] + caixa_texto["direita"]) / 2
            texto_sobre_candidato = caixa["esquerda"] <= centro_texto_x <= caixa["direita"]
            if sobreposicao >= 0.25 or texto_sobre_candidato:
                acima.append((caixa["base"] - caixa_texto["topo"], -candidato.get("quantidade_geometrica", 1), candidato))
        if acima:
            menor_distancia = min(item[0] for item in acima)
            proximos = [item for distancia, _, item in acima if distancia - menor_distancia <= max(3.0, menor_distancia * 0.2)]
            melhor = max(proximos, key=lambda item: item.get("quantidade_geometrica", 1))
            propor(melhor["id"], fonte, "legenda_regional_abaixo", 0.94)

    nome = interpretar_nome_arquivo(catalogo["arquivo"])
    especificacao_nome = _especificacao_material(nome["texto"])
    if especificacao_nome:
        fonte_nome = {**especificacao_nome, "texto": nome["texto"], "fonte": "nome_arquivo"}
        alvos_nome = [por_id[item] for item in confirmados if item in por_id]
        regra_nome = "nome_arquivo_em_alvo_confirmado"
        dimensoes_nome = nome.get("dimensoes") or {}
        if not alvos_nome and dimensoes_nome:
            largura = float(dimensoes_nome.get("largura_mm") or 0) / 10
            altura = float(dimensoes_nome.get("altura_mm") or 0) / 10
            alvos_nome = [
                item for item in visiveis
                if min(
                    abs(item["largura_cm"] - largura) + abs(item["altura_cm"] - altura),
                    abs(item["largura_cm"] - altura) + abs(item["altura_cm"] - largura),
                ) <= 0.5
            ]
            regra_nome = "nome_arquivo_com_dimensao"
        if not alvos_nome and len(visiveis) == 1:
            alvos_nome = visiveis
        for candidato in alvos_nome:
            propor(candidato["id"], fonte_nome, regra_nome, 0.75)

    resultado = []
    for candidato_id, opcoes in propostas.items():
        materiais = {item["material"] for item in opcoes if item.get("material")}
        familias = {
            "adesivo" if material.startswith("adesivo") else "lona" if material in {"banner", "lona"} else material
            for material in materiais
        }
        locais = [item for item in opcoes if item["fonte"] != "nome_arquivo"]
        escolhida = max(
            opcoes,
            key=lambda item: (len(item.get("material") or ""), item["fonte"] != "nome_arquivo", item["confianca"]),
        )
        conflitos = []
        material_escolhido = escolhida["material"] if len(familias) == 1 else None
        if len(familias) > 1:
            conflitos.append({
                "campo": "material", "valores": sorted(materiais),
                "fontes": sorted({item["fonte"] for item in opcoes}),
            })
        acabamentos = {
            item["acabamento"] for item in (locais or opcoes) if item.get("acabamento")
        }
        acabamento = next(iter(acabamentos)) if len(acabamentos) == 1 else None
        if len(acabamentos) > 1:
            conflitos.append({
                "campo": "acabamento", "valores": sorted(acabamentos),
                "fontes": sorted({item["fonte"] for item in (locais or opcoes) if item.get("acabamento")}),
            })
        resultado.append({
            "candidato_id": candidato_id, "material": material_escolhido,
            "acabamento": acabamento, "fonte": escolhida["fonte"],
            "texto": escolhida["texto"], "regra": escolhida["regra"],
            "confianca": escolhida["confianca"], "conflitos": conflitos,
            "status_associacao": "revisao_conflito" if conflitos else "associado",
            "evidencias": sorted(opcoes, key=lambda item: item["confianca"], reverse=True),
        })
    _classificar_papeis_materiais(catalogo, resultado)
    return sorted(resultado, key=lambda item: item["candidato_id"])


def extrair_candidatos_agente(caminho: Path) -> dict:
    """Cria um catálogo de caixas medíveis sem decidir quais são produtos."""
    with abrir_cdr(caminho) as doc:
        estrutura = list(_estrutura_visivel(doc))
        caixa_limites = doc.limites_conteudo(estrutura) if hasattr(doc, "limites_conteudo") else None
        recipientes_powerclip = [
            {
                "esquerda": objeto.caixa.esquerda / 100_000, "direita": objeto.caixa.direita / 100_000,
                "base": objeto.caixa.base / 100_000, "topo": objeto.caixa.topo / 100_000,
            }
            for objeto in estrutura if objeto.grupo_powerclip is not None and objeto.caixa is not None
        ]
        profundos = _inventario_geometrico(doc)
        rasos = _candidatos_arte(doc)
        evidencias = _evidencias_textuais(doc)

    candidatos = []
    for item_bruto in profundos:
        for item in _separar_regioes_contiguas(item_bruto):
            candidatos.append({
                "origem": item["origem"],
                "quantidade_geometrica": int(item.get("quantidade_sugerida") or 1),
                "largura_cm": float(item["largura_cm"]),
                "altura_cm": float(item["altura_cm"]),
                "posicoes_centro_cm": item.get("posicoes_centro_cm") or [],
                "tipos": item.get("tipos") or [],
                "caixa_cm": _caixa_de_centros(item),
                "regiao_medida": item.get("regiao_medida"),
                "total_regioes_mesma_medida": item.get("total_regioes_mesma_medida", 1),
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
    _anotar_hierarquia(candidatos, recipientes_powerclip)
    blocos_producao = detectar_blocos_producao(candidatos, evidencias)

    limites = None
    if caixa_limites is not None:
        limites = {
            "esquerda": caixa_limites.esquerda / 100_000, "direita": caixa_limites.direita / 100_000,
            "base": caixa_limites.base / 100_000, "topo": caixa_limites.topo / 100_000,
        }
    return {
        "arquivo": Path(caminho).name,
        "limites_conteudo_cm": limites,
        "candidatos": candidatos,
        "blocos_producao": blocos_producao,
        "evidencias_textuais": evidencias,
    }


def resumir_catalogo_regional(catalogo: dict) -> dict:
    """Converte o catálogo pesado em uma auditoria adequada à interface e ao log."""
    candidatos = catalogo["candidatos"] + catalogo.get("blocos_producao", [])
    visiveis = [item for item in candidatos if item.get("visivel_inicialmente", True)]
    materiais = {
        item["candidato_id"]: item for item in catalogo.get("materiais_regionais", [])
    }
    quantidades: dict[str, list[dict]] = {}
    for associacao in catalogo.get("ocr_regional", {}).get("associacoes", []):
        quantidades.setdefault(associacao["candidato_id"], []).append(associacao)
    itens = []
    conflitos = []
    for candidato in visiveis:
        candidato_id = candidato["id"]
        material = materiais.get(candidato_id) or {}
        associacoes = quantidades.get(candidato_id, [])
        # "N de cada": o candidato pode reunir K artes diferentes do mesmo tamanho,
        # então o total é N x K (a mesma regra que o validador do agente cobra).
        valores_quantidade = {
            int(item["quantidade"]) * (
                int(item.get("quantidade_ocorrencias_desenhadas") or 1) if item.get("regra") == "quantidade_de_cada" else 1
            )
            for item in associacoes
        }
        quantidade_pedido = next(iter(valores_quantidade)) if len(valores_quantidade) == 1 else None
        papel = material.get("papel_candidato", "sem_classificacao")
        conflitos_item = material.get("conflitos", [])
        requer_confirmacao_quantidade = any(
            item.get("requer_confirmacao_semantica") is True for item in associacoes
        )
        if conflitos_item or papel in {"estrutura_ambigua", "sem_classificacao"} or requer_confirmacao_quantidade:
            estado = "revisao_necessaria"
        elif papel == "produto_confirmado":
            estado = "confirmado_por_evidencia"
        elif papel == "produto_plausivel":
            estado = "produto_plausivel"
        else:
            estado = "estrutura_auxiliar"
        evidencias = [{
            "fonte": item.get("fonte"), "regra": item.get("regra"),
            "texto": item.get("texto"), "confianca": item.get("confianca"),
        } for item in material.get("evidencias", [])]
        itens.append({
            "candidato_id": candidato_id,
            "papel": papel, "estado": estado,
            "quantidade_pedido": quantidade_pedido,
            "quantidade_desenhada": candidato.get("quantidade_geometrica", 1),
            "largura_cm": round(float(candidato["largura_cm"]), 3),
            "altura_cm": round(float(candidato["altura_cm"]), 3),
            "material": material.get("material"),
            "acabamento": material.get("acabamento"),
            "exportavel_automaticamente": material.get("exportavel_automaticamente", False),
            "motivo": material.get("motivo_classificacao", "sem_associacao_regional"),
            "evidencias": evidencias,
        })
        for conflito in conflitos_item:
            conflitos.append({
                **conflito, "candidato_id": candidato_id,
                "evidencias": evidencias, "requer_revisao": True,
            })
    produtivos = [item for item in itens if item["papel"] in {"produto_confirmado", "produto_plausivel"}]
    auxiliares = [item for item in itens if item["estado"] == "estrutura_auxiliar"]
    ambiguos = [item for item in itens if item["estado"] == "revisao_necessaria"]
    return {
        "schema_version": "1.0-experimental",
        "arquivo": catalogo.get("arquivo"),
        "itens": itens,
        "resumo": {
            "candidatos_visiveis": len(itens),
            "produtos_propostos": len(produtivos),
            "produtos_confirmados": sum(item["papel"] == "produto_confirmado" for item in itens),
            "estruturas_auxiliares": len(auxiliares),
            "revisoes_necessarias": len(ambiguos),
            "conflitos_entre_fontes": len(conflitos),
        },
        "conflitos_fontes": conflitos,
    }


def executar_arquitetura_regional(caminho: Path) -> dict:
    """Executa a camada experimental completa sem alterar o resultado estável."""
    catalogo = extrair_candidatos_agente(caminho)
    catalogo["ocr_regional"] = extrair_associacoes_regionais(caminho, catalogo)
    catalogo["materiais_regionais"] = associar_materiais_acabamentos(catalogo)
    return resumir_catalogo_regional(catalogo)


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
                if capacidade == quantidade:
                    penalidade_quantidade = 0
                elif capacidade == 1:
                    penalidade_quantidade = 1
                else:
                    penalidade_quantidade = 2 + abs(capacidade - quantidade) / max(1, quantidade)
                penalidade_visibilidade = 0 if candidato.get("visivel_inicialmente", True) else 1
                opcoes.append((erro, penalidade_quantidade, penalidade_visibilidade, indice, candidato["id"]))
        if opcoes:
            erro, _, _, indice, candidato_id = min(opcoes)
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
