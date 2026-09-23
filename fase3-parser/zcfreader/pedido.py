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
    r"(?P<valor>\d+)\s*(?P<unidade>uni|un(?:d|id(?:ade)?s?)?|u(?:n)?|x)\b"
)


def parse_quantidade(texto: str) -> tuple[int, str] | None:
    """Reconhece formas usuais como ``1und``, ``2 un`` e ``qtd: 5``."""
    match = _QUANTIDADE.search(texto.strip())
    if match is None:
        match_qtd = re.search(r"(?i)\bq(?:td|uantidade)?\s*[:=-]?\s*(\d+)\b", texto)
        if match_qtd is None:
            return None
        return int(match_qtd.group(1)), "unidade"
    return int(match.group("valor")), "unidade"


def parse_material(texto: str) -> dict | None:
    """Extrai material e acabamento de instruções usuais da gráfica."""
    normalizado = " ".join(texto.casefold().split())
    adesivo = "adesivo" in normalizado or "vinil" in normalizado
    banner = "banner" in normalizado or "lona" in normalizado
    if adesivo and banner:
        return None  # documento misto: a associação precisa ser regional
    if not adesivo and not banner:
        return None
    if banner:
        material = "lona" if "lona" in normalizado else "banner"
    elif "transparente" in normalizado or "trasnparente" in normalizado:
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
    if "somente recorte" in normalizado:
        acabamento = "somente recorte"
    elif "recorte especial" in normalizado or "com recorte" in normalizado:
        acabamento = "recorte especial"
    elif re.search(r"\bsem\s+rec(?:orte|ortad[oa]s?|\.)?\b", normalizado):
        acabamento = "sem recorte"
    elif re.search(r"\brecortad[oa]s?\b", normalizado):
        acabamento = "recortado"
    else:
        acabamento = None
    return {"material": material, "acabamento": acabamento}


def parse_dimensoes(texto: str) -> dict | None:
    """Reconhece dimensões; sem unidade somente quando há contexto de quantidade."""
    sem_acentos = "".join(
        caractere for caractere in unicodedata.normalize("NFKD", texto.casefold())
        if not unicodedata.combining(caractere)
    )
    dimensao = re.search(
        r"(?<!\d)(\d+(?:[.,]\d+)?)\s*[x×]\s*(\d+(?:[.,]\d+)?)\s*(mm|cm|m)?\b",
        sem_acentos,
    )
    if dimensao is None:
        return None
    unidade = dimensao.group(3)
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
        "altura_mm": float(dimensao.group(2).replace(",", ".")) * fator,
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
    material = parse_material(sem_acentos)
    quantidade = parse_quantidade(sem_acentos)
    dimensoes = parse_dimensoes(sem_acentos)
    if dimensoes is None:
        sem_unidade = re.search(r"(?<!\d)(\d+[.,]\d+)\s*[x×]\s*(\d+[.,]\d+)(?!\d)", sem_acentos)
        if sem_unidade:
            a, b = (float(valor.replace(",", ".")) for valor in sem_unidade.groups())
            # Nomes como 1,00x0,55 em gráficas normalmente expressam metros.
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


def _candidatos_arte(doc) -> list[dict]:
    """Seleciona caixas externas prováveis, evitando objetos internos duplicados."""
    estrutura = _estrutura_visivel(doc)
    tipos_limite = {"bitmap", "retangulo", "curva", "desconhecido"}
    limites = [
        objeto for objeto in estrutura
        if objeto.tipo == "obj" and not objeto.ancestrais and objeto.caixa is not None
        and objeto.tipo_objeto in tipos_limite
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

    grupos = [
        objeto for objeto in estrutura
        if objeto.tipo == "grp" and not objeto.ancestrais and objeto.caixa is not None
    ]
    for grupo in grupos:
        area_grupo = _area(grupo.caixa)
        if area_grupo <= 0:
            continue
        sobreposto = any(
            _area_intersecao(grupo.caixa, limite.caixa) / min(area_grupo, _area(limite.caixa)) > 0.25
            for limite in externos if _area(limite.caixa) > 0
        )
        if not sobreposto:
            externos.append(grupo)

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
            "caixa_mm": _caixa_mm(caixa),
        })
    return componentes


def _aplicar_materiais(itens: list[dict], instrucoes: list[dict]) -> list[dict]:
    locais = [item for item in instrucoes if item["quantidade"] is not None]
    globais = [item for item in instrucoes if item["quantidade"] is None]
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
        cabecalho_global = bool(centros) and all(
            caixa_instrucao.esquerda <= x <= caixa_instrucao.direita and y < caixa_instrucao.topo
            for x, y in centros
        )
        explicita_global = bool(re.search(r"(?i)\b(todos?|todas?)\b", instrucao["texto_origem"]))
        if len(itens) > 1 and not (explicita_global or cabecalho_global):
            if instrucao not in ambiguas:
                ambiguas.append(instrucao)
            continue
        item["material"] = {
            "valor": instrucao["material"], "fonte": "texto_cdr_global", "confianca": 0.9,
            "texto_origem": instrucao["texto_origem"],
        }
        item["acabamento"] = {
            "valor": instrucao["acabamento"], "fonte": "texto_cdr_global", "confianca": 0.9,
        }
    return ambiguas


def _aplicar_nome_arquivo(itens: list[dict], evidencia: dict) -> None:
    """Usa o nome para preencher lacunas, nunca para sobrescrever o conteúdo do CDR."""
    material = evidencia.get("material")
    if material and len(itens) == 1:
        for item in itens:
            if item["material"]["valor"] is None:
                item["material"] = {
                    "valor": material["material"], "fonte": "nome_arquivo", "confianca": 0.65,
                    "texto_origem": evidencia["texto"],
                }
            if item["acabamento"]["valor"] is None and material["acabamento"] is not None:
                item["acabamento"] = {
                    "valor": material["acabamento"], "fonte": "nome_arquivo", "confianca": 0.6,
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
        chave = (
            round(item["dimensoes"]["largura_mm"], 1), round(item["dimensoes"]["altura_mm"], 1),
            item["material"]["valor"], item["acabamento"]["valor"],
        )
        grupos[chave].append(item)
    resultado = avulsos[:]
    for grupo in grupos.values():
        principal = grupo[0]
        principal["quantidade"]["valor"] = len(grupo)
        if len(grupo) > 1:
            principal["quantidade"]["confianca"] = 0.8
            principal["agrupamento"] = "mesmo_tamanho_e_material"
            principal["caixas_origem_mm"] = [_caixa_mm(item["_caixa"]) for item in grupo]
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
        associacoes = _associar_um_a_um(candidatos, quantidades)
        instancias = [item for item in doc.instancias_bitmaps() if item.objeto is not None and item.objeto.caixa is not None]

        itens = _itens_de_instrucoes_explicitas(quantidades)
        # Uma linha contendo quantidade e tamanho é evidência direta do pedido.
        # Curvas externas podem ser apenas partes internas da mesma arte.
        if not itens:
            for indice_candidato, candidato in enumerate(candidatos):
                indice_quantidade = associacoes.get(indice_candidato)
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
