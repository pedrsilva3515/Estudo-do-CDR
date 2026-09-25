"""Testes da comparação das provas de regressão com a referência."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from zcfreader.provas import comparar_com_referencia  # noqa: E402


def _medidas(**mudancas) -> dict:
    base = {
        "regras_pedido_correto": 1, "regras_linhas_corretas": 2, "regras_a_mais": 0, "regras_faltando": 0,
        "regras_material_ok": 2, "regras_acabamento_ok": 1, "regras_decidem_errado": 0, "itens_com_peca": 2,
    }
    return {**base, **mudancas}


class TestComparacao(unittest.TestCase):
    def test_igual_nao_tem_diferenca(self):
        diferencas = comparar_com_referencia({"a.cdr": _medidas()}, {"a.cdr": _medidas()})
        self.assertFalse(any(diferencas.values()))

    def test_menor_e_pior_ou_melhor_conforme_a_metrica(self):
        diferencas = comparar_com_referencia(
            {"a.cdr": _medidas(), "b.cdr": _medidas()},
            {"a.cdr": _medidas(regras_linhas_corretas=1), "b.cdr": _medidas(regras_a_mais=0, regras_faltando=0,
                                                                            itens_com_peca=3)},
        )
        self.assertEqual(list(diferencas["piorou"]), ["a.cdr"])
        self.assertEqual(list(diferencas["melhorou"]), ["b.cdr"])

    def test_regras_decidirem_errado_e_piora(self):
        diferencas = comparar_com_referencia({"a.cdr": _medidas()}, {"a.cdr": _medidas(regras_decidem_errado=1)})
        self.assertIn("a.cdr", diferencas["piorou"])

    def test_passar_a_dar_erro_e_piora(self):
        diferencas = comparar_com_referencia({"a.cdr": _medidas()}, {"a.cdr": {"erro": "ValueError: x"}})
        self.assertIn("a.cdr", diferencas["piorou"])

    def test_pedido_novo_e_pedido_sumido(self):
        diferencas = comparar_com_referencia({"a.cdr": _medidas()}, {"b.cdr": _medidas()})
        self.assertEqual(diferencas["novos"], ["b.cdr"])
        self.assertEqual(diferencas["sumiram"], ["a.cdr"])


if __name__ == "__main__":
    unittest.main()
