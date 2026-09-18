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

    def test_visao_pode_reconstruir_lista_completa(self):
        resultado = {
            "itens": [{
                "indice": 1, "quantidade": {"valor": 1},
                "dimensoes": {"largura_mm": 100, "altura_mm": 100},
                "material": {"valor": None}, "acabamento": {"valor": None},
            }], "alertas": [], "pendencias": [],
        }
        visual = {
            "estrutura_confere": "nao", "documento_misto": False, "observacoes": [],
            "itens": [
                {"indice": 1, "quantidade": 4, "largura_cm": 37, "altura_cm": 24.5, "material": "adesivo", "acabamento": None, "evidencia": "4 UN", "confianca": .9},
                {"indice": 2, "quantidade": 12, "largura_cm": 46.5, "altura_cm": 9, "material": "adesivo", "acabamento": None, "evidencia": "12 UN", "confianca": .9},
            ],
        }
        mesclar_analise_visual(resultado, visual, fonte="modelo_local")
        self.assertEqual(len(resultado["itens"]), 2)
        self.assertEqual(resultado["total_unidades"], 16)
        self.assertEqual(resultado["itens"][1]["dimensoes"]["largura_mm"], 465)
        self.assertIn("itens_estruturais_descartados", resultado)

    def test_proposta_incompleta_nao_substitui_estrutura(self):
        resultado = {"itens": [{"indice": 1, "quantidade": {"valor": 1}, "dimensoes": {"largura_mm": 10, "altura_mm": 20}, "material": {"valor": None}, "acabamento": {"valor": None}}], "alertas": []}
        visual = {"estrutura_confere": "nao", "documento_misto": False, "observacoes": [], "itens": [{"indice": 1, "quantidade": 9, "largura_cm": None, "altura_cm": None, "material": "adesivo", "acabamento": None, "evidencia": None, "confianca": .9}]}
        mesclar_analise_visual(resultado, visual)
        self.assertEqual(resultado["itens"][0]["quantidade"]["valor"], 1)

    def test_ocr_adiciona_instrucao_omitida_pelo_modelo(self):
        resultado = {"itens": [], "alertas": []}
        visual = {
            "estrutura_confere": "nao", "documento_misto": False,
            "instrucoes_visuais": [], "observacoes": [],
            "itens": [{"indice": 1, "quantidade": 12, "largura_cm": 46.5, "altura_cm": 9, "material": None, "acabamento": None, "evidencia": "12 UN", "confianca": .9}],
            "_ocr_visual": [{"texto": "4 UN (46,5X9)", "confianca": .99, "poligono_px": []}],
        }
        mesclar_analise_visual(resultado, visual, fonte="modelo_local")
        self.assertEqual([(i["quantidade"]["valor"], i["dimensoes"]["largura_mm"]) for i in resultado["itens"]], [(12, 465), (4, 465)])
        self.assertEqual(resultado["total_unidades"], 16)


if __name__ == "__main__":
    unittest.main()
