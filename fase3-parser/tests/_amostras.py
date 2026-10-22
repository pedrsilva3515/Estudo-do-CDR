"""Pedidos reais usados como prova local.

Os arquivos são de clientes da gráfica e o repositório é público: os caminhos
ficam em ``amostras_locais.json`` (fora do git), um por chave. Sem a lista ou
sem o arquivo, o teste é pulado.
"""
from __future__ import annotations

import json
import unittest
from pathlib import Path

LISTA = Path(__file__).with_name("amostras_locais.json")


def amostra(chave: str) -> Path | None:
    try:
        caminhos = json.loads(LISTA.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    caminho = caminhos.get(chave)
    return Path(caminho) if caminho and Path(caminho).is_file() else None


def com_amostra(chave: str):
    return unittest.skipUnless(amostra(chave), f"amostra local ausente: {chave}")
