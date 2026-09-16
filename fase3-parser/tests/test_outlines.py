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

    def test_tracejado(self):
        self.assertEqual(_contorno("caso_55_contorno_tracejado.cdr").tracejado, (2.0, 1.0, 3.0))

    def test_escala_com_objeto(self):
        self.assertTrue(_contorno("caso_54_contorno_escala_objeto.cdr").escala_com_objeto)

    def test_pontas_e_juncao(self):
        contorno = _contorno("caso_56_contorno_caps_join_1.cdr")
        self.assertEqual((contorno.pontas, contorno.juncao), (1, 1))


if __name__ == "__main__":
    unittest.main()
