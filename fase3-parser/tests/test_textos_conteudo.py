"""Associação texto -> objeto pelo conteúdo gravado após o objeto."""
from __future__ import annotations

import struct
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

_AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(_AQUI.parent))

from zcfreader.container import ZcfContainer  # noqa: E402
from zcfreader.text import FluxoTexto, TrechoTexto  # noqa: E402


def _bloco(texto: str) -> bytes:
    codificado = texto.encode("cp1252")
    return b"\x00" * 32 + struct.pack("<I", len(codificado)) + codificado + b"\x00" * 16


class TestTextosPorConteudo(unittest.TestCase):
    def test_textos_em_powerclip_nao_trocam_com_os_da_pagina(self):
        # dataN.dat (conteúdo de PowerClip) vem primeiro na estrutura, mas o
        # textinfo.xml lista primeiro os textos da página.
        dados = {"content/data/data1.dat": _bloco("COLÉGIO E CURSOS") + _bloco("MUNDI"),
                 "content/data/page1.dat": _bloco("VINIL BRILHOSO") + _bloco("1 UNI DE CADA")}
        tamanho = len(_bloco("COLÉGIO E CURSOS"))
        objetos = [
            SimpleNamespace(tipo="obj", tipo_objeto="texto", membro="content/data/data1.dat", offset_dados=0),
            SimpleNamespace(tipo="obj", tipo_objeto="texto", membro="content/data/data1.dat", offset_dados=tamanho),
            SimpleNamespace(tipo="obj", tipo_objeto="texto", membro="content/data/page1.dat", offset_dados=0),
            SimpleNamespace(tipo="obj", tipo_objeto="texto", membro="content/data/page1.dat", offset_dados=len(_bloco("VINIL BRILHOSO"))),
        ]
        fluxos = tuple(FluxoTexto((TrechoTexto(texto=t, idioma=None, quebra="para"),))
                       for t in ("VINIL BRILHOSO", "1 UNI DE CADA", "COLÉGIO E CURSOS", "MUNDI"))
        doc = object.__new__(ZcfContainer)
        doc.estrutura = lambda: objetos
        doc.textos = lambda: fluxos
        doc.read = lambda membro: dados[membro]
        associacao = [(t.objeto.membro.split("/")[-1], t.fluxo.texto) for t in doc.textos_por_objeto()]
        self.assertEqual(associacao, [
            ("data1.dat", "COLÉGIO E CURSOS"), ("data1.dat", "MUNDI"),
            ("page1.dat", "VINIL BRILHOSO"), ("page1.dat", "1 UNI DE CADA"),
        ])


if __name__ == "__main__":
    unittest.main()
