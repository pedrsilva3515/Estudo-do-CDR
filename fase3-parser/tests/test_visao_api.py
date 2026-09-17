"""Testes da mesclagem conservadora de análise visual paga."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(_AQUI.parent))

from zcfreader.visao_api import mesclar_analise_visual  # noqa: E402


class TestMesclagemVisual(unittest.TestCase):
    def test_api_preenche_lacuna_sem_apagar_geometria(self):
        resultado = {
            "itens": [{
                "indice": 1,
                "quantidade": {"valor": 2, "fonte": "texto_cdr"},
                "dimensoes": {"largura_mm": 300, "altura_mm": 400},
                "material": {"valor": None},
                "acabamento": {"valor": None},
            }],
            "alertas": [],
            "pendencias": ["material", "acabamento"],
        }
        visual = {"itens": [{
            "indice": 1, "quantidade": 2, "material": "adesivo leitoso",
            "acabamento": "recortado", "observacao": None, "confianca": 0.91,
        }], "observacoes": []}
        mesclar_analise_visual(resultado, visual)
        self.assertEqual(resultado["itens"][0]["material"]["fonte"], "visao_api")
        self.assertEqual(resultado["itens"][0]["dimensoes"]["largura_mm"], 300)
        self.assertEqual(resultado["pendencias"], [])

    def test_divergencia_vira_alerta_e_nao_sobrescreve(self):
        resultado = {
            "itens": [{
                "indice": 1,
                "quantidade": {"valor": 6, "fonte": "texto_cdr"},
                "material": {"valor": "adesivo normal"},
                "acabamento": {"valor": None},
            }],
            "alertas": [], "pendencias": ["acabamento"],
        }
        visual = {"itens": [{
            "indice": 1, "quantidade": 8, "material": "adesivo transparente",
            "acabamento": None, "observacao": None, "confianca": 0.7,
        }], "observacoes": []}
        mesclar_analise_visual(resultado, visual)
        self.assertEqual(resultado["itens"][0]["quantidade"]["valor"], 6)
        self.assertEqual(resultado["itens"][0]["material"]["valor"], "adesivo normal")
        self.assertEqual(len(resultado["alertas"]), 2)


if __name__ == "__main__":
    unittest.main()
