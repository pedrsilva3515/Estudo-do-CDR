"""Interpretação estrutural inicial de pedidos montados em arquivos CDR.

Esta camada só afirma o que pode ser rastreado ao contêiner ZCF. Informações
visuais convertidas em curvas exigem OCR/visão sobre o preview e permanecem
como pendência em vez de serem adivinhadas.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
import re

from .container import abrir_cdr


_QUANTIDADE = re.compile(
    r"(?ix)(?:\bq(?:td|uantidade)?\s*[:=-]?\s*)?"
    r"(?P<valor>\d+)\s*(?P<unidade>un(?:d|id(?:ade)?s?)?|u(?:n)?|x)\b"
)


def parse_quantidade(texto: str) -> tuple[int, str] | None:
    """Reconhece formas usuais como ``1und``, ``2 un`` e ``qtd: 5``."""
    match = _QUANTIDADE.search(texto.strip())
    if match is None:
        # "qtd: 5" sem sufixo de unidade.
        match_qtd = re.search(r"(?i)\bq(?:td|uantidade)?\s*[:=-]?\s*(\d+)\b", texto)
        if match_qtd is None:
            return None
        return int(match_qtd.group(1)), "unidade"
    return int(match.group("valor")), "unidade"


def _caixa_mm(caixa) -> dict[str, float]:
    return {
        "esquerda": round(caixa.esquerda / 10_000.0, 3),
        "base": round(caixa.base / 10_000.0, 3),
        "direita": round(caixa.direita / 10_000.0, 3),
        "topo": round(caixa.topo / 10_000.0, 3),
    }


def _centro_x(caixa) -> float:
    return (caixa.esquerda + caixa.direita) / 2.0


def _textos_quantidade(doc) -> list[dict]:
    associados = doc.textos_por_objeto() or ()
    encontrados = []
    vistos = set()
    for item in associados:
        caixa = item.objeto.caixa
        quantidade = parse_quantidade(item.fluxo.texto)
        if caixa is None or quantidade is None:
            continue
        # Cópias perfeitamente sobrepostas são comuns em arquivos de produção.
        chave = (
            item.fluxo.texto.strip().casefold(),
            caixa.esquerda,
            caixa.base,
            caixa.direita,
            caixa.topo,
        )
        if chave in vistos:
            continue
        vistos.add(chave)
        encontrados.append({
            "valor": quantidade[0],
            "unidade": quantidade[1],
            "texto_origem": item.fluxo.texto,
            "objeto": item.objeto,
        })
    return encontrados


def _dimensoes_componentes(instancias) -> list[dict]:
    componentes = []
    for instancia in sorted(instancias, key=lambda i: i.objeto.caixa.esquerda):
        caixa = instancia.objeto.caixa
        componentes.append({
            "largura_mm": round((caixa.direita - caixa.esquerda) / 10_000.0, 3),
            "altura_mm": round((caixa.topo - caixa.base) / 10_000.0, 3),
            "pixels": {
                "largura": instancia.registro.imagem.largura,
                "altura": instancia.registro.imagem.altura,
            },
            "dpi_efetivo": {
                "x": round(instancia.dpi_efetivo_x, 1) if instancia.dpi_efetivo_x else None,
                "y": round(instancia.dpi_efetivo_y, 1) if instancia.dpi_efetivo_y else None,
            },
            "espaco_cor": instancia.registro.imagem.espaco_de_cor,
            "caixa_mm": _caixa_mm(caixa),
        })
    return componentes


def interpretar_pedido(caminho) -> dict:
    """Gera o primeiro contrato JSON auditável de um pedido em CDR."""
    caminho = Path(caminho)
    with abrir_cdr(caminho) as doc:
        metadados = doc.metadados()
        contexto = doc.contexto_cor()
        quantidades = _textos_quantidade(doc)
        instancias = [
            item for item in doc.instancias_bitmaps()
            if item.objeto is not None and item.objeto.caixa is not None
        ]

        por_quantidade = defaultdict(list)
        sem_quantidade = []
        for instancia in instancias:
            if not quantidades:
                sem_quantidade.append(instancia)
                continue
            alvo = min(
                range(len(quantidades)),
                key=lambda indice: abs(
                    _centro_x(instancia.objeto.caixa)
                    - _centro_x(quantidades[indice]["objeto"].caixa)
                ),
            )
            por_quantidade[alvo].append(instancia)

        itens = []
        for indice, quantidade in enumerate(quantidades):
            componentes = _dimensoes_componentes(por_quantidade.get(indice, []))
            if componentes:
                esquerda = min(c["caixa_mm"]["esquerda"] for c in componentes)
                direita = max(c["caixa_mm"]["direita"] for c in componentes)
                base = min(c["caixa_mm"]["base"] for c in componentes)
                topo = max(c["caixa_mm"]["topo"] for c in componentes)
                dimensoes = {
                    "largura_mm": round(direita - esquerda, 3),
                    "altura_mm": round(topo - base, 3),
                    "tipo": "conjunto" if len(componentes) > 1 else "arte",
                    "fonte": "geometria_cdr",
                }
            else:
                dimensoes = None
            itens.append({
                "indice": indice + 1,
                "quantidade": {
                    "valor": quantidade["valor"],
                    "unidade": quantidade["unidade"],
                    "texto_origem": quantidade["texto_origem"],
                    "fonte": "texto_cdr",
                    "confianca": 1.0,
                },
                "dimensoes": dimensoes,
                "componentes": componentes,
                "material": {
                    "valor": None,
                    "fonte": None,
                    "confianca": 0.0,
                },
            })

        for instancia in sem_quantidade:
            componentes = _dimensoes_componentes([instancia])
            componente = componentes[0]
            itens.append({
                "indice": len(itens) + 1,
                "quantidade": {
                    "valor": None,
                    "unidade": "unidade",
                    "texto_origem": None,
                    "fonte": None,
                    "confianca": 0.0,
                },
                "dimensoes": {
                    "largura_mm": componente["largura_mm"],
                    "altura_mm": componente["altura_mm"],
                    "tipo": "arte",
                    "fonte": "geometria_cdr",
                },
                "componentes": componentes,
                "material": {"valor": None, "fonte": None, "confianca": 0.0},
            })

        itens.sort(key=lambda item: min(
            (c["caixa_mm"]["esquerda"] for c in item["componentes"]),
            default=float("inf"),
        ))
        for indice, item in enumerate(itens, 1):
            item["indice"] = indice

        alertas = []
        if contexto and contexto.modelo and contexto.modelo.casefold() == "cmyk":
            rgb = sum(
                componente["espaco_cor"].casefold() == "rgb"
                for item in itens for componente in item["componentes"]
            )
            if rgb:
                alertas.append({
                    "codigo": "BITMAP_RGB_EM_DOCUMENTO_CMYK",
                    "severidade": "atencao",
                    "mensagem": f"{rgb} bitmap(s) RGB em documento configurado como CMYK.",
                })
        baixos = sum(
            min(c["dpi_efetivo"]["x"] or 9999, c["dpi_efetivo"]["y"] or 9999) < 150
            for item in itens for c in item["componentes"]
        )
        if baixos:
            alertas.append({
                "codigo": "BITMAP_ABAIXO_150_DPI",
                "severidade": "atencao",
                "mensagem": f"{baixos} bitmap(s) estão abaixo de 150 DPI no tamanho aplicado.",
            })

        pendencias = []
        if any(item["material"]["valor"] is None for item in itens):
            pendencias.append("material")
        if any(item["quantidade"]["valor"] is None for item in itens):
            pendencias.append("quantidade_a_confirmar_por_visao_ou_operador")

        return {
            "schema_version": "0.1",
            "arquivo": {
                "nome": caminho.name,
                "paginas": metadados.paginas if metadados else None,
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
            "itens": itens,
            "alertas": alertas,
            "pendencias": pendencias,
            "limitacoes": [
                "Textos convertidos em curvas exigem a etapa visual/OCR do MVP.",
                "A associação entre quantidade e arte usa proximidade horizontal e deve ser confirmada na interface.",
            ],
        }
