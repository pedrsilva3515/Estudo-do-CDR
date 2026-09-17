"""Testes de conteúdo e estilos de texto."""
from __future__ import annotations

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

_AQUI = Path(__file__).resolve().parent
_RAIZ_PROJETO = _AQUI.parents[1]
sys.path.insert(0, str(_AQUI.parent))

from zcfreader import abrir_cdr  # noqa: E402

CASOS = _RAIZ_PROJETO / "casos-de-teste"


def _objeto_texto(nome: str):
    with abrir_cdr(CASOS / nome) as doc:
        return next(obj for obj in doc.estrutura() if obj.tipo_objeto == "texto")


class TestTexto(unittest.TestCase):
    def test_textinfo_em_caminho_metadata_usado_por_cdr_real(self):
        xml = b'''<?xml version="1.0"?><x:xmpmeta xmlns:x="adobe:ns:meta/"
            xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
            <rdf:RDF><rdf:Description><TextStream><TextRun lang="1046">1und</TextRun>
            </TextStream></rdf:Description></rdf:RDF></x:xmpmeta>'''
        with tempfile.TemporaryDirectory() as pasta:
            caminho = Path(pasta) / "real.cdr"
            with zipfile.ZipFile(caminho, "w") as arquivo:
                arquivo.writestr("metadata/textinfo.xml", xml)
            with abrir_cdr(caminho) as doc:
                self.assertEqual([fluxo.texto for fluxo in doc.textos()], ["1und"])

    def test_conteudo_vem_de_textinfo_xml(self):
        with abrir_cdr(CASOS / "caso_37_texto_arial_12.cdr") as doc:
            fluxos = doc.textos()
        self.assertEqual([fluxo.texto for fluxo in fluxos], ["Texto Alfa 123"])
        self.assertEqual(fluxos[0].trechos[0].idioma, 1046)
        self.assertEqual(fluxos[0].trechos[0].quebra, "para")

    def test_alteracao_de_conteudo_nao_muda_estilo(self):
        with abrir_cdr(CASOS / "caso_38_texto_conteudo_alterado.cdr") as doc:
            self.assertEqual([fluxo.texto for fluxo in doc.textos()], ["Texto Beta 456"])
            objeto = next(obj for obj in doc.estrutura() if obj.tipo_objeto == "texto")
        estilo = objeto.estilos_texto[0]
        self.assertEqual((estilo.fonte, round(estilo.tamanho_pt, 3)), ("Arial", 12.0))

    def test_tamanho_em_unidades_fisicas(self):
        doze = _objeto_texto("caso_37_texto_arial_12.cdr").estilos_texto[0]
        vinte_quatro = _objeto_texto("caso_39_texto_arial_24.cdr").estilos_texto[0]
        self.assertEqual((doze.tamanho_unidades, vinte_quatro.tamanho_unidades), (42333, 84667))
        self.assertAlmostEqual(doze.tamanho_pt, 12.0, places=3)
        self.assertAlmostEqual(vinte_quatro.tamanho_pt, 24.0, places=3)

    def test_fonte_por_objeto(self):
        objeto = _objeto_texto("caso_40_texto_times_12.cdr")
        self.assertEqual(objeto.estilos_texto[0].fonte, "Times New Roman")

    def test_texto_de_paragrafo(self):
        with abrir_cdr(CASOS / "caso_41_texto_paragrafo.cdr") as doc:
            self.assertEqual([fluxo.texto for fluxo in doc.textos()], ["Primeira linha\nSegunda linha"])
            objeto = next(obj for obj in doc.estrutura() if obj.tipo_objeto == "texto")
        self.assertEqual(objeto.codigo_tipo_objeto, 6)
        self.assertEqual(objeto.tipo_texto, "paragrafo")
        self.assertEqual([(e.fonte, round(e.tamanho_pt, 3)) for e in objeto.estilos_texto], [
            ("Arial", 12.0),
            ("Arial", 12.0),
        ])

    def test_dois_objetos_preservam_ordem_e_estilo(self):
        with abrir_cdr(CASOS / "caso_42_texto_dois_objetos.cdr") as doc:
            textos = [fluxo.texto for fluxo in doc.textos()]
            objetos = [obj for obj in doc.estrutura() if obj.tipo_objeto == "texto"]
        self.assertEqual(textos, ["Segundo objeto", "Primeiro objeto"])
        self.assertEqual(
            [(obj.estilos_texto[0].fonte, round(obj.estilos_texto[0].tamanho_pt, 3)) for obj in objetos],
            [("Times New Roman", 18.0), ("Arial", 12.0)],
        )

    def test_associa_texto_a_pagina_em_documento_multipagina(self):
        with abrir_cdr(CASOS / "caso_43_texto_duas_paginas.cdr") as doc:
            associados = doc.textos_por_objeto()
        self.assertEqual(
            [(item.fluxo.texto, item.objeto.pagina) for item in associados],
            [("Texto pagina um", 1), ("Texto pagina dois", 2)],
        )

    def test_associa_texto_dentro_de_powerclip(self):
        with abrir_cdr(CASOS / "caso_44_texto_powerclip.cdr") as doc:
            associados = doc.textos_por_objeto()
        self.assertEqual(len(associados), 1)
        self.assertEqual(associados[0].fluxo.texto, "Texto no PowerClip")
        self.assertEqual(associados[0].objeto.pagina, 1)
        self.assertEqual(associados[0].objeto.membro, "content/data/data1.dat")


if __name__ == "__main__":
    unittest.main()
