"""Agente de interpretação de pedidos (protótipo da v0.9, fora do fluxo do app).

O código produz fatos que a IA não pode alterar: peças candidatas com ID e
medida exata do CDR, textos (nativos e OCR) com ID e posição, e as pistas das
regras regionais. O modelo investiga com ferramentas e responde escolhendo
IDs, citando o texto que prova cada quantidade e material. Um validador
confere a resposta e devolve os erros para correção.
"""
from __future__ import annotations

import base64
from io import BytesIO
import json
from pathlib import Path
import re
from time import perf_counter
import unicodedata

from .experimento_agente import (
    associar_materiais_acabamentos,
    extrair_associacoes_regionais,
    extrair_candidatos_agente,
    resumir_catalogo_regional,
)
from .visao_api import URL_OPENROUTER, extrair_imagem_analise, extrair_json_resposta

ARQUIVO_REGRAS_DA_CASA = Path(__file__).with_name("regras_da_casa.md")
MAX_RODADAS = 8
MAX_CORRECOES = 2
# Imagens menores reduzem o custo por pedido; os rótulos continuam legíveis.
LADO_MAXIMO_IMAGEM = 1500
QUALIDADE_JPEG = 80


class OrcamentoExcedido(RuntimeError):
    pass


# ---------------------------------------------------------------- fatos

def _caixa_texto_nativo(evidencia: dict) -> dict:
    caixa = evidencia["caixa_mm"]
    return {k: caixa[k] / 10 for k in ("esquerda", "direita", "base", "topo")}


def _sobreposicao(a: dict, b: dict) -> float:
    largura = min(a["direita"], b["direita"]) - max(a["esquerda"], b["esquerda"])
    altura = min(a["topo"], b["topo"]) - max(a["base"], b["base"])
    if largura <= 0 or altura <= 0:
        return 0.0
    menor = min(
        (a["direita"] - a["esquerda"]) * (a["topo"] - a["base"]),
        (b["direita"] - b["esquerda"]) * (b["topo"] - b["base"]),
    )
    return largura * altura / menor if menor > 0 else 0.0


def extrair_fatos(caminho: Path) -> dict:
    """Catálogo de candidatas, textos numerados, imagem e pistas das regras."""
    caminho = Path(caminho)
    catalogo = extrair_candidatos_agente(caminho)
    catalogo["ocr_regional"] = extrair_associacoes_regionais(caminho, catalogo)
    materiais = associar_materiais_acabamentos(catalogo)
    catalogo["materiais_regionais"] = materiais
    auditoria_regional = resumir_catalogo_regional(catalogo)
    imagem = extrair_imagem_analise(caminho)

    textos = []
    for evidencia in catalogo["evidencias_textuais"]:
        textos.append({"texto": evidencia["texto"], "fonte": "texto_nativo", "caixa_cm": _caixa_texto_nativo(evidencia)})
    for leitura in catalogo["ocr_regional"].get("leituras_ocr", []):
        # O OCR repete textos nativos; só acrescenta o que é novo (ex.: texto em curvas).
        repetido = any(
            _sobreposicao(leitura["caixa_cm"], t["caixa_cm"]) > 0.5
            and _normalizar(leitura["texto"])[:6] in _normalizar(t["texto"])
            for t in textos if t["fonte"] == "texto_nativo"
        )
        if not repetido:
            textos.append({
                "texto": leitura["texto"], "fonte": "ocr",
                "confianca": round(float(leitura.get("confianca") or 0), 2), "caixa_cm": leitura["caixa_cm"],
            })
    textos.sort(key=lambda t: (-t["caixa_cm"]["topo"], t["caixa_cm"]["esquerda"]))
    for indice, texto in enumerate(textos, 1):
        texto["id"] = f"T{indice:02d}"

    candidatos = {c["id"]: c for c in catalogo["candidatos"] + catalogo.get("blocos_producao", [])}
    pistas = []
    for associacao in catalogo["ocr_regional"].get("associacoes", []):
        pistas.append(
            f"{associacao['candidato_id']}: quantidade {associacao['quantidade']} "
            f"pela regra '{associacao.get('regra')}' a partir de \"{associacao.get('texto')}\""
        )
    for material in materiais:
        if material.get("material") or material.get("acabamento"):
            pistas.append(
                f"{material['candidato_id']}: material {material.get('material')!r}, acabamento "
                f"{material.get('acabamento')!r} (papel sugerido: {material.get('papel_candidato')})"
            )
    return {
        "arquivo": caminho.name,
        "limites_cm": catalogo["limites_conteudo_cm"],
        "candidatos": candidatos,
        "textos": {t["id"]: t for t in textos},
        "pistas_regras": pistas,
        "auditoria_regional": auditoria_regional,
        "imagem": imagem[0] if imagem else None,
        "imagem_origem": imagem[2] if imagem else None,
    }


# ---------------------------------------------------------------- imagens

def _px(fatos: dict, tamanho: tuple[int, int], caixa: dict) -> tuple[float, float, float, float]:
    lim = fatos["limites_cm"]
    largura_cm = (lim["direita"] - lim["esquerda"]) or 1
    altura_cm = (lim["topo"] - lim["base"]) or 1
    return (
        (caixa["esquerda"] - lim["esquerda"]) / largura_cm * tamanho[0],
        (lim["topo"] - caixa["topo"]) / altura_cm * tamanho[1],
        (caixa["direita"] - lim["esquerda"]) / largura_cm * tamanho[0],
        (lim["topo"] - caixa["base"]) / altura_cm * tamanho[1],
    )


def _data_url(imagem, formato: str = "PNG") -> str:
    buffer = BytesIO()
    imagem.save(buffer, format=formato, **({"quality": QUALIDADE_JPEG} if formato == "JPEG" else {}))
    return f"data:image/{formato.lower()};base64,{base64.b64encode(buffer.getvalue()).decode('ascii')}"


def _reduzir(imagem, lado_max: int = LADO_MAXIMO_IMAGEM):
    if max(imagem.size) > lado_max:
        escala = lado_max / max(imagem.size)
        imagem = imagem.resize((round(imagem.size[0] * escala), round(imagem.size[1] * escala)))
    return imagem


def _anotar(imagem, fatos: dict, ids: list[str], textos: bool = False):
    """Desenha caixa e ID de cada candidata (set-of-marks) sobre uma cópia."""
    from PIL import ImageDraw, ImageFont

    copia = imagem.convert("RGB").copy()
    desenho = ImageDraw.Draw(copia)
    espessura = max(2, round(max(copia.size) / 600))
    # Rótulos legíveis depois da redução para ~1800 px enviada ao modelo.
    tamanho_fonte = max(14, round(max(copia.size) / 70))
    fonte = ImageFont.load_default(size=tamanho_fonte)
    fonte_texto = ImageFont.load_default(size=max(12, round(tamanho_fonte * 0.8)))
    for indice, candidato_id in enumerate(ids):
        cor = ("#e11d48", "#2563eb", "#059669", "#d97706", "#7c3aed", "#0891b2")[indice % 6]
        x0, y0, x1, y1 = _px(fatos, copia.size, fatos["candidatos"][candidato_id]["caixa_cm"])
        desenho.rectangle((x0, y0, x1, y1), outline=cor, width=espessura)
        caixa_rotulo = desenho.textbbox((x0 + 4, y0 + 2), candidato_id, font=fonte)
        desenho.rectangle((x0, y0, caixa_rotulo[2] + 4, caixa_rotulo[3] + 4), fill=cor)
        desenho.text((x0 + 4, y0 + 2), candidato_id, fill="white", font=fonte)
    if textos:
        for texto in fatos["textos"].values():
            x0, y0, x1, y1 = _px(fatos, copia.size, texto["caixa_cm"])
            desenho.rectangle((x0, y0, x1, y1), outline="#64748b", width=1)
            caixa_rotulo = desenho.textbbox((x1 + 3, y0), texto["id"], font=fonte_texto)
            desenho.rectangle(caixa_rotulo, fill="#f1f5f9")
            desenho.text((x1 + 3, y0), texto["id"], fill="#334155", font=fonte_texto)
    return copia


def imagens_iniciais(fatos: dict) -> list[str]:
    from PIL import Image

    if not fatos["imagem"]:
        return []
    with Image.open(BytesIO(fatos["imagem"])) as original:
        original.load()
        visiveis = [i for i, c in fatos["candidatos"].items() if c.get("visivel_inicialmente", True)]
        limpa = _reduzir(original.convert("RGB"))
        anotada = _reduzir(_anotar(original, fatos, visiveis, textos=True))
    return [_data_url(limpa, "JPEG"), _data_url(anotada, "JPEG")]


def imagem_da_regiao(fatos: dict, caixa_cm: dict, lado_maximo_px: int = 560, margem: float = 0.08) -> bytes | None:
    """PNG da região do pedido, para a revisão conferir o que foi interpretado."""
    from PIL import Image

    if not fatos.get("imagem") or not caixa_cm:
        return None
    largura = max(caixa_cm["direita"] - caixa_cm["esquerda"], 0.1)
    altura = max(caixa_cm["topo"] - caixa_cm["base"], 0.1)
    folga = margem * max(largura, altura)
    area = {
        "esquerda": caixa_cm["esquerda"] - folga, "direita": caixa_cm["direita"] + folga,
        "base": caixa_cm["base"] - folga, "topo": caixa_cm["topo"] + folga,
    }
    with Image.open(BytesIO(fatos["imagem"])) as original:
        original.load()
        x0, y0, x1, y1 = _px(fatos, original.size, area)
        corte = original.convert("RGB").crop((
            max(0, round(x0)), max(0, round(y0)),
            min(original.size[0], round(x1)), min(original.size[1], round(y1)),
        ))
    if not corte.size[0] or not corte.size[1]:
        return None
    buffer = BytesIO()
    _reduzir(corte, lado_maximo_px).save(buffer, format="PNG")
    return buffer.getvalue()


def recorte(fatos: dict, ids: list[str], mostrar_filhos: bool) -> str | None:
    from PIL import Image

    if not fatos["imagem"]:
        return None
    caixas = [fatos["candidatos"][i]["caixa_cm"] for i in ids]
    uniao = {
        "esquerda": min(c["esquerda"] for c in caixas), "direita": max(c["direita"] for c in caixas),
        "base": min(c["base"] for c in caixas), "topo": max(c["topo"] for c in caixas),
    }
    margem = 0.15 * max(uniao["direita"] - uniao["esquerda"], uniao["topo"] - uniao["base"], 1)
    area = {"esquerda": uniao["esquerda"] - margem, "direita": uniao["direita"] + margem,
            "base": uniao["base"] - margem, "topo": uniao["topo"] + margem}
    marcados = list(ids)
    if mostrar_filhos:
        for candidato_id in ids:
            marcados += fatos["candidatos"][candidato_id].get("filhos_ids") or []
    with Image.open(BytesIO(fatos["imagem"])) as original:
        original.load()
        anotada = _anotar(original, fatos, [i for i in dict.fromkeys(marcados) if i in fatos["candidatos"]])
        x0, y0, x1, y1 = _px(fatos, anotada.size, area)
        corte = anotada.crop((max(0, round(x0)), max(0, round(y0)), min(anotada.size[0], round(x1)), min(anotada.size[1], round(y1))))
    return _data_url(_reduzir(corte, 1200), "JPEG")


# ---------------------------------------------------------------- ficha textual

def _medida(c: dict) -> str:
    return f"{c['largura_cm']:.2f} x {c['altura_cm']:.2f} cm"


def ficha_fatos(fatos: dict) -> str:
    linhas = [
        f"ARQUIVO: {fatos['arquivo']}", "",
        "PEÇAS CANDIDATAS DE PRIMEIRO NÍVEL (medidas exatas do CDR;",
        "'ocorrências desenhadas' pode reunir artes diferentes do mesmo tamanho):",
    ]
    for candidato_id, c in fatos["candidatos"].items():
        if not c.get("visivel_inicialmente", True):
            continue
        filhos = c.get("filhos_ids") or []
        linhas.append(
            f"- {candidato_id}: {_medida(c)}; ocorrências desenhadas: {c.get('quantidade_geometrica', 1)}; "
            f"origem: {c.get('origem')}; tipos: {','.join(c.get('tipos') or [])}"
            + (f"; contém {len(filhos)} candidata(s) interna(s)" if filhos else "")
        )
    linhas += ["", "TEXTOS DA PÁGINA (de cima para baixo; posição em cm):"]
    for texto_id, t in fatos["textos"].items():
        caixa = t["caixa_cm"]
        linhas.append(
            f"- {texto_id} [{t['fonte']}] \"{t['texto']}\" em x={caixa['esquerda']:.1f}..{caixa['direita']:.1f}, "
            f"y={caixa['base']:.1f}..{caixa['topo']:.1f}"
        )
    if fatos["pistas_regras"]:
        linhas += ["", "PISTAS DAS REGRAS AUTOMÁTICAS (podem estar erradas ou incompletas):"]
        linhas += [f"- {p}" for p in fatos["pistas_regras"]]
    return "\n".join(linhas)


def caminho_regras_da_casa() -> Path:
    """Cópia editável ao lado da configuração; o arquivo do pacote é só o modelo inicial."""
    from .configuracao import caminho_configuracao

    editavel = caminho_configuracao().with_name("regras_da_casa.md")
    if not editavel.exists():
        try:
            editavel.parent.mkdir(parents=True, exist_ok=True)
            editavel.write_text(ARQUIVO_REGRAS_DA_CASA.read_text(encoding="utf-8"), encoding="utf-8")
        except OSError:
            return ARQUIVO_REGRAS_DA_CASA
    return editavel


def regras_da_casa() -> str:
    try:
        texto = caminho_regras_da_casa().read_text(encoding="utf-8")
    except OSError:
        return ""
    return re.sub(r"<!--.*?-->", "", texto, flags=re.S).strip()


PROMPT_SISTEMA = """Você é o operador experiente de uma gráfica de comunicação visual e interpreta a montagem de um pedido recebido em CorelDRAW.

Objetivo: listar as LINHAS DE PRODUÇÃO do pedido — cada produto distinto com quantidade a produzir, medida, material e acabamento.

Você recebe:
1. Imagem limpa da montagem.
2. A mesma imagem com as peças candidatas de primeiro nível marcadas por ID (A01, A02…) e os textos por ID (T01, T02…).
3. Uma ficha com as medidas EXATAS de cada candidata e todos os textos. As medidas vêm do arquivo: nunca estime nem invente medidas.

Como decidir:
- Um produto é uma peça que será impressa/cortada. Molduras de montagem, colchetes, setas, cotas, legendas e cabeçalhos NÃO são produtos.
- Uma candidata pode ser uma montagem com vários produtos dentro, ou um detalhe interno (logo, texto da arte) de um produto. Use ver_detalhe com mostrar_filhos=true para investigar e escolher o nível certo.
- "ocorrências desenhadas" é quantas vezes a MESMA MEDIDA aparece na mesma região. Podem ser artes diferentes do mesmo tamanho (use ver_detalhe para ver quais são). Isso NÃO é necessariamente a quantidade do pedido.
- Quantidade: use o texto de instrução ("4 UN", "30 UNI DE CADA", "60 und"). "N DE CADA" vale N para CADA peça desenhada: uma candidata com K ocorrências e a instrução "N de cada" soma N x K unidades. Nesse caso, ou informe um item com quantidade N x K, ou separe em K itens de N unidades usando os IDs internos. Sem instrução, a quantidade é o número de ocorrências desenhadas.
- Legendas de área (ex.: "0,5022 M²") ajudam a conferir: área ÷ (largura × altura) = unidades.
- Material e acabamento vêm de textos próximos ou de cabeçalhos que abrangem a peça; o nome do arquivo também é evidência.
- Quando não houver como decidir com segurança, NÃO chute: registre uma pergunta objetiva para o operador.

Resposta: chame a ferramenta `finalizar`. Cada item cita os IDs das peças e o ID do texto que prova a quantidade e o material. Itens sem prova serão rejeitados pelo validador."""


# ---------------------------------------------------------------- ferramentas

def _ferramentas() -> list[dict]:
    ids = {"type": "array", "items": {"type": "string"}, "minItems": 1}
    item = {
        "type": "object",
        "properties": {
            "ids": {**ids, "description": "IDs das candidatas deste produto"},
            "combinar": {"type": "string", "enum": ["nao", "uniao"], "description": "'nao': cada ID é uma peça com a mesma medida; 'uniao': os IDs juntos formam UMA peça, medida = caixa que envolve todos"},
            "quantidade": {"type": "integer", "minimum": 1},
            "origem_quantidade": {"type": "string", "enum": ["texto", "ocorrencias_desenhadas"]},
            "texto_quantidade": {"type": ["string", "null"], "description": "ID do texto (T..) que prova a quantidade"},
            "material": {"type": ["string", "null"]},
            "texto_material": {"type": ["string", "null"], "description": "ID do texto que prova o material, ou 'NOME_ARQUIVO'"},
            "acabamento": {"type": ["string", "null"]},
            "texto_acabamento": {"type": ["string", "null"]},
            "justificativa": {"type": "string"},
        },
        "required": ["ids", "combinar", "quantidade", "origem_quantidade", "texto_quantidade", "material",
                     "texto_material", "acabamento", "texto_acabamento", "justificativa"],
    }
    return [
        {"type": "function", "function": {
            "name": "ver_detalhe",
            "description": "Amplia a região de uma ou mais candidatas. Com mostrar_filhos=true, marca também as candidatas internas com seus IDs e medidas.",
            "parameters": {"type": "object", "properties": {"ids": ids, "mostrar_filhos": {"type": "boolean"}}, "required": ["ids", "mostrar_filhos"]},
        }},
        {"type": "function", "function": {
            "name": "medir_uniao",
            "description": "Calcula a medida exata da caixa que envolve várias candidatas (para produtos que o cliente não agrupou).",
            "parameters": {"type": "object", "properties": {"ids": ids}, "required": ["ids"]},
        }},
        {"type": "function", "function": {
            "name": "finalizar",
            "description": "Entrega o pedido interpretado.",
            "parameters": {"type": "object", "properties": {
                "itens": {"type": "array", "items": item},
                "perguntas": {"type": "array", "items": {"type": "object", "properties": {
                    "pergunta": {"type": "string"}, "ids": {"type": "array", "items": {"type": "string"}},
                }, "required": ["pergunta", "ids"]}},
                "observacoes": {"type": "string"},
            }, "required": ["itens", "perguntas", "observacoes"]},
        }},
    ]


def _caixa_uniao(fatos: dict, ids: list[str]) -> dict:
    caixas = [fatos["candidatos"][i]["caixa_cm"] for i in ids]
    return {
        "esquerda": min(c["esquerda"] for c in caixas), "direita": max(c["direita"] for c in caixas),
        "base": min(c["base"] for c in caixas), "topo": max(c["topo"] for c in caixas),
    }


def _descrever_filhos(fatos: dict, ids: list[str]) -> str:
    linhas = []
    for candidato_id in ids:
        c = fatos["candidatos"][candidato_id]
        linhas.append(f"{candidato_id}: {_medida(c)}, ocorrências {c.get('quantidade_geometrica', 1)}")
        for filho_id in c.get("filhos_ids") or []:
            filho = fatos["candidatos"].get(filho_id)
            if filho:
                linhas.append(
                    f"  - {filho_id}: {_medida(filho)}, ocorrências {filho.get('quantidade_geometrica', 1)}"
                    + (f", contém {len(filho.get('filhos_ids') or [])}" if filho.get("filhos_ids") else "")
                )
    return "\n".join(linhas)


# ---------------------------------------------------------------- validação

def _normalizar(texto) -> str:
    texto = "".join(
        c for c in unicodedata.normalize("NFKD", str(texto or "").casefold()) if not unicodedata.combining(c)
    )
    return " ".join(texto.split())


def _ancestrais(fatos: dict, candidato_id: str) -> set[str]:
    vistos = set()
    atual = fatos["candidatos"].get(candidato_id, {}).get("pai_id")
    while atual and atual not in vistos:
        vistos.add(atual)
        atual = fatos["candidatos"].get(atual, {}).get("pai_id")
    return vistos


# Abreviações e sinônimos usados nas montagens da gráfica.
_SINONIMOS = {
    "ads": "adesivo", "adesivos": "adesivo", "vinil": "adesivo", "vinilico": "adesivo",
    "banner": "lona", "banners": "lona", "lonas": "lona",
    "rec": "recorte", "recortado": "recorte", "recortados": "recorte", "recortada": "recorte", "recortadas": "recorte",
    "ilhoses": "ilhos", "ilhois": "ilhos",
}


def _termos(texto) -> list[str]:
    termos = []
    for palavra in re.findall(r"[^\W\d_]+", _normalizar(texto)):
        palavra = _SINONIMOS.get(palavra, palavra)
        if len(palavra) >= 3 or palavra in {"sem", "com"}:
            termos.append(palavra)
    return termos


def _quantidade_de_cada(texto) -> int | None:
    """Quantidade por peça em instruções como "3 UNIDADES DE CADA"."""
    if not texto or not re.search(r"(?i)\bde\s+cada\b", str(texto)):
        return None
    from .pedido import parse_quantidade

    instrucao = parse_quantidade(str(texto))
    return instrucao[0] if instrucao else None


def _cita(fatos: dict, texto_id, valor: str) -> bool:
    """O texto citado contém todos os termos relevantes do valor (com abreviações expandidas)?"""
    if texto_id == "NOME_ARQUIVO":
        fonte = fatos["arquivo"]
    elif texto_id in fatos["textos"]:
        fonte = fatos["textos"][texto_id]["texto"]
    else:
        return False
    termos_fonte = _termos(fonte)
    return all(
        any(t == f or (len(t) >= 5 and len(f) >= 5 and t[:5] == f[:5]) for f in termos_fonte)
        for t in _termos(valor)
    )


def validar(fatos: dict, resposta: dict) -> list[str]:
    erros = []
    usados: dict[str, int] = {}
    for n, item in enumerate(resposta.get("itens") or [], 1):
        ids = item.get("ids") or []
        desconhecidos = [i for i in ids if i not in fatos["candidatos"]]
        if desconhecidos or not ids:
            erros.append(f"Item {n}: IDs inexistentes {desconhecidos or '(nenhum)'}.")
            continue
        for candidato_id in ids:
            if candidato_id in usados:
                erros.append(f"Item {n}: {candidato_id} já está no item {usados[candidato_id]}.")
            usados[candidato_id] = n
        if item.get("combinar") == "nao" and len(ids) > 1:
            medidas = {(round(fatos["candidatos"][i]["largura_cm"] * 2) / 2, round(fatos["candidatos"][i]["altura_cm"] * 2) / 2) for i in ids}
            if len(medidas) > 1:
                erros.append(f"Item {n}: IDs com medidas diferentes {sorted(medidas)}; separe em itens ou use combinar='uniao'.")
        quantidade = item.get("quantidade")
        desenhadas = sum(int(fatos["candidatos"][i].get("quantidade_geometrica") or 1) for i in ids)
        if item.get("origem_quantidade") == "texto":
            texto_id = item.get("texto_quantidade")
            texto = fatos["textos"].get(texto_id, {}).get("texto") if texto_id != "NOME_ARQUIVO" else fatos["arquivo"]
            por_peca = _quantidade_de_cada(texto)
            if not texto:
                erros.append(f"Item {n}: texto_quantidade {texto_id!r} não existe.")
            elif por_peca and desenhadas > 1:
                # "N de cada" com K peças desenhadas no item: o total é N × K.
                if quantidade != por_peca * desenhadas:
                    erros.append(
                        f"Item {n}: \"{texto}\" pede {por_peca} de cada e este item reúne {desenhadas} peças "
                        f"desenhadas; use quantidade {por_peca * desenhadas} ou separe em {desenhadas} itens "
                        f"de {por_peca} unidades (investigue os IDs internos com ver_detalhe)."
                    )
            elif not re.search(rf"(?<!\d){quantidade}(?!\d)", texto):
                erros.append(f"Item {n}: o texto {texto_id} (\"{texto}\") não contém a quantidade {quantidade}.")
        elif item.get("origem_quantidade") == "ocorrencias_desenhadas":
            esperado = 1 if item.get("combinar") == "uniao" else desenhadas
            if quantidade != esperado:
                erros.append(f"Item {n}: {quantidade} unidades, mas há {esperado} ocorrência(s) desenhada(s) nesses IDs.")
        for campo in ("material", "acabamento"):
            valor, fonte = item.get(campo), item.get(f"texto_{campo}")
            if valor and not _cita(fatos, fonte, valor):
                erros.append(f"Item {n}: {campo} '{valor}' sem texto que o comprove ({fonte!r}); cite o ID correto ou use null.")
        acabamento, material = item.get("acabamento"), item.get("material")
        if acabamento and material and _termos(acabamento) and set(_termos(acabamento)) <= set(_termos(material)):
            erros.append(
                f"Item {n}: acabamento '{acabamento}' repete o material; acabamento é o que se faz depois "
                "da impressão (recorte, laminação, ilhós, bainha...). Se nenhum foi pedido, use null."
            )
    ids_por_item = {n: set(item.get("ids") or []) for n, item in enumerate(resposta.get("itens") or [], 1)}
    for n, ids in ids_por_item.items():
        for m, outros in ids_por_item.items():
            if n >= m:
                continue
            for a in ids:
                for b in outros:
                    if a in _ancestrais(fatos, b) or b in _ancestrais(fatos, a):
                        erros.append(f"Itens {n} e {m}: {a} e {b} estão um dentro do outro; a mesma peça seria contada duas vezes.")
    return erros


def resultado_do_agente(fatos: dict, resposta: dict) -> dict:
    itens = []
    for item in resposta.get("itens") or []:
        ids = [i for i in item.get("ids") or [] if i in fatos["candidatos"]]
        if not ids:
            continue
        if item.get("combinar") == "uniao":
            caixa = _caixa_uniao(fatos, ids)
            largura, altura = caixa["direita"] - caixa["esquerda"], caixa["topo"] - caixa["base"]
        else:
            largura, altura = fatos["candidatos"][ids[0]]["largura_cm"], fatos["candidatos"][ids[0]]["altura_cm"]
        itens.append({
            "indice": len(itens) + 1,
            "quantidade": {"valor": int(item["quantidade"]), "fonte": "agente", "texto_origem": item.get("texto_quantidade")},
            "dimensoes": {"largura_mm": round(largura * 10, 2), "altura_mm": round(altura * 10, 2), "fonte": "geometria_cdr"},
            "material": {"valor": item.get("material"), "fonte": "agente", "texto_origem": item.get("texto_material")},
            "acabamento": {"valor": item.get("acabamento"), "fonte": "agente", "texto_origem": item.get("texto_acabamento")},
            "candidatos": ids, "justificativa": item.get("justificativa"),
        })
    return {
        "itens": itens, "total_unidades": sum(i["quantidade"]["valor"] for i in itens),
        "perguntas": resposta.get("perguntas") or [], "observacoes": resposta.get("observacoes"),
    }


# ---------------------------------------------------------------- execução

def _sem_imagens(mensagens: list[dict]) -> list[dict]:
    limpas = []
    for mensagem in mensagens:
        conteudo = mensagem.get("content")
        if isinstance(conteudo, list):
            conteudo = [
                {"type": "image_url", "image_url": "<imagem>"} if parte.get("type") == "image_url" else parte
                for parte in conteudo
            ]
        limpas.append({**mensagem, "content": conteudo})
    return limpas


def _contrato_sem_ferramentas() -> str:
    """Pedido de resposta única, para modelos locais que não usam ferramentas."""
    esquema = _ferramentas()[-1]["function"]["parameters"]
    return (
        "\n\nVocê NÃO tem ferramentas: responda de uma vez só, com um único objeto JSON válido, "
        "sem texto em volta e sem cercas de código, seguindo este JSON Schema: "
        + json.dumps(esquema, ensure_ascii=False)
        + "\nUse apenas IDs existentes na ficha. Se precisar separar artes diferentes reunidas numa "
        "candidata, use os IDs internos citados na ficha."
    )


def interpretar_com_agente(
    caminho: Path, chave: str, modelo: str, fatos: dict | None = None, custo_maximo_usd: float | None = None,
    preco_por_token: tuple[float, float] | None = None, base_url: str = URL_OPENROUTER,
    usar_ferramentas: bool = True,
) -> dict:
    """Executa o agente e devolve resultado no formato do pedido, com rastro para auditoria.

    ``custo_maximo_usd`` interrompe o pedido quando o gasto informado pelo
    OpenRouter ultrapassa o limite (OrcamentoExcedido). Se a resposta não trouxer
    o custo, ele é estimado por ``preco_por_token`` (entrada, saída).

    ``base_url`` permite um servidor local compatível com a API da OpenAI
    (LM Studio, Ollama); com ``usar_ferramentas=False`` o modelo responde de uma
    vez só, sem investigar, o que costuma ser necessário em modelos pequenos.
    """
    from openai import OpenAI

    inicio = perf_counter()
    fatos = fatos or extrair_fatos(caminho)
    local = base_url != URL_OPENROUTER
    cliente = OpenAI(
        api_key=chave or "local", base_url=base_url, timeout=900 if local else 240,
        default_headers=None if local else {"X-Title": "Leitor de Pedidos CDR"},
    )
    sistema = PROMPT_SISTEMA
    if not usar_ferramentas:
        sistema += _contrato_sem_ferramentas()
    casa = regras_da_casa()
    if casa:
        sistema += "\n\nREGRAS DA CASA (convenções desta gráfica):\n" + casa
    conteudo = [{"type": "text", "text": ficha_fatos(fatos)}]
    for rotulo, url in zip(("Imagem limpa:", "Imagem com IDs:"), imagens_iniciais(fatos)):
        conteudo += [{"type": "text", "text": rotulo}, {"type": "image_url", "image_url": {"url": url}}]
    mensagens: list[dict] = [{"role": "system", "content": sistema}, {"role": "user", "content": conteudo}]
    rastro = {"modelo": modelo, "imagem_origem": fatos["imagem_origem"], "chamadas": 0, "custo_usd": 0.0, "correcoes": []}
    correcoes = 0
    resposta_final = None

    for _ in range(MAX_RODADAS):
        opcoes = {"max_tokens": 6000}
        if usar_ferramentas:
            opcoes.update(tools=_ferramentas(), tool_choice="auto")
        if not local:
            opcoes["extra_body"] = {"provider": {"data_collection": "deny"}, "usage": {"include": True}}
        resposta = cliente.chat.completions.create(model=modelo, messages=mensagens, **opcoes)
        rastro["chamadas"] += 1
        uso = getattr(resposta, "usage", None)
        custo = getattr(uso, "cost", None) if uso else None
        if custo is None and uso is not None:
            custo = (getattr(uso, "model_extra", None) or {}).get("cost")
        if custo is None and uso is not None and preco_por_token:
            custo = (int(getattr(uso, "prompt_tokens", 0) or 0) * preco_por_token[0]
                     + int(getattr(uso, "completion_tokens", 0) or 0) * preco_por_token[1])
        rastro["custo_usd"] += float(custo or 0)
        rastro.setdefault("tokens", {"entrada": 0, "saida": 0})
        rastro["tokens"]["entrada"] += int(getattr(uso, "prompt_tokens", 0) or 0)
        rastro["tokens"]["saida"] += int(getattr(uso, "completion_tokens", 0) or 0)
        if custo_maximo_usd is not None and rastro["custo_usd"] > custo_maximo_usd:
            raise OrcamentoExcedido(
                f"Pedido interrompido: US$ {rastro['custo_usd']:.4f} excede o limite de US$ {custo_maximo_usd:.4f}."
            )
        if not resposta.choices:
            raise RuntimeError(f"O modelo {modelo} não devolveu resposta.")
        mensagem = resposta.choices[0].message
        if not usar_ferramentas:
            # Resposta única: o validador aprova ou devolve os erros para correção.
            mensagens.append({"role": "assistant", "content": mensagem.content or ""})
            try:
                proposta = extrair_json_resposta(mensagem.content or "")
            except RuntimeError as erro:
                erros = [str(erro)]
                proposta = {"itens": [], "perguntas": [], "observacoes": ""}
            else:
                erros = validar(fatos, proposta)
            if erros and correcoes < MAX_CORRECOES:
                correcoes += 1
                rastro["correcoes"].append(erros)
                mensagens.append({
                    "role": "user",
                    "content": "Corrija e responda de novo, só com o JSON:\n- " + "\n- ".join(erros),
                })
                continue
            resposta_final = proposta
            rastro["erros_restantes"] = erros
            break
        chamadas = mensagem.tool_calls or []
        mensagens.append({
            "role": "assistant", "content": mensagem.content or "",
            **({"tool_calls": [c.model_dump() for c in chamadas]} if chamadas else {}),
        })
        if not chamadas:
            mensagens.append({"role": "user", "content": "Use as ferramentas; entregue o resultado chamando `finalizar`."})
            continue
        imagens_pendentes = []
        for chamada in chamadas:
            try:
                argumentos = json.loads(chamada.function.arguments or "{}")
            except json.JSONDecodeError:
                argumentos = {}
            nome = chamada.function.name
            ids_validos = [i for i in argumentos.get("ids") or [] if i in fatos["candidatos"]]
            if nome == "ver_detalhe":
                if not ids_validos:
                    saida = "Nenhum ID válido."
                else:
                    url = recorte(fatos, ids_validos, bool(argumentos.get("mostrar_filhos")))
                    saida = _descrever_filhos(fatos, ids_validos) + ("\n(imagem ampliada a seguir)" if url else "\n(sem imagem)")
                    if url:
                        imagens_pendentes.append((f"Detalhe de {', '.join(ids_validos)}:", url))
            elif nome == "medir_uniao":
                if not ids_validos:
                    saida = "Nenhum ID válido."
                else:
                    caixa = _caixa_uniao(fatos, ids_validos)
                    saida = f"União de {', '.join(ids_validos)}: {caixa['direita'] - caixa['esquerda']:.2f} x {caixa['topo'] - caixa['base']:.2f} cm"
            elif nome == "finalizar":
                erros = validar(fatos, argumentos)
                if erros and correcoes < MAX_CORRECOES:
                    correcoes += 1
                    rastro["correcoes"].append(erros)
                    saida = "Rejeitado pelo validador. Corrija e chame finalizar novamente:\n- " + "\n- ".join(erros)
                else:
                    resposta_final = argumentos
                    rastro["erros_restantes"] = erros
                    saida = "Recebido."
            else:
                saida = f"Ferramenta desconhecida: {nome}"
            mensagens.append({"role": "tool", "tool_call_id": chamada.id, "content": saida})
        if resposta_final is not None:
            break
        if imagens_pendentes:
            partes = []
            for rotulo, url in imagens_pendentes:
                partes += [{"type": "text", "text": rotulo}, {"type": "image_url", "image_url": {"url": url}}]
            mensagens.append({"role": "user", "content": partes})

    if resposta_final is None:
        raise RuntimeError(f"O agente não finalizou em {MAX_RODADAS} rodadas.")
    resultado = resultado_do_agente(fatos, resposta_final)
    rastro["duracao_s"] = round(perf_counter() - inicio, 1)
    rastro["resposta"] = resposta_final
    rastro["mensagens"] = _sem_imagens(mensagens)
    resultado["rastro_agente"] = rastro
    if rastro.get("erros_restantes"):
        resultado["alertas"] = [{"codigo": "AGENTE_COM_ERROS_DE_VALIDACAO", "severidade": "revisao", "mensagem": e} for e in rastro["erros_restantes"]]
    return resultado
