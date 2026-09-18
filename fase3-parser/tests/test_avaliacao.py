import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zcfreader.avaliacao import comparar_resultados  # noqa: E402


def resultado(itens):
    return {"itens": itens, "total_unidades": sum(i["quantidade"]["valor"] for i in itens)}


def item(qtd, largura, altura, material="adesivo"):
    return {"quantidade": {"valor": qtd}, "dimensoes": {"largura_mm": largura, "altura_mm": altura}, "material": {"valor": material}, "acabamento": {"valor": None}}


class TestAvaliacao(unittest.TestCase):
    def test_comparacao_independe_da_ordem(self):
        a = resultado([item(30, 280, 330), item(60, 200, 250)])
        b = resultado([item(60, 200, 250), item(30, 280, 330)])
        self.assertTrue(comparar_resultados(a, b)["exato"])

    def test_detecta_total_e_dimensao_errados(self):
        metricas = comparar_resultados(resultado([item(1, 620, 160)]), resultado([item(60, 200, 250)]))
        self.assertFalse(metricas["exato"])
        self.assertFalse(metricas["total_unidades_correto"])
        self.assertEqual(metricas["acuracia_campos"]["dimensoes"], 0)


if __name__ == "__main__":
    unittest.main()
