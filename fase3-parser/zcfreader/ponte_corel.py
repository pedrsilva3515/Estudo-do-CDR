"""Ponte entre a macro do CorelDRAW e a análise.

A macro chama:
    python -m zcfreader.ponte_corel <arquivo.cdr> <saida.txt> <regras|ia>

e lê o resultado em texto simples (Windows-1252, separado por TAB), que o VBA
lê sem bibliotecas extras. Uma linha por registro:

    INFO      camada   duracao_s   custo_usd
    ITEM      n  quantidade  largura_cm  altura_cm  material  acabamento  esquerda  direita  base  topo  situacao  origem_material  origem_quantidade
    PERGUNTA  texto
    ERRO      mensagem

As coordenadas (cm) são as do arquivo, com origem no centro da página; a macro
converte para as do CorelDRAW. O resultado completo também é gravado em JSON ao
lado (<saida>.json), para a correção pelo Corel usar depois.

Modos:
- regras: sem IA e sem custo. Se as regras resolvem, é a resposta delas; se não,
  mostra os produtos prováveis das regras, marcados "a confirmar".
- ia: o mesmo fluxo em camadas do aplicativo (regras, depois a IA configurada).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from time import perf_counter


LADO_MINIMO_SEM_TEXTO_CM = 3.0
# Muitas peças pequenas da mesma medida desenhadas: o cliente mandou a grade montada.
# Nas revisões de 22/10/2026 eram grade 25, 30, 90 e 120 peças de 4 a 10 cm; não eram
# 6 árvores de 20 cm, 5 faixas de 90 cm nem pares de peças grandes.
GRADE_MINIMA_PECAS = 6
GRADE_PECA_MAXIMA_CM = 15.0


def _caixa_do_item(item: dict, candidatos: dict) -> dict | None:
    if item.get("caixa_cm"):
        return item["caixa_cm"]
    caixas = [candidatos[i]["caixa_cm"] for i in item.get("candidatos") or [] if i in candidatos]
    caixas += [
        {chave: valor / 10 for chave, valor in componente["caixa_mm"].items()}
        for componente in item.get("componentes") or [] if componente.get("caixa_mm")
    ]
    if not caixas:
        return None
    return {
        "esquerda": min(c["esquerda"] for c in caixas), "direita": max(c["direita"] for c in caixas),
        "base": min(c["base"] for c in caixas), "topo": max(c["topo"] for c in caixas),
    }


def separar_ocorrencias(resultado: dict, candidatos: dict, auditoria: dict | None = None) -> dict:
    """Ajusta itens cuja peça tem várias ocorrências desenhadas da mesma medida.

    - Artes diferentes (bitmaps diferentes) com quantidade igual ao número de
      ocorrências: um item de 1 unidade por arte, cada um com a sua caixa.
    - Cópias da mesma arte: a caixa passa a ser a de uma ocorrência, para exportar
      uma peça com a quantidade, e não todas juntas.
    - "N de cada" com K peças desenhadas (quantidade N × K): K itens de N unidades,
      seja qual for a arte, porque "de cada" já diz que cada peça é um produto.
    - Sem como saber (arte só em vetor) ou quantidade diferente: marca para conferir.
    - Muitas peças pequenas desenhadas (``GRADE_MINIMA_PECAS`` ou mais, de até
      ``GRADE_PECA_MAXIMA_CM``): o cliente mandou a grade
      montada, e o que vai para a produção é 1 grade com o tamanho do conjunto.
    """
    from copy import deepcopy
    from .agente import _quantidade_de_cada
    from .experimento_agente import caixas_das_ocorrencias

    # Quantidade por peça das instruções "N DE CADA" ligadas a cada candidata.
    por_ocorrencia = {}
    for regra in (auditoria or {}).get("itens") or []:
        for evidencia in regra.get("evidencias") or []:
            por_peca = _quantidade_de_cada(evidencia.get("texto"))
            if por_peca:
                por_ocorrencia.setdefault(regra["candidato_id"], por_peca)

    itens = []
    for item in resultado.get("itens") or []:
        ids = item.get("candidatos") or []
        candidato = candidatos.get(ids[0]) if len(ids) == 1 else None
        caixas = caixas_das_ocorrencias(candidato) if candidato else []
        if len(caixas) <= 1:
            itens.append(item)
            continue
        artes = candidato.get("artes")
        quantidade = (item.get("quantidade") or {}).get("valor") or 0
        por_peca = por_ocorrencia.get(ids[0])
        pequena = max(candidato["largura_cm"], candidato["altura_cm"]) <= GRADE_PECA_MAXIMA_CM
        if len(caixas) >= GRADE_MINIMA_PECAS and pequena and not por_peca:
            grade = {
                "esquerda": min(c["esquerda"] for c in caixas), "direita": max(c["direita"] for c in caixas),
                "base": min(c["base"] for c in caixas), "topo": max(c["topo"] for c in caixas),
            }
            item["quantidade"] = {"valor": 1}
            item["dimensoes"] = {"largura_mm": round((grade["direita"] - grade["esquerda"]) * 10, 1),
                                 "altura_mm": round((grade["topo"] - grade["base"]) * 10, 1)}
            item["caixa_cm"] = grade
            item["grade"] = {"pecas": len(caixas), "peca_cm": [candidato["largura_cm"], candidato["altura_cm"]]}
            item["situacao"] = f"grade de {len(caixas)} - confirmar"
            itens.append(item)
            continue
        if por_peca and por_peca * len(caixas) == quantidade:
            # "N de cada" com K peças desenhadas: K itens de N unidades, cada um com a sua caixa.
            for caixa in caixas:
                novo = deepcopy(item)
                novo["quantidade"] = {**(novo.get("quantidade") or {}), "valor": por_peca}
                novo["caixa_cm"] = caixa
                novo["situacao"] = (novo.get("situacao") or "").replace(" - conferir artes", "")
                itens.append(novo)
            continue
        if artes == "distintas" and quantidade == len(caixas):
            for caixa in caixas:
                novo = deepcopy(item)
                novo["quantidade"] = {**(novo.get("quantidade") or {}), "valor": 1}
                novo["caixa_cm"] = caixa
                itens.append(novo)
            continue
        if artes == "iguais":
            item["caixa_cm"] = caixas[0]
        else:
            situacao = item.get("situacao") or ""
            item["situacao"] = f"{situacao} - conferir artes" if situacao else "conferir artes"
        itens.append(item)
    itens = _sem_repetir_grade(itens, candidatos)
    for indice, item in enumerate(itens, 1):
        item["indice"] = indice
    resultado["itens"] = itens
    return resultado


# Faca de recorte em volta da arte: curva que envolve a peça com uma margem pequena
# (a borda branca). No pedido "PARA NATAL" as margens iam de 0,1 a 1,2 cm.
FACA_MARGEM_MAXIMA_CM = 3.0


def _faca_em_volta(caixa: dict, candidatos: dict, ignorar: set[str]) -> str | None:
    melhor = None
    for candidato_id, c in candidatos.items():
        if candidato_id in ignorar or set(c.get("tipos") or []) != {"curva"} or not c.get("caixa_cm"):
            continue
        faca = c["caixa_cm"]
        margens = (caixa["esquerda"] - faca["esquerda"], faca["direita"] - caixa["direita"],
                   caixa["base"] - faca["base"], faca["topo"] - caixa["topo"])
        if all(-0.05 <= m <= FACA_MARGEM_MAXIMA_CM for m in margens) and max(margens) > 0.2:
            # A mais justa: uma moldura maior em volta da faca não é a faca.
            if melhor is None or sum(margens) < melhor[0]:
                melhor = (sum(margens), candidato_id)
    return melhor[1] if melhor else None


def aplicar_medida_da_faca(resultado: dict, candidatos: dict) -> dict:
    """Peça com faca em volta: a medida do item é a da faca, que inclui a borda branca.

    O acabamento não muda: a faca não quer dizer que a gráfica recorta (o cliente
    pode recortar em casa); o recorte só entra quando está escrito.
    """
    itens = resultado.get("itens") or []
    usados = {i for item in itens for i in item.get("candidatos") or []}
    facas_listadas = set()
    for item in itens:
        caixa = _caixa_do_item(item, candidatos)
        if not caixa:
            continue
        faca_id = _faca_em_volta(caixa, candidatos, set(item.get("candidatos") or []))
        if not faca_id:
            continue
        faca = candidatos[faca_id]
        dimensoes = item.get("dimensoes") or {}
        item["faca"] = {"candidato": faca_id, "arte_cm": [round((dimensoes.get("largura_mm") or 0) / 10, 2),
                                                           round((dimensoes.get("altura_mm") or 0) / 10, 2)]}
        item["dimensoes"] = {**dimensoes, "largura_mm": round(faca["largura_cm"] * 10, 1),
                             "altura_mm": round(faca["altura_cm"] * 10, 1), "tipo": "faca_de_recorte"}
        item["caixa_cm"] = dict(faca["caixa_cm"])
        if faca_id in usados:
            facas_listadas.add(faca_id)
    # A faca que as regras listaram como peça "sem texto" deixa de ser um item a mais.
    resultado["itens"] = [
        item for item in itens
        if "faca" in item or len(item.get("candidatos") or []) != 1 or item["candidatos"][0] not in facas_listadas
    ]
    for indice, item in enumerate(resultado["itens"], 1):
        item["indice"] = indice
    return resultado


def finalizar_resultado(resultado: dict, fatos: dict) -> dict:
    """Ajustes depois das regras ou da IA, iguais na macro e na régua."""
    candidatos = fatos.get("candidatos") or {}
    separar_ocorrencias(resultado, candidatos, fatos.get("auditoria_regional"))
    aplicar_medida_da_faca(resultado, candidatos)
    return aplicar_catalogo(resultado)


def _sem_repetir_grade(itens: list[dict], candidatos: dict) -> list[dict]:
    """Tira os itens que ocupam a mesma caixa de uma grade já listada.

    A grade costuma vir em mais de uma camada (impressão e corte) e às vezes com o
    contorno da folha desenhado: tudo isso é a mesma grade, não itens a mais.
    """
    def mesma_caixa(a: dict | None, b: dict) -> bool:
        return bool(a) and all(abs(a[lado] - b[lado]) <= 0.5 for lado in ("esquerda", "direita", "base", "topo"))

    grades = [_caixa_do_item(item, candidatos) for item in itens if item.get("grade")]
    restantes, vistas = [], []
    for item in itens:
        caixa = _caixa_do_item(item, candidatos)
        if item.get("grade"):
            if any(mesma_caixa(caixa, g) for g in vistas):
                continue
            vistas.append(caixa)
        elif any(mesma_caixa(caixa, g) for g in grades):
            continue
        restantes.append(item)
    return restantes


def _material_do_nome_arquivo(caminho: Path | None, itens: list[dict]) -> None:
    """Preenche material e acabamento vazios pelo nome do arquivo, como faz o leitor estrutural."""
    from .pedido import interpretar_nome_arquivo, _aplicar_nome_arquivo

    if caminho is None or not itens:
        return
    evidencia = interpretar_nome_arquivo(caminho.name)
    # Só material e acabamento: medida e quantidade continuam vindo do desenho.
    _aplicar_nome_arquivo(itens, {"texto": evidencia["texto"], "material": evidencia["material"]})


def _material_do_cabecalho(itens: list[dict], fatos: dict) -> None:
    """Peça sem material herda o do título de material mais próximo acima dela, na mesma coluna.

    O cliente escreve "VINIL FOSCO" ou "Paineis outdoor" uma vez em cima de várias fileiras
    de peças; as regras só ligam o título à primeira fileira. Títulos com medida
    ("BANNER 90X60") falam de uma peça só e não valem para a coluna.
    """
    from .agente import _quantidade_de_cada
    from .experimento_agente import _dimensoes_instrucao_material, _especificacao_material

    candidatos = fatos.get("candidatos") or {}
    titulos = []
    for texto in (fatos.get("textos") or {}).values():
        especificacao = _especificacao_material(texto.get("texto") or "")
        if especificacao and texto.get("caixa_cm") and not _dimensoes_instrucao_material(texto["texto"], especificacao):
            titulos.append((texto["caixa_cm"], especificacao, texto["texto"]))
    for item in itens:
        if (item.get("material") or {}).get("valor"):
            continue
        caixa = _caixa_do_item(item, candidatos)
        if not caixa:
            continue
        centro_x = (caixa["esquerda"] + caixa["direita"]) / 2
        acima, de_cada = [], []
        for titulo, especificacao, texto in titulos:
            margem = max(2.0, (titulo["direita"] - titulo["esquerda"]) * 0.15)
            if titulo["esquerda"] - margem <= centro_x <= titulo["direita"] + margem and titulo["base"] >= caixa["topo"] - 0.5:
                acima.append((titulo["base"] - caixa["topo"], especificacao))
            # "paineis outdoor 1und de cada" embaixo de vários painéis vale para todos os que ele toca.
            if _quantidade_de_cada(texto) and titulo["esquerda"] < caixa["direita"] and caixa["esquerda"] < titulo["direita"]:
                distancia = titulo["base"] - caixa["topo"] if titulo["base"] >= caixa["topo"] else caixa["base"] - titulo["topo"]
                if distancia >= -0.5:
                    de_cada.append((distancia, especificacao))
        if not (acima or de_cada):
            continue
        especificacao = min(acima or de_cada, key=lambda par: par[0])[1]
        item["material"] = {"valor": especificacao["material"], "origem": "titulo_da_coluna"}
        if especificacao.get("acabamento") and not (item.get("acabamento") or {}).get("valor"):
            item["acabamento"] = {"valor": especificacao["acabamento"]}


def _parece_instrucao(texto: str) -> bool:
    """Texto que fala do pedido (material, quantidade ou medida), e não da arte."""
    import re

    from .agente import _quantidade_de_cada
    from .experimento_agente import _especificacao_material
    from .pedido import parse_quantidade

    return bool(_especificacao_material(texto) or parse_quantidade(texto) or _quantidade_de_cada(texto)
                or re.search(r"(?i)\d\s*(?:cm|mm|m)\b|\d\s*[x×]\s*\d", texto))


def _area_intersecao(a: dict, b: dict) -> float:
    largura = min(a["direita"], b["direita"]) - max(a["esquerda"], b["esquerda"])
    altura = min(a["topo"], b["topo"]) - max(a["base"], b["base"])
    return largura * altura if largura > 0 and altura > 0 else 0.0


def _medida_confere(texto: str, largura_cm: float, altura_cm: float) -> bool | None:
    """A medida escrita no texto é a da peça? None se o texto não tem medida."""
    from .pedido import parse_dimensoes

    dimensoes = parse_dimensoes(texto)
    if not dimensoes or not dimensoes.get("largura_mm") or not dimensoes.get("altura_mm"):
        return None
    w, h = dimensoes["largura_mm"] / 10, dimensoes["altura_mm"] / 10
    return any(
        abs(a - w) <= max(1.5, 0.03 * w) and abs(b - h) <= max(1.5, 0.03 * h)
        for a, b in ((largura_cm, altura_cm), (altura_cm, largura_cm))
    )


def _quantidade_escrita(itens: list[dict], fatos: dict) -> None:
    """Liga às peças as quantidades escritas que as regras não ligaram.

    - Um texto com quantidade junto de cada cópia ("5 UN (67X102 CM)" em cima de cada
      placa, "30und" embaixo de cada adesivo): o pedido é a soma. Cada texto pertence à
      cópia mais próxima (acima, abaixo ou ao lado). Com duas ou mais cópias, a soma vale
      mesmo se as regras já tinham ligado um dos textos à peça inteira.

    As demais só mexem em item cuja quantidade não veio de um texto (veio do desenho ou
    do padrão 1):
    - Texto com quantidade e a medida da peça ("35x25 10 unidades"): vale para ela.
    - "N de cada" como única quantidade do arquivo: N por peça desenhada.
    - Um único texto com quantidade e uma única peça: é dela.
    """
    from .agente import _quantidade_de_cada
    from .experimento_agente import caixas_das_ocorrencias
    from .pedido import parse_quantidade

    candidatos = fatos.get("candidatos") or {}
    textos = []
    for texto in (fatos.get("textos") or {}).values():
        quantidade = parse_quantidade(texto.get("texto") or "")
        por_peca = _quantidade_de_cada(texto.get("texto"))
        if (quantidade or por_peca) and texto.get("caixa_cm"):
            textos.append({**texto, "quantidade": por_peca or quantidade[0], "de_cada": por_peca})
    if not textos:
        return
    de_cada = {t["de_cada"] for t in textos if t["de_cada"]}

    def junto(texto: dict, caixa: dict) -> float | None:
        """Distância do texto logo acima, abaixo ou ao lado da caixa."""
        t = texto["caixa_cm"]
        centro_x, centro_y = (t["esquerda"] + t["direita"]) / 2, (t["base"] + t["topo"]) / 2
        if caixa["esquerda"] - 0.5 <= centro_x <= caixa["direita"] + 0.5:
            limite = max(3.0, 0.3 * (caixa["topo"] - caixa["base"]))
            for distancia in (t["base"] - caixa["topo"], caixa["base"] - t["topo"]):
                if -0.5 <= distancia <= limite:
                    return max(distancia, 0.0)
        if caixa["base"] - 0.5 <= centro_y <= caixa["topo"] + 0.5:
            limite = max(3.0, 0.3 * (caixa["direita"] - caixa["esquerda"]))
            for distancia in (caixa["esquerda"] - t["direita"], t["esquerda"] - caixa["direita"]):
                if -0.5 <= distancia <= limite:
                    return max(distancia, 0.0)
        return None

    # Cada texto de quantidade fica com a cópia mais próxima, entre todas as peças.
    copias = []
    for indice, item in enumerate(itens):
        ids = item.get("candidatos") or []
        candidato = candidatos.get(ids[0]) if len(ids) == 1 else None
        if candidato:
            for caixa in caixas_das_ocorrencias(candidato) or [candidato["caixa_cm"]]:
                copias.append((indice, caixa, candidato["largura_cm"], candidato["altura_cm"]))
    rotulos: dict[tuple[int, int], list[tuple[float, dict]]] = {}
    for texto in textos:
        if texto["de_cada"]:
            continue
        distancias = [
            (d, numero) for numero, (_, caixa, largura, altura) in enumerate(copias)
            if _medida_confere(texto["texto"], largura, altura) is not False and (d := junto(texto, caixa)) is not None
        ]
        if not distancias:
            continue
        menor = min(d for d, _ in distancias)
        empatadas = {copias[numero][0] for d, numero in distancias if d - menor <= 0.2}
        if len(empatadas) == 1:
            numero = min(distancias, key=lambda par: par[0])[1]
            rotulos.setdefault((copias[numero][0], numero), []).append((menor, texto))

    for indice, item in enumerate(itens):
        numeros = [numero for numero, copia in enumerate(copias) if copia[0] == indice]
        if not numeros:
            continue
        novo = None
        por_copia = []
        for numero in numeros:
            proprios = rotulos.get((indice, numero)) or []
            if not proprios:
                break
            menor = min(d for d, _ in proprios)
            # Dois textos no mesmo lugar com quantidades diferentes (um escondido atrás do outro): não dá para saber.
            if len({t["quantidade"] for d, t in proprios if d - menor <= 0.2}) > 1:
                break
            por_copia.append(min(proprios, key=lambda par: par[0])[1])
        quantidade = item.get("quantidade") or {}
        sem_texto = quantidade.get("origem") == "desenho" or (
            quantidade.get("origem") is None and (item.get("origem_campos") or {}).get("quantidade") == "padrao_grafica")
        if len(por_copia) == len(numeros) and (len(numeros) >= 2 or sem_texto):
            novo = sum(t["quantidade"] for t in por_copia)
        if not sem_texto and novo is None:
            continue
        ids = item.get("candidatos") or []
        candidato = candidatos[ids[0]]
        largura, altura = candidato["largura_cm"], candidato["altura_cm"]
        ocorrencias = numeros
        if novo is None:
            com_medida = [t for t in textos if _medida_confere(t["texto"], largura, altura)]
            if len(com_medida) == 1:
                novo = com_medida[0]["quantidade"] * (len(ocorrencias) if com_medida[0]["de_cada"] else 1)
        # Só quando é a única quantidade escrita: com outras, o "de cada" é de uma parte do pedido.
        if novo is None and len(de_cada) == 1 and all(t["de_cada"] for t in textos):
            novo = next(iter(de_cada)) * len(ocorrencias)
        if novo is None and len(textos) == 1 and len(itens) == 1 and not textos[0]["de_cada"]:
            novo = textos[0]["quantidade"]
        if novo:
            item["quantidade"] = {"valor": int(novo), "origem": "texto"}
            (item.get("origem_campos") or {}).pop("quantidade", None)


def _analisar_regras(caminho: Path, fatos: dict) -> dict:
    from .camadas import regras_resolvem, resultado_das_regras

    auditoria = fatos["auditoria_regional"]
    if regras_resolvem(auditoria):
        resultado = resultado_das_regras(auditoria)
        for item in resultado["itens"]:
            item["situacao"] = "regras"
        _quantidade_escrita(resultado["itens"], fatos)
        _material_do_nome_arquivo(caminho, resultado["itens"])
        return {"itens": resultado["itens"], "perguntas_operador": [], "processamento": {"fluxo": "macro_corel", "camada_final": "regras"}}
    itens = []
    for regra in auditoria.get("itens") or []:
        produto = regra.get("papel") in {"produto_confirmado", "produto_plausivel"}
        # Peças que o programa enxerga mas sem texto que as explique. Nas correções pela
        # macro, adicionar peça dá muito mais trabalho que remover; simulação nos 68
        # pedidos revisados: faltando 31 -> 8 linhas, com ~44 a mais para remover.
        sem_texto = (regra.get("papel") == "sem_classificacao"
                     and min(regra["largura_cm"], regra["altura_cm"]) >= LADO_MINIMO_SEM_TEXTO_CM)
        if not (produto or sem_texto):
            continue
        itens.append({
            "indice": len(itens) + 1,
            "quantidade": {"valor": int(regra.get("quantidade_pedido") or regra.get("quantidade_desenhada") or 1),
                           "origem": "texto" if regra.get("quantidade_pedido") else "desenho"},
            "dimensoes": {"largura_mm": regra["largura_cm"] * 10, "altura_mm": regra["altura_cm"] * 10},
            "material": {"valor": regra.get("material")},
            "acabamento": {"valor": regra.get("acabamento")},
            "candidatos": [regra["candidato_id"]],
            "situacao": "a confirmar" if produto else "sem texto - confirmar",
        })
    # Peça sem texto que está dentro de outra peça da lista é parte dela (ex.: o bitmap
    # dentro do grupo com fundo), não um item a mais.
    candidatos = fatos.get("candidatos") or {}
    listados = {item["candidatos"][0] for item in itens}

    from .experimento_agente import caixas_das_ocorrencias

    def dentro_de_ocorrencia(caixa: dict, pai: dict) -> bool:
        # A caixa de uma peça repetida cobre todas as cópias e o espaço entre elas:
        # só conta como "dentro" o que cabe numa das ocorrências.
        ocorrencias = caixas_das_ocorrencias(pai) or [pai["caixa_cm"]]
        return any(
            o["esquerda"] - 0.3 <= caixa["esquerda"] and caixa["direita"] <= o["direita"] + 0.3
            and o["base"] - 0.3 <= caixa["base"] and caixa["topo"] <= o["topo"] + 0.3
            for o in ocorrencias
        )

    def dentro_de_listado(candidato_id: str) -> bool:
        vistos = set()
        caixa = (candidatos.get(candidato_id) or {}).get("caixa_cm")
        pai = (candidatos.get(candidato_id) or {}).get("pai_id")
        while caixa and pai and pai not in vistos:
            if pai in listados and dentro_de_ocorrencia(caixa, candidatos[pai]):
                return True
            vistos.add(pai)
            pai = (candidatos.get(pai) or {}).get("pai_id")
        return False

    def emendas_de_outra_peca(candidato_id: str) -> bool:
        # Painel de papel outdoor dividido em folhas: as cópias juntas ocupam a mesma
        # caixa de uma peça já listada, sem ser filhas dela no arquivo.
        candidato = candidatos.get(candidato_id) or {}
        if int(candidato.get("quantidade_geometrica") or 1) < 2 or not candidato.get("caixa_cm"):
            return False
        caixa = candidato["caixa_cm"]
        return any(
            outro != candidato_id and int((candidatos.get(outro) or {}).get("quantidade_geometrica") or 1) == 1
            and all(abs(caixa[lado] - candidatos[outro]["caixa_cm"][lado]) <= 0.5
                    for lado in ("esquerda", "direita", "base", "topo"))
            for outro in listados if (candidatos.get(outro) or {}).get("caixa_cm")
        )

    def copia_de_outra_peca(candidato_id: str) -> bool:
        # A mesma peça em outra camada ou só o miolo dela (o fundo de 50x50 dentro da placa
        # de 51x51, a curva de corte sobre o bitmap): cada cópia cabe numa cópia de outra
        # peça listada quase do mesmo tamanho.
        candidato = candidatos.get(candidato_id) or {}
        if not (candidato.get("caixa_cm") and candidato.get("largura_cm")):
            return False
        for outro in listados:
            pai = candidatos.get(outro) or {}
            if outro == candidato_id or not (pai.get("caixa_cm") and pai.get("largura_cm")):
                continue
            # Das duas camadas, fica a maior (e, do mesmo tamanho, a primeira).
            area, area_pai = candidato["largura_cm"] * candidato["altura_cm"], pai["largura_cm"] * pai["altura_cm"]
            if area > area_pai or (area == area_pai and candidato_id < outro):
                continue
            if not (0.85 * pai["largura_cm"] <= candidato["largura_cm"] <= pai["largura_cm"] + 0.3
                    and 0.85 * pai["altura_cm"] <= candidato["altura_cm"] <= pai["altura_cm"] + 0.3):
                continue
            if all(dentro_de_ocorrencia(caixa, pai) for caixa in caixas_das_ocorrencias(candidato) or [candidato["caixa_cm"]]):
                return True
        return False

    instrucoes = [t["caixa_cm"] for t in (fatos.get("textos") or {}).values()
                  if t.get("caixa_cm") and _parece_instrucao(t.get("texto") or "")]

    def instrucao_em_curvas(candidato_id: str) -> bool:
        # "VINIL BLACKOUT 65cm x 1,03m" escrito em curvas: o OCR lê o texto em cima da peça.
        candidato = candidatos.get(candidato_id) or {}
        if not candidato.get("caixa_cm") or "bitmap" in (candidato.get("tipos") or []):
            return False
        for caixa in caixas_das_ocorrencias(candidato) if candidato.get("largura_cm") else [candidato["caixa_cm"]]:
            area = (caixa["direita"] - caixa["esquerda"]) * (caixa["topo"] - caixa["base"])
            if area <= 0 or sum(_area_intersecao(caixa, t) for t in instrucoes) / area < 0.5:
                return False
        return True

    produtos = [item["candidatos"][0] for item in itens if item["situacao"] != "sem texto - confirmar"]

    def sobre_peca_com_texto(candidato_id: str) -> bool:
        # Moldura, fundo ou grupo em volta de uma peça que tem texto (a placa de 105,6x106,8
        # dentro do retângulo de 105,6x140,5): a peça é a que o texto explica.
        candidato = candidatos.get(candidato_id) or {}
        caixa = candidato.get("caixa_cm")
        if not caixa:
            return False
        area = (caixa["direita"] - caixa["esquerda"]) * (caixa["topo"] - caixa["base"])
        if area <= 0:
            return False
        # Só quando as peças com texto ocupam a maior parte dela: a lona de 70x100 com o
        # texto ligado a um bitmap de 33x30 dentro continua sendo a peça.
        coberta = 0.0
        for outro in produtos:
            pai = candidatos.get(outro) or {}
            # Peça com texto que é parte do grupo dela (o bitmap dentro do adesivo de 50x30):
            # o grupo é a peça, e não uma moldura em volta, a não ser que o grupo junte a
            # peça e a instrução escrita (peça + legenda).
            if pai.get("pai_id") == candidato_id and not any(
                    _area_intersecao(caixa, t) >= 0.8 * (t["direita"] - t["esquerda"]) * (t["topo"] - t["base"])
                    for t in instrucoes):
                continue
            for ocorrencia in (caixas_das_ocorrencias(pai) if pai.get("largura_cm") else []) or [pai.get("caixa_cm")]:
                if ocorrencia:
                    coberta += _area_intersecao(caixa, ocorrencia)
        return coberta >= 0.5 * area

    itens = [
        item for item in itens
        if item["situacao"] != "sem texto - confirmar"
        or not (dentro_de_listado(item["candidatos"][0]) or emendas_de_outra_peca(item["candidatos"][0])
                or copia_de_outra_peca(item["candidatos"][0]) or instrucao_em_curvas(item["candidatos"][0])
                or sobre_peca_com_texto(item["candidatos"][0]))
    ]
    for indice, item in enumerate(itens, 1):
        item["indice"] = indice
    _quantidade_escrita(itens, fatos)
    _material_do_cabecalho(itens, fatos)
    _material_do_nome_arquivo(caminho, itens)
    for item in itens:
        # Nada escrito sobre o material: vale o adesivo, o padrão da casa (aparece "(padrão)").
        if not (item.get("material") or {}).get("valor"):
            item["material"] = {"valor": "adesivo"}
    return {"itens": itens, "perguntas_operador": [], "processamento": {"fluxo": "macro_corel", "camada_final": "regras (a confirmar)"}}


def _analisar_ia(caminho: Path, fatos: dict) -> dict:
    from .camadas import interpretar_em_camadas
    from .configuracao import carregar_configuracao, obter_chave
    from .pedido import interpretar_pedido

    configuracao = carregar_configuracao()
    return interpretar_em_camadas(
        caminho, obter_chave("openrouter"), interpretar_pedido(caminho), fatos=fatos,
        modelo_rapido=configuracao["modelo_rapido"], modelo_forte=configuracao["modelo_forte"],
        custo_maximo_usd=configuracao["limite_pedido_usd"], url_servidor_local=configuracao["url_servidor_local"],
    )


def aplicar_catalogo(resultado: dict) -> dict:
    """Troca material e acabamento pelos nomes do Portal Flow, guardando o texto lido.

    O material que vem só do padrão da gráfica (o pedido dizia apenas "adesivo")
    fica marcado em ``origem_campos`` para aparecer como "(padrão)" na macro.
    """
    from .catalogo_portal import acabamentos_portal, material_portal

    for item in resultado.get("itens") or []:
        material = (item.get("material") or {}).get("valor")
        acabamento = (item.get("acabamento") or {}).get("valor")
        nome, origem = material_portal(material, acabamento)
        if nome:
            item["material"] = {**(item.get("material") or {}), "valor": nome, "texto_lido": material}
            if origem == "padrao_grafica":
                item["origem_campos"] = {**(item.get("origem_campos") or {}), "material": "padrao_grafica"}
        acabamentos = acabamentos_portal(material, acabamento)
        if acabamentos:
            item["acabamento"] = {**(item.get("acabamento") or {}), "valor": " + ".join(acabamentos),
                                  "texto_lido": acabamento}
    return resultado


def _campo(valor) -> str:
    texto = "" if valor is None else str(valor)
    return " ".join(texto.replace("\t", " ").split())


def _numero(valor) -> str:
    return f"{float(valor):.3f}"


def linhas_de_saida(resultado: dict, candidatos: dict, duracao_s: float) -> list[str]:
    processamento = resultado.get("processamento") or {}
    linhas = ["\t".join(["INFO", _campo(processamento.get("camada_final")), f"{duracao_s:.1f}",
                         f"{float(processamento.get('custo_usd') or 0):.4f}"])]
    for n, item in enumerate(resultado.get("itens") or [], 1):
        dimensoes = item.get("dimensoes") or {}
        caixa = _caixa_do_item(item, candidatos)
        coordenadas = [_numero(caixa[c]) for c in ("esquerda", "direita", "base", "topo")] if caixa else ["", "", "", ""]
        linhas.append("\t".join([
            "ITEM", str(n), _campo((item.get("quantidade") or {}).get("valor")),
            _numero((dimensoes.get("largura_mm") or 0) / 10), _numero((dimensoes.get("altura_mm") or 0) / 10),
            _campo((item.get("material") or {}).get("valor")), _campo((item.get("acabamento") or {}).get("valor")),
            *coordenadas, _campo(item.get("situacao") or ""),
            _campo((item.get("origem_campos") or {}).get("material") or "arquivo"),
            _campo((item.get("origem_campos") or {}).get("quantidade") or "arquivo"),
        ]))
    for pergunta in resultado.get("perguntas_operador") or []:
        linhas.append("\t".join(["PERGUNTA", _campo(pergunta.get("pergunta") if isinstance(pergunta, dict) else pergunta)]))
    return linhas


_ORIGENS_VALIDAS = {"arquivo", "padrao_grafica", "faltou_no_pedido"}


def _numero_ou_none(texto: str) -> float | None:
    try:
        return float(texto.replace(",", "."))
    except (AttributeError, ValueError):
        return None


def resultado_corrigido(original: dict, linhas: list[str]) -> tuple[dict, str]:
    """Monta o resultado correto a partir do arquivo de correção escrito pela macro.

    Linhas (TAB):
        OBS   texto
        ITEM  n_original  quantidade  largura_cm  altura_cm  material  acabamento
              origem_quantidade  origem_material  origem_acabamento  peca  esquerda  direita  base  topo
              motivo  objetos
    ``n_original`` 0 = item novo; ``peca`` "corel" = peça escolhida selecionando no CorelDRAW.
    """
    from copy import deepcopy

    from .origem_campos import definir_origens

    originais = original.get("itens") or []
    itens, observacao = [], ""
    for linha in linhas:
        campos = linha.rstrip("\r\n").split("\t")
        if campos[0] == "OBS" and len(campos) > 1:
            observacao = campos[1].strip()
        if campos[0] != "ITEM" or len(campos) < 17:
            continue
        indice_original = int(campos[1] or 0)
        base = deepcopy(originais[indice_original - 1]) if 0 < indice_original <= len(originais) else {}
        item = base
        quantidade = int(float(campos[2] or 0) or 1)
        largura, altura = _numero_ou_none(campos[3]) or 0.0, _numero_ou_none(campos[4]) or 0.0
        antes_dim = base.get("dimensoes") or {}

        if (base.get("quantidade") or {}).get("valor") != quantidade:
            item["quantidade"] = {"valor": quantidade, "unidade": "unidade", "fonte": "correcao_operador", "confianca": 1.0}
        for campo, valor in (("material", campos[5]), ("acabamento", campos[6])):
            valor = valor.strip() or None
            if (base.get(campo) or {}).get("valor") != valor:
                item[campo] = {"valor": valor, "fonte": "correcao_operador", "confianca": 1.0}

        if campos[10] == "corel" or not antes_dim:
            item["dimensoes"] = {
                "largura_mm": round(largura * 10, 3), "altura_mm": round(altura * 10, 3),
                "tipo": "peca_indicada_pelo_operador", "fonte": "correcao_operador", "confianca": 1.0,
            }
        caixa = [_numero_ou_none(c) for c in campos[11:15]]
        if all(v is not None for v in caixa):
            item["caixa_cm"] = dict(zip(("esquerda", "direita", "base", "topo"), caixa))
        if campos[10] == "corel":
            item["peca_correta"] = {
                "origem": "selecao_corel", "largura_cm": largura, "altura_cm": altura,
                "objetos_corel": [o for o in campos[16].split(";") if o],
            }
            if base:
                item["peca_correta"]["antes"] = {
                    "ids": list(base.get("candidatos") or []),
                    "largura_cm": round((antes_dim.get("largura_mm") or 0) / 10, 3),
                    "altura_cm": round((antes_dim.get("altura_mm") or 0) / 10, 3),
                }
        if campos[15].strip():
            item["observacao_operador"] = campos[15].strip()
        origens = {
            campo: codigo for campo, codigo in zip(("quantidade", "material", "acabamento"), campos[7:10])
            if codigo in _ORIGENS_VALIDAS
        }
        itens.append(definir_origens(item, origens))
    correto = {k: v for k, v in original.items() if k != "itens"}
    correto["itens"] = itens
    return correto, observacao


def salvar_correcao(caminho: Path, arquivo_correcao: Path) -> Path:
    from .configuracao import carregar_configuracao
    from .relatorios import classificar_diferencas, gerar_pacote_diagnostico

    linhas = arquivo_correcao.read_text(encoding="cp1252").splitlines()
    original_json = next((l.split("\t", 1)[1] for l in linhas if l.startswith("ORIGINAL\t")), None)
    if not original_json or not Path(original_json).exists():
        raise FileNotFoundError("Resultado da análise não encontrado; analise o arquivo de novo antes de salvar.")
    dados = json.loads(Path(original_json).read_text(encoding="utf-8"))
    if Path(dados["arquivo"]).resolve() != Path(caminho).resolve():
        raise ValueError("A análise guardada é de outro arquivo; analise este arquivo de novo antes de salvar.")
    original = dados["resultado"]
    correto, observacao = resultado_corrigido(original, linhas)
    situacao = "corrigido" if classificar_diferencas(original, correto) else "confirmado"
    configuracao = carregar_configuracao()
    return gerar_pacote_diagnostico(
        Path(caminho), original, correto, situacao=situacao, observacao_operador=observacao,
        incluir_cdr=bool(configuracao.get("incluir_cdr_diagnostico", True)),
    )


def main(argumentos: list[str]) -> int:
    caminho, saida, modo = Path(argumentos[0]), Path(argumentos[1]), (argumentos[2] if len(argumentos) > 2 else "regras")
    if modo == "salvar":
        # Aqui "saida" é o arquivo de correção escrito pela macro; a resposta vai para <correcao>.ok
        try:
            linhas = ["\t".join(["OK", str(salvar_correcao(caminho, saida))])]
        except Exception as erro:
            linhas = ["\t".join(["ERRO", _campo(f"{type(erro).__name__}: {erro}")])]
        Path(str(saida) + ".ok").write_text("\r\n".join(linhas) + "\r\n", encoding="cp1252", errors="replace", newline="")
        return 0
    inicio = perf_counter()
    try:
        # O CorelDRAW aberto nunca é usado pela análise: o desenho vem do próprio arquivo.
        import zcfreader.visao_api as visao_api
        visao_api.renderizar_com_corel = lambda *a, **k: None
        from .agente import extrair_fatos

        fatos = extrair_fatos(caminho)
        resultado = _analisar_ia(caminho, fatos) if modo == "ia" else _analisar_regras(caminho, fatos)
        finalizar_resultado(resultado, fatos)
        linhas = linhas_de_saida(resultado, fatos.get("candidatos") or {}, perf_counter() - inicio)
        Path(str(saida) + ".json").write_text(
            json.dumps({"arquivo": str(caminho), "modo": modo, "resultado": resultado}, ensure_ascii=False,
                       indent=2, default=str),
            encoding="utf-8",
        )
    except Exception as erro:  # a macro mostra a mensagem ao operador
        linhas = ["\t".join(["ERRO", _campo(f"{type(erro).__name__}: {erro}")])]
    saida.write_text("\r\n".join(linhas) + "\r\n", encoding="cp1252", errors="replace", newline="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
