"""Interpretação auditável de pedidos montados em arquivos CDR.

A camada combina texto nativo e geometria do contêiner ZCF. Cada conclusão
mantém sua fonte e confiança; informação ausente vira pendência, não palpite.
"""
from __future__ import annotations

from collections import defaultdict
from math import hypot
from pathlib import Path
import re
from types import SimpleNamespace
import unicodedata

from .container import abrir_cdr


_QUANTIDADE = re.compile(
    r"(?ix)(?:\bq(?:td|uantidade)?\s*[:=-]?\s*)?"
    # "x" só é unidade quando não separa duas medidas: "6x" sim, "2,15 x 1,95" não.
    r"(?<![\d,.])(?P<valor>\d+)\s*(?P<unidade>uni|un(?:d|id(?:ade)?s?)?|u(?:n)?|x(?!\s*\d))\b"
)


# "50 ADESIVOS 8CM", "2 LONAS 3X1": o número antes do nome do produto é a quantidade.
_QUANTIDADE_PRODUTO = re.compile(
    r"(?i)(?<![\d,.])(?P<valor>\d+)\s*(?:adesivos?|lonas?|banners?|placas?|ps|pe[çc]as?|impress(?:[õo]es|[ãa]o)|c[óo]pias?)\b"
)


def _descolar(texto: str) -> str:
    """Separa a unidade grudada na palavra seguinte: "50undads" vira "50und ads"."""
    return re.sub(r"(?i)(\d\s*und)(?=[a-z])", r"\1 ", texto)


def parse_quantidade(texto: str) -> tuple[int, str] | None:
    """Reconhece formas usuais como ``1und``, ``2 un``, ``qtd: 5`` e ``50 adesivos``."""
    texto = _descolar(texto)
    match =_QUANTIDADE.search(texto.strip()) or _QUANTIDADE_PRODUTO.search(texto)
    if match is None:
        match_qtd = re.search(r"(?i)\bq(?:td|uantidade)?\s*[:=-]?\s*(\d+)\b", texto)
        if match_qtd is None:
            return None
        return int(match_qtd.group(1)), "unidade"
    return int(match.group("valor")), "unidade"


# Erros de digitação comuns: "trasnparente", "trasparente", "tranparente".
_TRANSPARENTE = r"tra(?:ns|sn|s|n)parente"

_MODIFICADORES_ADESIVO = (
    "branco", "fosco", "brilho", "brilhoso", _TRANSPARENTE, "leitoso", "blackout",
    "perfurado", "jateado", "refletivo", "prism[aá]tico", "super", "cola", "normal",
)


def parse_material(texto: str) -> dict | None:
    """Extrai material e acabamento de instruções usuais da gráfica."""
    normalizado = _descolar(" ".join(texto.casefold().split()))
    # "leitoso com trasparente aplicado em cima" é laminação: o transparente não é o material.
    laminacao_transparente = re.search(
        r"(?:\bcom\s+)?(?:o\s+)?" + _TRANSPARENTE + r"\s+aplicad[oa]\s+(?:em|por)\s+cima", normalizado
    )
    laminacao = laminacao_transparente is not None or re.search(r"\blamina(?:d[oa]s?|[çc][ãa]o)\b", normalizado)
    if laminacao_transparente:
        normalizado = " ".join(normalizado.replace(laminacao_transparente.group(0), " ").split())
    # "ads" é adesivo quando descreve o pedido ("1und ads leitoso", "ads recortados");
    # sozinho num texto da arte ("Google Ads") não é.
    if re.search(r"\d\s*(?:und\s+)?ads\b|\bads\s+(?:recort|com\b|sem\b|" + "|".join(_MODIFICADORES_ADESIVO) + ")", normalizado):
        normalizado = re.sub(r"\bads\b", "adesivo", normalizado)
    # Início de palavra: "Qd_Institucional" não é lona ("_" também separa palavras).
    palavras = normalizado.replace("_", " ")
    adesivo = re.search(r"\b(?:adesivo|vinil)", palavras) is not None
    # Rótulo curto "TRANPARENTE COM BRANCO" já diz o adesivo; numa frase da arte não.
    adesivo = adesivo or (re.search(r"\b" + _TRANSPARENTE + r"\b", palavras) is not None and len(palavras.split()) <= 5)
    banner = re.search(r"\b(?:banner|lona)", palavras) is not None
    # "Papel outdor" é erro comum e "painel outdoor" é o mesmo papel; "outdoor"
    # sozinho pode ser só o tema da arte.
    papel = re.search(r"\b(?:papel|paine(?:l|is))\s+out\s?doo?r\b", palavras) is not None
    # "1 PS ADESIVADO", "placa de PS 2mm": a peça é a placa, mesmo com vinil aplicado.
    # "PS" solto num texto da arte (um "PS:" no fim de um recado) não é material.
    ps = re.search(r"\bps\b", palavras) is not None and re.search(
        r"\d\s*ps\b|\bplacas?\b|\badesivad[oa]s?\b|\bps\s*\d\s*mm\b", palavras
    ) is not None
    if ps and not banner and not papel:
        espessura = re.search(r"\b([12])\s*mm\b", palavras)
        material = "ps" + (f" {espessura.group(1)} mm" if espessura else "")
        if re.search(r"\badesiv", palavras):
            material += " adesivado"
        return {"material": material, "acabamento": None}
    if adesivo + banner + papel > 1:
        return None  # documento misto: a associação precisa ser regional
    if papel:
        return {"material": "papel outdoor", "acabamento": None}
    if not adesivo and not banner:
        return None
    if banner:
        # Na gráfica, banner é lona com acabamento de bastão e cordinha.
        material = "lona"
    elif re.search(_TRANSPARENTE, normalizado):
        material = "adesivo transparente"
    elif "fosco" in normalizado:
        material = "adesivo fosco"
    elif "super cola" in normalizado:
        material = "adesivo super cola"
    elif "leitoso" in normalizado:
        material = "adesivo leitoso"
    elif "normal" in normalizado:
        material = "adesivo normal"
    else:
        material = "adesivo"
    if not banner:
        # "ADESIVO BRANCO FOSCO BLACKOUT" é outro material que "adesivo fosco":
        # quando o texto descreve o adesivo com palavras conhecidas, vale a descrição inteira.
        descricao = re.search(r"\b(?:adesivos?|vinil)((?:\s+(?:" + "|".join(_MODIFICADORES_ADESIVO) + r"))+)\b", normalizado)
        if descricao:
            material = "adesivo " + re.sub(_TRANSPARENTE, "transparente", " ".join(descricao.group(1).split()))
        # Branco aplicado por baixo do transparente é outro pedido que o transparente puro.
        if material == "adesivo transparente" and re.search(r"\bcom\s+(?:o\s+)?branco\b", normalizado):
            material = "adesivo transparente com branco"
    if re.search(r"\b(?:somente|apenas)\s+recorte\b", normalizado):
        acabamento = "somente recorte"
    elif re.search(r"\b(?:re)?corte especial\b", normalizado) or "com recorte" in normalizado:
        acabamento = "recorte especial"
    elif re.search(r"\bsem\s+rec(?:orte|ortad[oa]s?|\.)?\b", normalizado):
        acabamento = "sem recorte"
    elif re.search(r"\brecortad[oa]s?\b", normalizado):
        acabamento = "recortado"
    elif re.search(r"\bbanners?\b", palavras):
        acabamento = "banner"
    else:
        acabamento = None
    if laminacao:
        acabamento = f"{acabamento} + laminação" if acabamento else "laminação"
    return {"material": material, "acabamento": acabamento}


def parse_dimensoes(texto: str) -> dict | None:
    """Reconhece dimensões; sem unidade somente quando há contexto de quantidade."""
    sem_acentos = "".join(
        caractere for caractere in unicodedata.normalize("NFKD", _descolar(texto).casefold())
        if not unicodedata.combining(caractere)
    )
    # A unidade pode vir só no fim ("60x90cm") ou nas duas medidas ("1,10M X 2,40M").
    dimensao = re.search(
        r"(?<!\d)(\d+(?:[.,]\d+)?)\s*(?:(mm|cm|m)\s*)?[x×]\s*(\d+(?:[.,]\d+)?)\s*(mm|cm|m)?\b",
        sem_acentos,
    )
    if dimensao is None:
        return None
    unidade = dimensao.group(4) or dimensao.group(2)
    if unidade is None:
        # Evita interpretar telefone, código ou texto da arte como dimensão.
        contexto_quantidade = re.search(
            r"(?i)(?:\bq(?:td|uantidade)?\s*[:=-]?\s*\d+\b|\b\d+\s*un(?:d|id(?:ade)?s?)?\b)",
            sem_acentos,
        )
        if contexto_quantidade is None:
            return None
        unidade = "cm"
    fator = {"mm": 1.0, "cm": 10.0, "m": 1000.0}[unidade]
    return {
        "largura_mm": float(dimensao.group(1).replace(",", ".")) * fator,
        "altura_mm": float(dimensao.group(3).replace(",", ".")) * fator,
        "texto_origem": dimensao.group(0),
    }


def interpretar_nome_arquivo(nome: str) -> dict:
    """Extrai somente evidências explícitas do nome, sempre com baixa prioridade."""
    base = Path(nome).stem
    texto = " ".join(base.replace("_", " ").replace("-", " ").split())
    sem_acentos = "".join(
        caractere for caractere in unicodedata.normalize("NFKD", texto.casefold())
        if not unicodedata.combining(caractere)
    )
    # "ADS" é a abreviação de adesivo nos nomes de arquivo; no texto da arte pode ser outra coisa.
    material = parse_material(re.sub(r"\bads\b", "adesivo", sem_acentos))
    quantidade = parse_quantidade(sem_acentos)
    dimensoes = parse_dimensoes(sem_acentos)
    if dimensoes is None:
        sem_unidade = re.search(r"(?<!\d)(\d+(?:[.,]\d+)?)\s*[x×]\s*(\d+(?:[.,]\d+)?)(?!\d)", sem_acentos)
        if sem_unidade:
            a, b = (float(valor.replace(",", ".")) for valor in sem_unidade.groups())
            # Nomes como 1,00x0,55 ou 3x1 expressam metros; 71X61 ou 60 X90, centímetros.
            fator = 1000.0 if max(a, b) <= 5 else 10.0
            dimensoes = {"largura_mm": a * fator, "altura_mm": b * fator, "texto_origem": sem_unidade.group(0)}
    return {"texto": texto, "material": material, "quantidade": quantidade, "dimensoes": dimensoes}


def _caixa_mm(caixa) -> dict[str, float]:
    return {
        "esquerda": round(caixa.esquerda / 10_000.0, 3),
        "base": round(caixa.base / 10_000.0, 3),
        "direita": round(caixa.direita / 10_000.0, 3),
        "topo": round(caixa.topo / 10_000.0, 3),
    }


def _centro(caixa) -> tuple[float, float]:
    return ((caixa.esquerda + caixa.direita) / 2.0, (caixa.base + caixa.topo) / 2.0)


def _area(caixa) -> float:
    return max(0, caixa.direita - caixa.esquerda) * max(0, caixa.topo - caixa.base)


def _area_intersecao(a, b) -> float:
    largura = max(0, min(a.direita, b.direita) - max(a.esquerda, b.esquerda))
    altura = max(0, min(a.topo, b.topo) - max(a.base, b.base))
    return largura * altura


def _contem(externa, interna, tolerancia: int = 100) -> bool:
    return (
        externa.esquerda - tolerancia <= interna.esquerda
        and externa.direita + tolerancia >= interna.direita
        and externa.base - tolerancia <= interna.base
        and externa.topo + tolerancia >= interna.topo
    )


def _distancia(a, b) -> float:
    ax, ay = _centro(a)
    bx, by = _centro(b)
    return hypot(ax - bx, ay - by)


def _textos_quantidade(doc) -> list[dict]:
    encontrados = []
    vistos = set()
    for item in doc.textos_por_objeto() or ():
        caixa = item.objeto.caixa
        quantidade = parse_quantidade(item.fluxo.texto)
        if caixa is None or quantidade is None:
            continue
        chave = (item.fluxo.texto.strip().casefold(), caixa.esquerda, caixa.base, caixa.direita, caixa.topo)
        if chave in vistos:
            continue
        vistos.add(chave)
        encontrados.append({
            "valor": quantidade[0], "unidade": quantidade[1],
            "texto_origem": item.fluxo.texto, "objeto": item.objeto,
            "dimensoes": parse_dimensoes(item.fluxo.texto),
        })
    return encontrados


def _textos_material(doc) -> list[dict]:
    encontrados = []
    for item in doc.textos_por_objeto() or ():
        if item.objeto.caixa is None:
            continue
        material = parse_material(item.fluxo.texto)
        if material is not None:
            encontrados.append({
                **material,
                "texto_origem": item.fluxo.texto,
                "quantidade": parse_quantidade(item.fluxo.texto),
                "objeto": item.objeto,
            })
    return encontrados


def _evidencias_textuais(doc) -> list[dict]:
    """Expõe texto nativo com posição para a etapa de associação regional."""
    evidencias, vistos = [], set()
    for item in doc.textos_por_objeto() or ():
        texto = " ".join(item.fluxo.texto.split()).strip()
        caixa = item.objeto.caixa
        if not texto or caixa is None:
            continue
        chave = (texto.casefold(), caixa.esquerda, caixa.base, caixa.direita, caixa.topo)
        if chave in vistos:
            continue
        vistos.add(chave)
        evidencias.append({
            "texto": texto, "caixa_mm": _caixa_mm(caixa),
            "quantidade": (parse_quantidade(texto) or (None,))[0],
            "dimensoes": parse_dimensoes(texto), "material": parse_material(texto),
        })
    return evidencias


def _estrutura_visivel(doc):
    """Estrutura com a caixa do conteúdo de PowerClip recortada pela máscara."""
    visivel = getattr(doc, "estrutura_visivel", None)
    return visivel() if visivel is not None else doc.estrutura()


def _molduras_do_grupo(conteudo: list) -> list:
    """Molduras de peças distintas montadas dentro de um único grupo de topo.

    É comum agrupar tudo (título e várias peças) num grupo só. Cada peça é então
    um subgrupo cujo retângulo de contorno tem a mesma caixa do subgrupo. Só vale
    quando há pelo menos duas molduras sem sobreposição e todo objeto que não é
    texto está dentro de alguma delas; caso contrário o grupo segue como uma peça.
    """
    tolerancia = 10_000  # 1 mm
    molduras = []
    for posicao, item in enumerate(conteudo):
        if item.tipo != "obj" or item.tipo_objeto != "retangulo" or item.caixa is None:
            continue
        profundidade = len(item.ancestrais)
        pai = next((anterior for anterior in reversed(conteudo[:posicao])
                    if anterior.tipo == "grp" and len(anterior.ancestrais) == profundidade - 1), None)
        if pai is None or pai.caixa is None:
            continue
        if _contem(pai.caixa, item.caixa, tolerancia) and _contem(item.caixa, pai.caixa, tolerancia):
            molduras.append(item)
    molduras = [
        moldura for moldura in molduras
        if not any(outra is not moldura and _area(outra.caixa) > _area(moldura.caixa) * 1.05
                   and _contem(outra.caixa, moldura.caixa, tolerancia) for outra in molduras)
    ]
    if len(molduras) < 2:
        return []
    for indice, moldura in enumerate(molduras):
        for outra in molduras[indice + 1:]:
            if _area_intersecao(moldura.caixa, outra.caixa) > 0.02 * min(_area(moldura.caixa), _area(outra.caixa)):
                return []
    for item in conteudo:
        if item.tipo != "obj" or item.tipo_objeto == "texto" or item.caixa is None:
            continue
        if not any(_contem(moldura.caixa, item.caixa, tolerancia) for moldura in molduras):
            return []
    return molduras


def _copias_do_grupo(conteudo: list) -> list:
    """Subgrupos idênticos lado a lado (6 logos agrupados) numa folha de peças recortadas."""
    tolerancia = 10_000  # 1 mm
    filhos = [item for item in conteudo if item.tipo == "grp" and len(item.ancestrais) == 1 and item.caixa is not None]
    if len(filhos) < 2:
        return []
    largura, altura = filhos[0].caixa.direita - filhos[0].caixa.esquerda, filhos[0].caixa.topo - filhos[0].caixa.base
    if any(abs(f.caixa.direita - f.caixa.esquerda - largura) > tolerancia
           or abs(f.caixa.topo - f.caixa.base - altura) > tolerancia for f in filhos):
        return []
    for indice, filho in enumerate(filhos):
        for outro in filhos[indice + 1:]:
            if _area_intersecao(filho.caixa, outro.caixa) > 0.02 * _area(filho.caixa):
                return []
    for item in conteudo:
        if item.tipo == "obj" and item.caixa is not None and not any(_contem(f.caixa, item.caixa, tolerancia) for f in filhos):
            return []
    return filhos


def _folhas_de_marcacao(doc, estrutura: list, textos) -> list:
    """Retângulos brancos que só marcam a área de várias peças recortadas.

    O cliente às vezes desenha uma folha branca atrás das peças ("adesivo com
    recorte, 20cm cada círculo"). A folha não é peça quando: é branca ou vazia,
    tem dentro duas ou mais formas fechadas separadas e o pedido fala em recorte
    ou em "cada". Sem esses três sinais, um adesivo retangular com fundo branco
    e artes dentro continua sendo uma peça só.
    """
    # "sem recorte" não separa as peças: a folha inteira segue como uma peça.
    if not any(
        re.search(r"(?i)\b(?:re)?cort|\bcada\b", t.fluxo.texto) and not re.search(r"(?i)\bsem\s+rec", t.fluxo.texto)
        for t in textos
    ):
        return []
    leitor = getattr(doc, "read", None)
    if leitor is None:
        return []
    from .page import parse_estilos
    from .render_proprio import _estilo_do_objeto, _preenchimento

    estilos = {}
    folhas = []
    topo = [o for o in estrutura if not o.ancestrais and o.caixa is not None and o.tipo_objeto != "texto"]
    for folha in topo:
        if folha.tipo != "obj" or folha.tipo_objeto != "retangulo":
            continue
        if folha.membro not in estilos:
            estilos[folha.membro] = parse_estilos(leitor(folha.membro)) if folha.membro else ()
        cor = _preenchimento(_estilo_do_objeto(folha, estilos))
        if cor is not None and min(cor[:3]) < 245:
            continue
        internas = []
        for objeto in topo:
            if objeto is folha or not _contem(folha.caixa, objeto.caixa) or _area(objeto.caixa) > 0.5 * _area(folha.caixa):
                continue
            # A arte de um PowerClip e a máscara dela ocupam a mesma caixa: contam uma vez.
            if not any(_contem(c, objeto.caixa, 10_000) and _contem(objeto.caixa, c, 10_000) for c in internas):
                internas.append(objeto.caixa)
        separadas = len(internas) >= 2 and all(
            _area_intersecao(a, b) <= 0.02 * min(_area(a), _area(b))
            for i, a in enumerate(internas) for b in internas[i + 1:]
        )
        if separadas:
            folhas.append(folha)
    return folhas


def _candidatos_arte(doc) -> list[dict]:
    """Seleciona caixas externas prováveis, evitando objetos internos duplicados."""
    estrutura = list(_estrutura_visivel(doc))
    textos = getattr(doc, "textos_por_objeto", lambda: ())() or ()
    folhas = _folhas_de_marcacao(doc, estrutura, textos)
    tipos_limite = {"bitmap", "retangulo", "curva", "desconhecido"}
    limites = [
        objeto for objeto in estrutura
        if objeto.tipo == "obj" and not objeto.ancestrais and objeto.caixa is not None
        and objeto.tipo_objeto in tipos_limite and not any(objeto is folha for folha in folhas)
    ]
    externos = []
    prioridade = {"retangulo": 4, "desconhecido": 4, "bitmap": 3, "curva": 2}
    for objeto in limites:
        # Curvas abertas costumam ser colchetes, linhas de agrupamento ou corte;
        # não delimitam por si só a área fechada de um produto.
        if objeto.tipo_objeto == "curva" and objeto.geometria_curva and objeto.geometria_curva.possui_subcaminho_aberto:
            continue
        contenedores = [
            outro for outro in limites
            if outro is not objeto and _area(outro.caixa) > _area(objeto.caixa) * 1.05
            and _contem(outro.caixa, objeto.caixa)
        ]
        if any(prioridade.get(outro.tipo_objeto, 0) >= prioridade.get(objeto.tipo_objeto, 0)
               for outro in contenedores):
            continue
        externos.append(objeto)

    # O conteúdo de um PowerClip (as fotos de uma colagem) fica guardado como grupo
    # de topo. Quando o recipiente está num grupo que tem uma forma do tamanho do
    # grupo inteiro (moldura, imagem de fundo ou a máscara da peça), a peça é esse
    # grupo e as fotos não são peças. Sem isso (pôsteres lado a lado, círculo solto
    # recortando a arte), cada conteúdo continua sendo peça.
    # Uma medida escrita no pedido ("1,10M X 2,40M") igual à do grupo também diz que
    # o grupo inteiro é a peça. Um conteúdo pode ter seus próprios PowerClips (fotos
    # dentro de um painel que está dentro da colagem): eles seguem a mesma peça.
    medidas_escritas = [m for m in (parse_dimensoes(t.fluxo.texto) for t in textos) if m]

    def medida_escrita(caixa) -> bool:
        largura, altura = (caixa.direita - caixa.esquerda) / 10_000, (caixa.topo - caixa.base) / 10_000
        return any(
            abs(largura - a) <= 0.02 * a and abs(altura - b) <= 0.02 * b
            for m in medidas_escritas
            for a, b in ((m["largura_mm"], m["altura_mm"]), (m["altura_mm"], m["largura_mm"]))
        )

    recortes = []  # (id do grupo de topo, é a peça inteira, ids recortados dentro dele)
    for posicao, topo in enumerate(estrutura):
        if topo.ancestrais or topo.tipo != "grp" or topo.caixa is None:
            continue
        fim = next((i for i in range(posicao + 1, len(estrutura)) if not estrutura[i].ancestrais), len(estrutura))
        filhos = estrutura[posicao + 1:fim]
        emoldurado = any(
            filho.tipo == "obj" and filho.tipo_objeto != "texto" and filho.caixa is not None and _contem(topo.caixa, filho.caixa, 10_000)
            and _contem(filho.caixa, topo.caixa, 10_000)
            for filho in filhos
        ) or medida_escrita(topo.caixa)
        ids = {filho.grupo_powerclip for filho in filhos if getattr(filho, "grupo_powerclip", None) is not None}
        recortes.append((getattr(topo, "id_estrutural", None), emoldurado, ids))
    conteudos_powerclip = set()
    while True:
        novos = set().union(*(ids for id_topo, emoldurado, ids in recortes
                              if emoldurado or id_topo in conteudos_powerclip)) - conteudos_powerclip
        if not novos:
            break
        conteudos_powerclip |= novos
    mascaras_soltas = {
        objeto.grupo_powerclip: objeto for objeto in estrutura
        if getattr(objeto, "grupo_powerclip", None) is not None and not objeto.ancestrais and objeto.caixa is not None
    }
    for inicio, grupo in enumerate(estrutura):
        if grupo.tipo != "grp" or grupo.ancestrais or grupo.caixa is None:
            continue
        if getattr(grupo, "id_estrutural", None) in conteudos_powerclip:
            continue
        area_grupo = _area(grupo.caixa)
        if area_grupo <= 0:
            continue
        sobreposto = any(
            _area_intersecao(grupo.caixa, limite.caixa) / min(area_grupo, _area(limite.caixa)) > 0.25
            for limite in externos if _area(limite.caixa) > 0
        )
        if not sobreposto:
            fim = next((i for i in range(inicio + 1, len(estrutura)) if not estrutura[i].ancestrais), len(estrutura))
            conteudo = estrutura[inicio + 1:fim]
            # Foto recortada por um círculo solto: a peça tem o tamanho do círculo.
            mascara = mascaras_soltas.get(getattr(grupo, "id_estrutural", None))
            externos.extend(
                _molduras_do_grupo(conteudo) or (folhas and _copias_do_grupo(conteudo)) or [mascara or grupo]
            )

    candidatos = []
    for objeto in externos:
        caixa = objeto.caixa
        largura_mm = (caixa.direita - caixa.esquerda) / 10_000.0
        altura_mm = (caixa.topo - caixa.base) / 10_000.0
        if largura_mm <= 1 or altura_mm <= 1 or max(largura_mm / altura_mm, altura_mm / largura_mm) > 100:
            continue
        candidatos.append({
            "objeto": objeto, "caixa": caixa, "tipo": objeto.tipo_objeto or "grupo",
            "largura_mm": round(largura_mm, 3), "altura_mm": round(altura_mm, 3),
        })
    return sorted(candidatos, key=lambda item: (item["caixa"].esquerda, -item["caixa"].topo))


def _inventario_geometrico(doc) -> list[dict]:
    """Expõe medidas profundas como hipóteses, sem promovê-las diretamente a itens.

    Montagens reais costumam colocar vários produtos dentro de um único grupo de
    topo. Caixas coincidentes (arte + contorno), repetições do mesmo tamanho,
    bitmaps e blocos numéricos são sinais úteis para a adjudicação visual.
    """
    estrutura = list(_estrutura_visivel(doc))
    inventario: list[dict] = []
    vistos = set()

    def adicionar(origem: str, quantidade: int, largura_cm: float, altura_cm: float, caixas, tipos) -> None:
        if largura_cm <= 0.1 or altura_cm <= 0.1:
            return
        if max(largura_cm / altura_cm, altura_cm / largura_cm) > 100:
            return
        centros = tuple(sorted(
            (round((c.esquerda + c.direita) / 200_000, 2), round((c.base + c.topo) / 200_000, 2))
            for c in caixas
        ))
        chave = (origem, quantidade, round(largura_cm, 2), round(altura_cm, 2), centros)
        if chave in vistos:
            return
        vistos.add(chave)
        inventario.append({
            "id": f"G{len(inventario) + 1}", "origem": origem,
            "quantidade_sugerida": quantidade,
            "largura_cm": round(largura_cm, 3), "altura_cm": round(altura_cm, 3),
            "posicoes_centro_cm": [{"x": x, "y": y} for x, y in centros],
            "tipos": sorted(set(tipos)),
        })

    # União dos objetos imprimíveis de cada grupo de topo, descartando os
    # cabeçalhos de texto. É especialmente útil em artes compostas por curvas.
    for inicio, grupo in enumerate(estrutura):
        if grupo.tipo != "grp" or grupo.ancestrais or grupo.caixa is None:
            continue
        fim = next((i for i in range(inicio + 1, len(estrutura)) if not estrutura[i].ancestrais), len(estrutura))
        filhos = [
            item for item in estrutura[inicio + 1:fim]
            if item.tipo == "obj" and item.tipo_objeto != "texto" and item.caixa is not None
        ]
        if not filhos:
            continue
        esquerda = min(item.caixa.esquerda for item in filhos)
        direita = max(item.caixa.direita for item in filhos)
        base = min(item.caixa.base for item in filhos)
        topo = max(item.caixa.topo for item in filhos)
        caixa_uniao = SimpleNamespace(esquerda=esquerda, direita=direita, base=base, topo=topo)
        adicionar(
            "uniao_grupo_sem_textos", 1,
            (direita - esquerda) / 100_000, (topo - base) / 100_000,
            [caixa_uniao], [item.tipo_objeto or "desconhecido" for item in filhos],
        )

    # Objetos com a mesma medida podem ser duplicatas sobrepostas (arte e
    # contorno) ou repetições físicas. Centros distintos definem a quantidade.
    por_medida = defaultdict(list)
    for item in estrutura:
        if item.tipo != "obj" or item.tipo_objeto == "texto" or item.caixa is None:
            continue
        largura = (item.caixa.direita - item.caixa.esquerda) / 100_000
        altura = (item.caixa.topo - item.caixa.base) / 100_000
        if largura > 0.1 and altura > 0.1:
            por_medida[(round(largura, 2), round(altura, 2))].append(item)
    medidas_repetidas = []
    for (largura, altura), objetos in por_medida.items():
        if len(objetos) < 2 and not any(item.tipo_objeto == "bitmap" for item in objetos):
            continue
        posicoes = {}
        for item in objetos:
            centro = (
                round((item.caixa.esquerda + item.caixa.direita) / 200_000, 2),
                round((item.caixa.base + item.caixa.topo) / 200_000, 2),
            )
            posicoes.setdefault(centro, item.caixa)
        medidas_repetidas.append({
            "largura": largura, "altura": altura, "objetos": objetos,
            "caixas": list(posicoes.values()), "quantidade": len(posicoes),
        })
    for candidato in medidas_repetidas:
        area = candidato["largura"] * candidato["altura"]
        dominado = any(
            outro is not candidato
            and outro["quantidade"] == candidato["quantidade"]
            and outro["largura"] * outro["altura"] > area * 1.1
            and all(any(_contem(caixa_maior, caixa) for caixa_maior in outro["caixas"])
                    for caixa in candidato["caixas"])
            for outro in medidas_repetidas
        )
        if dominado and not any(item.tipo_objeto == "bitmap" for item in candidato["objetos"]):
            continue
        adicionar(
            "objetos_mesma_medida", candidato["quantidade"],
            candidato["largura"], candidato["altura"], candidato["caixas"],
            [item.tipo_objeto or "desconhecido" for item in candidato["objetos"]],
        )

    # Sequências como 01..20 podem ser a própria arte, não uma instrução.
    for item in doc.textos_por_objeto() or ():
        texto = "".join(item.fluxo.texto.split())
        caixa = item.objeto.caixa
        digitos = sum(caractere.isdigit() for caractere in texto)
        if caixa is None or digitos < 8 or digitos / max(1, len(texto)) < 0.6:
            continue
        adicionar(
            "bloco_numerico", 1,
            (caixa.direita - caixa.esquerda) / 100_000,
            (caixa.topo - caixa.base) / 100_000,
            [caixa], ["texto_artistico"],
        )

    ordenado_bruto = sorted(inventario, key=lambda item: (
        item["posicoes_centro_cm"][0]["x"] if item["posicoes_centro_cm"] else 0,
        -(item["largura_cm"] * item["altura_cm"]),
    ))
    ordenado = []
    for item in ordenado_bruto:
        duplicado = any(
            anterior["quantidade_sugerida"] == item["quantidade_sugerida"]
            and abs(anterior["largura_cm"] - item["largura_cm"]) <= 0.02
            and abs(anterior["altura_cm"] - item["altura_cm"]) <= 0.02
            and anterior["posicoes_centro_cm"] == item["posicoes_centro_cm"]
            for anterior in ordenado
        )
        if not duplicado:
            ordenado.append(item)
        if len(ordenado) >= 80:
            break
    for indice, item in enumerate(ordenado, 1):
        item["id"] = f"G{indice}"
    return ordenado


def selecionar_inventario_geometrico(inventario: list[dict]) -> list[dict]:
    """Remove agregados e partes internas usando contenção entre hipóteses."""
    selecionados = [item for item in inventario if item.get("origem") != "uniao_grupo_sem_textos"]
    unioes = [item for item in inventario if item.get("origem") == "uniao_grupo_sem_textos"]

    def contem_centro(uniao: dict, centro: dict) -> bool:
        origem = uniao.get("posicoes_centro_cm") or []
        if not origem:
            return False
        cx, cy = origem[0]["x"], origem[0]["y"]
        return (
            cx - uniao["largura_cm"] / 2 <= centro["x"] <= cx + uniao["largura_cm"] / 2
            and cy - uniao["altura_cm"] / 2 <= centro["y"] <= cy + uniao["altura_cm"] / 2
        )

    for uniao in unioes:
        internos = [
            item for item in selecionados
            if item.get("id") != uniao.get("id")
            and item.get("posicoes_centro_cm")
            and all(contem_centro(uniao, centro) for centro in item["posicoes_centro_cm"])
        ]
        if len(internos) >= 2:
            continue  # caixa agregada que engloba produtos distintos
        if len(internos) == 1 and internos[0].get("quantidade_sugerida", 1) > 1:
            selecionados.remove(internos[0])
        selecionados.append(uniao)
    return sorted(selecionados, key=lambda item: item["posicoes_centro_cm"][0]["x"])


def _associar_um_a_um(candidatos: list[dict], referencias: list[dict]) -> dict[int, int]:
    pares = sorted(
        (_distancia(candidato["caixa"], referencia["objeto"].caixa), ci, ri)
        for ci, candidato in enumerate(candidatos)
        for ri, referencia in enumerate(referencias)
    )
    usados_candidatos = set()
    usados_referencias = set()
    resultado = {}
    for _, ci, ri in pares:
        if ci in usados_candidatos or ri in usados_referencias:
            continue
        resultado[ci] = ri
        usados_candidatos.add(ci)
        usados_referencias.add(ri)
    # "N de cada" é uma instrução de região, não uma relação um-para-um.
    for ri, referencia in enumerate(referencias):
        if not re.search(r"(?i)\bde\s+cada\b", referencia["texto_origem"]):
            continue
        caixa = referencia["objeto"].caixa
        margem = max((caixa.direita - caixa.esquerda) * 0.08, 200_000)  # 20 mm
        for ci, candidato in enumerate(candidatos):
            centro_x, centro_y = _centro(candidato["caixa"])
            if caixa.esquerda - margem <= centro_x <= caixa.direita + margem and centro_y < caixa.topo:
                resultado[ci] = ri
    return resultado


def _dimensoes_componentes(instancias) -> list[dict]:
    componentes = []
    for instancia in sorted(instancias, key=lambda i: i.objeto.caixa.esquerda):
        caixa = instancia.objeto.caixa
        componentes.append({
            "largura_mm": round((caixa.direita - caixa.esquerda) / 10_000.0, 3),
            "altura_mm": round((caixa.topo - caixa.base) / 10_000.0, 3),
            "pixels": {"largura": instancia.registro.imagem.largura, "altura": instancia.registro.imagem.altura},
            "dpi_efetivo": {
                "x": round(instancia.dpi_efetivo_x, 1) if instancia.dpi_efetivo_x else None,
                "y": round(instancia.dpi_efetivo_y, 1) if instancia.dpi_efetivo_y else None,
            },
            "espaco_cor": instancia.registro.imagem.espaco_de_cor,
            "identificador_bitmap": instancia.identificador_bitmap,
            "caixa_mm": _caixa_mm(caixa),
        })
    return componentes


def _aplicar_materiais(itens: list[dict], instrucoes: list[dict]) -> list[dict]:
    # "paineis outdoor 1und de cada" tem quantidade, mas fala de várias peças.
    de_cada = [item for item in instrucoes if re.search(r"(?i)\bcada\b", item["texto_origem"])]
    locais = [item for item in instrucoes if item["quantidade"] is not None and item not in de_cada]
    globais = [item for item in instrucoes if item["quantidade"] is None or item in de_cada]
    ocupados = set()
    for instrucao in locais:
        quantidade = instrucao["quantidade"][0]
        elegiveis = [i for i, item in enumerate(itens) if i not in ocupados and item["quantidade"]["valor"] == quantidade]
        if not elegiveis:
            elegiveis = [i for i in range(len(itens)) if i not in ocupados]
        if not elegiveis:
            continue
        alvo = min(elegiveis, key=lambda i: _distancia(itens[i]["_caixa"], instrucao["objeto"].caixa))
        ocupados.add(alvo)
        itens[alvo]["material"] = {
            "valor": instrucao["material"], "fonte": "texto_cdr_local", "confianca": 0.98,
            "texto_origem": instrucao["texto_origem"],
        }
        itens[alvo]["acabamento"] = {
            "valor": instrucao["acabamento"], "fonte": "texto_cdr_local", "confianca": 0.98,
        }

    ambiguas = []
    for indice, item in enumerate(itens):
        if indice in ocupados or not globais:
            continue
        instrucao = min(globais, key=lambda x: _distancia(item["_caixa"], x["objeto"].caixa))
        caixa_instrucao = instrucao["objeto"].caixa
        centros = [_centro(outro["_caixa"]) for outro in itens]
        # Texto que cobre na horizontal todas as peças vale para todas, seja cabeçalho
        # (acima de todas) ou rodapé (abaixo de todas).
        cobre_todas = bool(centros) and all(
            caixa_instrucao.esquerda <= x <= caixa_instrucao.direita for x, _ in centros
        )
        cabecalho_global = cobre_todas and (
            all(y < caixa_instrucao.topo for _, y in centros)
            or all(y > caixa_instrucao.base for _, y in centros)
        )
        explicita_global = bool(re.search(r"(?i)\b(todos?|todas?|cada)\b", instrucao["texto_origem"]))
        # Vários textos de material dizendo a mesma coisa ("ads recortados" duas vezes)
        # não deixam dúvida: valem para todas as peças sem instrução própria.
        explicita_global = explicita_global or (
            len(globais) > 1 and len({(x["material"], x["acabamento"]) for x in globais}) == 1
        )
        if len(itens) > 1 and not (explicita_global or cabecalho_global):
            # Títulos de coluna ("Papel outdor" sobre umas peças, "Adesivo" sobre
            # outra) ou rótulos embaixo ("LONA", "adesivos"): vale o texto mais
            # próximo acima ou abaixo da peça e alinhado com ela.
            caixa = item["_caixa"]

            def distancia_vertical(x) -> float:
                texto = x["objeto"].caixa
                return texto.base - caixa.topo if texto.base >= caixa.topo - 10_000 else caixa.base - texto.topo

            alinhados = [
                x for x in globais
                if (x["objeto"].caixa.base >= caixa.topo - 10_000 or x["objeto"].caixa.topo <= caixa.base + 10_000)
                and min(x["objeto"].caixa.direita, caixa.direita) > max(x["objeto"].caixa.esquerda, caixa.esquerda)
            ]
            if not alinhados:
                if instrucao not in ambiguas:
                    ambiguas.append(instrucao)
                continue
            titulo = min(alinhados, key=distancia_vertical)
            item["material"] = {
                "valor": titulo["material"], "fonte": "texto_cdr_regional", "confianca": 0.85,
                "texto_origem": titulo["texto_origem"],
            }
            item["acabamento"] = {
                "valor": titulo["acabamento"], "fonte": "texto_cdr_regional", "confianca": 0.85,
            }
            continue
        item["material"] = {
            "valor": instrucao["material"], "fonte": "texto_cdr_global", "confianca": 0.9,
            "texto_origem": instrucao["texto_origem"],
        }
        item["acabamento"] = {
            "valor": instrucao["acabamento"], "fonte": "texto_cdr_global", "confianca": 0.9,
        }

    # Peça sem rótulo próprio colada a uma peça rotulada (o adesivo redondo logo
    # acima da lateral do freezer) é do mesmo material que ela.
    def folga(a, b) -> float:
        dx = max(0, max(a.esquerda, b.esquerda) - min(a.direita, b.direita))
        dy = max(0, max(a.base, b.base) - min(a.topo, b.topo))
        return hypot(dx, dy)

    rotulados = [item for item in itens if item["material"].get("fonte") == "texto_cdr_regional"]
    for item in itens:
        if item["material"]["valor"] is not None or not rotulados:
            continue
        vizinho = min(rotulados, key=lambda outro: folga(item["_caixa"], outro["_caixa"]))
        if folga(item["_caixa"], vizinho["_caixa"]) > 10 * 100_000:
            continue
        item["material"] = {**vizinho["material"], "fonte": "peca_vizinha", "confianca": 0.7}
        item["acabamento"] = {**vizinho["acabamento"], "fonte": "peca_vizinha", "confianca": 0.7}
    if all(item["material"]["valor"] is not None for item in itens):
        return []
    return ambiguas


def _aplicar_nome_arquivo(itens: list[dict], evidencia: dict) -> None:
    """Usa o nome para preencher lacunas, nunca para sobrescrever o conteúdo do CDR."""
    material = evidencia.get("material")
    # O material do nome vale para o arquivo inteiro ("ADESIVOS CLIENTE" com 4 peças),
    # a não ser que o nome cite outro produto ("paineis e adesivo") ou que o CDR
    # seja mais específico que o nome: "adesivo" no CDR combina com "adesivo
    # brilhoso" no nome, mas "adesivo transparente" no CDR não combina com "ads".
    aplicavel = len(itens) == 1
    if material and len(itens) > 1:
        outro_produto = re.search(r"\b(?:paine(?:l|is)|placas?|ps|lonas?|banners?)\b", evidencia["texto"].casefold())
        aplicavel = not outro_produto and all(
            item["material"]["valor"] is None or material["material"].startswith(item["material"]["valor"])
            for item in itens
        )
    if material and aplicavel:
        reducao = 0.0 if len(itens) == 1 else 0.05
        for item in itens:
            if item["material"]["valor"] is None:
                item["material"] = {
                    "valor": material["material"], "fonte": "nome_arquivo", "confianca": 0.65 - reducao,
                    "texto_origem": evidencia["texto"],
                }
            if item["acabamento"]["valor"] is None and material["acabamento"] is not None:
                item["acabamento"] = {
                    "valor": material["acabamento"], "fonte": "nome_arquivo", "confianca": 0.6 - reducao,
                }

    # Quantidade no nome só é segura quando o documento contém uma única arte.
    if len(itens) == 1:
        dimensoes = evidencia.get("dimensoes")
        if dimensoes:
            atual = itens[0].get("dimensoes", {})
            esperado = (dimensoes["largura_mm"], dimensoes["altura_mm"])
            medido = (atual.get("largura_mm"), atual.get("altura_mm"))
            if medido != esperado:
                itens[0]["dimensoes_geometria"] = atual
                itens[0]["dimensoes"] = {
                    **dimensoes, "tipo": "instrucao_nome_arquivo", "fonte": "nome_arquivo", "confianca": 0.75,
                }
        quantidade = evidencia.get("quantidade")
        if quantidade and itens[0]["quantidade"]["fonte"] == "contagem_de_composicoes":
            itens[0]["quantidade"] = {
                "valor": quantidade[0], "unidade": quantidade[1],
                "texto_origem": evidencia["texto"], "fonte": "nome_arquivo", "confianca": 0.7,
            }


def _consolidar_mesmo_tamanho(itens: list[dict]) -> list[dict]:
    """Agrupa peças sem quantidade explícita quando tamanho e material coincidem."""
    grupos = defaultdict(list)
    avulsos = []
    for item in itens:
        if item["quantidade"]["fonte"] != "contagem_de_composicoes":
            avulsos.append(item)
            continue
        # Cópias da mesma arte apontam para o mesmo bitmap; artes diferentes do mesmo
        # tamanho (bitmaps diferentes) continuam como itens separados.
        assinatura = tuple(sorted(c.get("identificador_bitmap") or 0 for c in item.get("componentes") or []))
        chave = (
            round(item["dimensoes"]["largura_mm"], 1), round(item["dimensoes"]["altura_mm"], 1),
            item["material"]["valor"], item["acabamento"]["valor"], assinatura,
        )
        grupos[chave].append(item)
    resultado = avulsos[:]
    for chave, grupo in grupos.items():
        principal = grupo[0]
        principal["quantidade"]["valor"] = len(grupo)
        if len(grupo) > 1:
            principal["quantidade"]["confianca"] = 0.8
            principal["agrupamento"] = "mesmo_tamanho_e_material"
            principal["caixas_origem_mm"] = [_caixa_mm(item["_caixa"]) for item in grupo]
            if not chave[-1]:
                # Sem bitmap não dá para saber se são cópias da mesma arte.
                principal["situacao"] = "conferir artes"
        resultado.append(principal)
    return resultado


def _itens_de_instrucoes_explicitas(quantidades: list[dict]) -> list[dict]:
    """Transforma linhas com quantidade+tamanho em itens autoritativos."""
    itens = []
    for origem in (item for item in quantidades if item.get("dimensoes")):
        dimensoes = origem["dimensoes"]
        itens.append({
            "indice": len(itens) + 1,
            "quantidade": {
                "valor": origem["valor"], "unidade": origem["unidade"],
                "texto_origem": origem["texto_origem"], "fonte": "texto_cdr", "confianca": 1.0,
            },
            "dimensoes": {
                "largura_mm": dimensoes["largura_mm"], "altura_mm": dimensoes["altura_mm"],
                "tipo": "pedido_explicito", "fonte": "texto_cdr", "confianca": 1.0,
                "texto_origem": dimensoes["texto_origem"],
            },
            "componentes": [],
            "material": {"valor": None, "fonte": None, "confianca": 0.0},
            "acabamento": {"valor": None, "fonte": None, "confianca": 0.0},
            "evidencia_geometrica": "texto_com_quantidade_e_dimensoes",
            "_caixa": origem["objeto"].caixa,
        })
    return itens


def interpretar_pedido(caminho) -> dict:
    """Gera o contrato JSON auditável de um pedido em CDR."""
    caminho = Path(caminho)
    with abrir_cdr(caminho) as doc:
        metadados = doc.metadados()
        contexto = doc.contexto_cor()
        quantidades = _textos_quantidade(doc)
        instrucoes = _textos_material(doc)
        evidencias_textuais = _evidencias_textuais(doc)
        inventario_geometrico = _inventario_geometrico(doc)
        evidencia_nome = interpretar_nome_arquivo(caminho.name)
        candidatos = _candidatos_arte(doc)
        # Sobras de edição (um ponto de 5 mm ao lado de peças de metro) não são peças.
        # Miniatura com texto de quantidade ao lado ("ads 4x4 100und") é peça.
        associacoes = _associar_um_a_um(candidatos, quantidades)
        maior_area = max((c["largura_mm"] * c["altura_mm"] for c in candidatos), default=0)
        vestigios = [
            c for indice, c in enumerate(candidatos)
            if indice not in associacoes and max(c["largura_mm"], c["altura_mm"]) < 10
            and c["largura_mm"] * c["altura_mm"] < maior_area * 0.001
        ]
        if vestigios:
            candidatos = [c for c in candidatos if c not in vestigios]
            associacoes = _associar_um_a_um(candidatos, quantidades)
        instancias = [item for item in doc.instancias_bitmaps() if item.objeto is not None and item.objeto.caixa is not None]

        itens = _itens_de_instrucoes_explicitas(quantidades)
        # Uma linha contendo quantidade e tamanho é evidência direta do pedido e
        # representa a arte mais próxima dela. As demais artes desenhadas só viram
        # peças quando têm rótulo de material próprio (os "painel outdoor" ao lado de
        # "ads 4x4 100und"); sem rótulo, são o desenho do próprio item explícito.
        explicitas = [origem for origem in quantidades if origem.get("dimensoes")]
        rotulos_proprios = any(instrucao["quantidade"] is None for instrucao in instrucoes)
        representadas = set(_associar_um_a_um(candidatos, explicitas)) if itens else set()
        if not itens or (rotulos_proprios and len(representadas) < len(candidatos)):
            for indice_candidato, candidato in enumerate(candidatos):
                if indice_candidato in representadas:
                    continue
                indice_quantidade = associacoes.get(indice_candidato)
                if indice_quantidade is not None and quantidades[indice_quantidade].get("dimensoes") and itens:
                    indice_quantidade = None  # essa linha já virou item explícito
                if indice_quantidade is None:
                    quantidade = {
                        "valor": 1, "unidade": "unidade", "texto_origem": None,
                        "fonte": "contagem_de_composicoes", "confianca": 0.85,
                    }
                else:
                    origem = quantidades[indice_quantidade]
                    quantidade = {
                        "valor": origem["valor"], "unidade": origem["unidade"],
                        "texto_origem": origem["texto_origem"], "fonte": "texto_cdr", "confianca": 1.0,
                    }
                componentes_instancia = [
                    instancia for instancia in instancias
                    if _area_intersecao(candidato["caixa"], instancia.objeto.caixa) / max(1, _area(instancia.objeto.caixa)) > 0.5
                ]
                itens.append({
                    "indice": len(itens) + 1,
                    "quantidade": quantidade,
                    "dimensoes": {
                        "largura_mm": candidato["largura_mm"], "altura_mm": candidato["altura_mm"],
                        "tipo": "contorno_externo", "fonte": "geometria_cdr", "confianca": 0.9,
                    },
                    "componentes": _dimensoes_componentes(componentes_instancia),
                    "material": {"valor": None, "fonte": None, "confianca": 0.0},
                    "acabamento": {"valor": None, "fonte": None, "confianca": 0.0},
                    "evidencia_geometrica": candidato["tipo"],
                    # Caixa da peça inteira (o grupo), em cm: quem seleciona a peça no
                    # CorelDRAW precisa dela; sem isso sobra só a caixa dos bitmaps internos.
                    "caixa_cm": {chave: valor / 10 for chave, valor in _caixa_mm(candidato["caixa"]).items()},
                    "_caixa": candidato["caixa"],
                })

        materiais_ambiguos = _aplicar_materiais(itens, instrucoes)
        _aplicar_nome_arquivo(itens, evidencia_nome)
        itens = _consolidar_mesmo_tamanho(itens)
        itens.sort(key=lambda item: (item["_caixa"].esquerda, -item["_caixa"].topo))
        for indice, item in enumerate(itens, 1):
            item["indice"] = indice
            del item["_caixa"]

        alertas = []
        if vestigios:
            alertas.append({
                "codigo": "OBJETO_MINUSCULO_IGNORADO", "severidade": "atencao",
                "mensagem": f"{len(vestigios)} objeto(s) menor(es) que 1 cm ignorado(s) como sobra de edição: "
                + ", ".join(f"{c['largura_mm']:g} x {c['altura_mm']:g} mm" for c in vestigios) + ".",
            })
        if materiais_ambiguos:
            alertas.append({
                "codigo": "MATERIAL_GLOBAL_AMBIGUO", "severidade": "revisao",
                "mensagem": "Há instrução de material sem associação inequívoca; ela não foi aplicada a todos os itens.",
            })
        if contexto and contexto.modelo and contexto.modelo.casefold() == "cmyk":
            rgb = sum(c["espaco_cor"].casefold() == "rgb" for item in itens for c in item["componentes"])
            if rgb:
                alertas.append({
                    "codigo": "BITMAP_RGB_EM_DOCUMENTO_CMYK", "severidade": "atencao",
                    "mensagem": f"{rgb} bitmap(s) RGB em documento configurado como CMYK.",
                })
        baixos = sum(
            min(c["dpi_efetivo"]["x"] or 9999, c["dpi_efetivo"]["y"] or 9999) < 150
            for item in itens for c in item["componentes"]
        )
        if baixos:
            alertas.append({
                "codigo": "BITMAP_ABAIXO_150_DPI", "severidade": "atencao",
                "mensagem": f"{baixos} bitmap(s) estão abaixo de 150 DPI no tamanho aplicado.",
            })

        pendencias = []
        if any(item["material"]["valor"] is None for item in itens):
            pendencias.append("material")
        if any(item["acabamento"]["valor"] is None for item in itens):
            pendencias.append("acabamento")

        return {
            "schema_version": "0.3",
            "arquivo": {
                "nome": caminho.name, "paginas": metadados.paginas if metadados else None,
                "nome_interpretado": evidencia_nome,
                "tamanho_pagina_mm": {
                    "largura": metadados.largura_pagina_mm if metadados else None,
                    "altura": metadados.altura_pagina_mm if metadados else None,
                },
            },
            "modo_cor": {
                "documento": contexto.modelo if contexto else None,
                "intento_renderizacao": contexto.intento_renderizacao if contexto else None,
                "possui_rgb": contexto.possui_objetos_rgb if contexto else None,
                "possui_cmyk": contexto.possui_objetos_cmyk if contexto else None,
            },
            "evidencias_textuais": evidencias_textuais,
            "itens": itens,
            "total_unidades": sum(item["quantidade"]["valor"] or 0 for item in itens),
            "alertas": alertas,
            "hipoteses": {
                "inventario_geometrico": inventario_geometrico,
                "materiais_globais_ambiguos": [
                    {"material": item["material"], "acabamento": item["acabamento"], "texto_origem": item["texto_origem"]}
                    for item in materiais_ambiguos
                ],
            },
            "pendencias": pendencias,
            "limitacoes": [
                "Textos convertidos em curvas exigem a etapa visual.",
                "Agrupamentos por mesmo tamanho e material devem ser confirmados pelo operador.",
            ],
        }
