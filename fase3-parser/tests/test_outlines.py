"""Testes das propriedades de contorno por objeto."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_AQUI = Path(__file__).resolve().parent
_RAIZ_PROJETO = _AQUI.parents[1]
sys.path.insert(0, str(_AQUI.parent))

from zcfreader import abrir_cdr  # noqa: E402

CASOS = _RAIZ_PROJETO / "casos-de-teste"


def _contorno(nome: str):
    with abrir_cdr(CASOS / nome) as doc:
        return next(o.contorno for o in doc.estrutura() if o.tipo == "obj")


class TestContornos(unittest.TestCase):
    def test_larguras_em_milimetros(self):
        casos = {
            "caso_49_contorno_padrao_02mm.cdr": (2000, 0.2),
            "caso_52_contorno_05mm.cdr": (5000, 0.5),
            "caso_53_contorno_10mm.cdr": (10000, 1.0),
        }
        for nome, esperado in casos.items():
            with self.subTest(nome=nome):
                contorno = _contorno(nome)
                self.assertEqual((contorno.largura_unidades, contorno.largura_mm), esperado)
                self.assertTrue(contorno.presente)

    def test_largura_zero_equivale_a_sem_contorno(self):
        for nome in ("caso_50_sem_contorno.cdr", "caso_51_contorno_largura_zero.cdr"):
            with self.subTest(nome=nome):
                contorno = _contorno(nome)
                self.assertEqual(contorno.largura_unidades, 0)
                self.assertFalse(contorno.presente)

    def test_linha_fina_nativa(self):
        contorno = _contorno("caso_61_contorno_linha_fina.cdr")
        self.assertEqual(contorno.largura_unidades, 762)
        self.assertAlmostEqual(contorno.largura_mm, 0.0762)
        self.assertTrue(contorno.linha_fina)
        self.assertTrue(contorno.presente)

        self.assertFalse(_contorno("caso_49_contorno_padrao_02mm.cdr").linha_fina)

    def test_tracejado(self):
        self.assertEqual(_contorno("caso_55_contorno_tracejado.cdr").tracejado, (2.0, 1.0, 3.0))

    def test_escala_com_objeto(self):
        self.assertTrue(_contorno("caso_54_contorno_escala_objeto.cdr").escala_com_objeto)

    def test_pontas_e_juncao(self):
        contorno = _contorno("caso_56_contorno_caps_join_1.cdr")
        self.assertEqual((contorno.pontas, contorno.juncao), (1, 1))
        self.assertEqual((contorno.pontas_nome, contorno.juncao_nome),
                         ("arredondada", "arredondada"))

    def test_pontas_quadradas_e_juncao_chanfrada(self):
        contorno = _contorno("caso_59_contorno_caps_join_2.cdr")
        self.assertEqual((contorno.pontas_nome, contorno.juncao_nome),
                         ("quadrada", "chanfrada"))

    def test_alinhamento_interno_e_externo(self):
        interno = _contorno("caso_57_contorno_alinhamento_interno.cdr")
        externo = _contorno("caso_58_contorno_alinhamento_externo.cdr")
        self.assertEqual((interno.alinhamento, interno.alinhamento_nome), (1, "interno"))
        self.assertEqual((externo.alinhamento, externo.alinhamento_nome), (2, "externo"))

    def test_setas_sao_geometrias_serializadas(self):
        contorno = _contorno("caso_60_contorno_setas.cdr")
        self.assertTrue(contorno.seta_inicial.startswith("M"))
        self.assertTrue(contorno.seta_final.startswith("M"))
        self.assertNotEqual(contorno.seta_inicial, contorno.seta_final)


if __name__ == "__main__":
    unittest.main()
