"""Formato de texto que a macro do CorelDRAW lê."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from zcfreader.ponte_corel import linhas_de_saida  # noqa: E402


class TestLinhasDeSaida(unittest.TestCase):
    def test_item_com_caixa_do_candidato(self):
        resultado = {
            "processamento": {"camada_final": "regras", "custo_usd": 0},
            "itens": [{
                "quantidade": {"valor": 6}, "dimensoes": {"largura_mm": 400, "altura_mm": 300},
                "material": {"valor": "adesivo\tfosco"}, "acabamento": {"valor": None}, "candidatos": ["A05"],
            }],
            "perguntas_operador": [{"pergunta": "Qual o acabamento?"}],
        }
        candidatos = {"A05": {"caixa_cm": {"esquerda": -47.1, "direita": -7.1, "base": -20.2, "topo": 9.8}}}
        linhas = linhas_de_saida(resultado, candidatos, 4.25)
        self.assertEqual(linhas[0], "INFO\tregras\t4.2\t0.0000")
        campos = linhas[1].split("\t")
        self.assertEqual(len(campos), 12)
        self.assertEqual(campos[:7], ["ITEM", "1", "6", "40.000", "30.000", "adesivo fosco", ""])
        self.assertEqual(campos[7:11], ["-47.100", "-7.100", "-20.200", "9.800"])
        self.assertEqual(linhas[2], "PERGUNTA\tQual o acabamento?")

    def test_item_sem_posicao_tem_coordenadas_vazias(self):
        resultado = {"itens": [{"quantidade": {"valor": 1}, "dimensoes": {"largura_mm": 100, "altura_mm": 100}}]}
        campos = linhas_de_saida(resultado, {}, 1)[1].split("\t")
        self.assertEqual(campos[7:11], ["", "", "", ""])


if __name__ == "__main__":
    unittest.main()
