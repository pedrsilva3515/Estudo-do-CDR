"""Testes da leitura de META-INF/metadata.xml."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_AQUI = Path(__file__).resolve().parent
_RAIZ_PROJETO = _AQUI.parents[1]
sys.path.insert(0, str(_AQUI.parent))

from zcfreader import abrir_cdr  # noqa: E402
from zcfreader.metadata import FormatoMetadadosInvalido, parse_metadata  # noqa: E402

CASOS = _RAIZ_PROJETO / "casos-de-teste"


class TestMetadadosPagina(unittest.TestCase):
    def test_todos_os_casos_numerados_tem_xml_legivel(self):
        casos = sorted(CASOS.glob("caso_*.cdr"))
        self.assertGreaterEqual(len(casos), 33)
        for caminho in casos:
            with self.subTest(caso=caminho.name), abrir_cdr(caminho) as doc:
                meta = doc.metadados()
                self.assertIsNotNone(meta)
                self.assertGreaterEqual(meta.paginas, 1)
                paginas_reais = sum(
                    1
                    for nome in doc.namelist()
                    if nome.startswith("content/data/page") and nome.endswith(".dat")
                )
                self.assertEqual(meta.paginas, paginas_reais)

    def test_pagina_a4_em_milimetros(self):
        with abrir_cdr(CASOS / "caso_00_base.cdr") as doc:
            meta = doc.metadados()
        self.assertEqual(meta.paginas, 1)
        self.assertEqual(meta.layers, 1)
        self.assertEqual(meta.nome_tamanho_pagina, "A4")
        self.assertEqual(meta.largura_pagina_mm, 210.0)
        self.assertEqual(meta.altura_pagina_mm, 297.0)
        self.assertEqual(meta.orientacao, "retrato")

    def test_segunda_pagina_consta_no_resumo(self):
        with abrir_cdr(CASOS / "caso_14_segunda_pagina.cdr") as doc:
            meta = doc.metadados()
        self.assertEqual(meta.paginas, 2)


class TestMetadadosObjetos(unittest.TestCase):
    def test_contagem_do_documento_base(self):
        with abrir_cdr(CASOS / "caso_00_base.cdr") as doc:
            meta = doc.metadados()
        self.assertEqual(meta.contagem_objetos["Total"], 1)
        self.assertEqual(meta.contagem_objetos["Rect"], 1)

    def test_grupo_e_identificado(self):
        with abrir_cdr(CASOS / "caso_13_grupo.cdr") as doc:
            meta = doc.metadados()
        self.assertEqual(meta.contagem_objetos["Group"], 1)


class TestContextoCor(unittest.TestCase):
    def test_intento_de_renderizacao(self):
        with abrir_cdr(CASOS / "caso_104_contexto_cor_intento_1.cdr") as doc:
            contexto = doc.contexto_cor()
        self.assertEqual(contexto.modelo, "Cmyk")
        self.assertEqual(contexto.intento_renderizacao, "Saturation")
        self.assertTrue(contexto.possui_objetos_cmyk)
        self.assertFalse(contexto.possui_objetos_rgb)


class TestMetadadosInvalidos(unittest.TestCase):
    def test_xml_invalido_levanta_erro_especifico(self):
        with self.assertRaises(FormatoMetadadosInvalido):
            parse_metadata(b"<metadata>")


if __name__ == "__main__":
    unittest.main()
