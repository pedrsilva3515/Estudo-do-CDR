"""Testes da mesclagem conservadora de análise visual paga."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(_AQUI.parent))

from zcfreader.visao_api import incorporar_instrucoes_ocr, mesclar_analise_visual, normalizar_mapa_visual, precisa_adjudicacao  # noqa: E402


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

    def test_visao_divergente_vira_sugestao_sem_substituir_itens(self):
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
        self.assertEqual(len(resultado["itens"]), 1)
        self.assertEqual(resultado["total_unidades"], 1)
        self.assertEqual(len(resultado["sugestoes_visuais"]), 2)
        self.assertIn("SUGESTAO_VISUAL_DIVERGENTE", [a["codigo"] for a in resultado["alertas"]])

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
        # Só a linha com prova textual entra; o item proposto apenas pelo modelo vira sugestão.
        self.assertEqual([(i["quantidade"]["valor"], i["dimensoes"]["largura_mm"]) for i in resultado["itens"]], [(4, 465)])
        self.assertEqual(resultado["total_unidades"], 4)
        self.assertEqual([s["quantidade"] for s in resultado["sugestoes_visuais"]], [12])

    def test_mapa_inicial_divergente_pede_adjudicacao_mas_nao_substitui(self):
        resultado = {"itens": [{"indice": 1, "quantidade": {"valor": 1}, "dimensoes": {"largura_mm": 100, "altura_mm": 100}, "material": {"valor": None}, "acabamento": {"valor": None}}], "alertas": []}
        mapa = {
            "_fase": "mapa_visual_inicial", "estrutura_confere": "nao", "documento_misto": False,
            "instrucoes_visuais": [], "observacoes": [],
            "itens": [
                {"indice": 1, "quantidade": 2, "largura_cm": 10, "altura_cm": 10, "material": None, "acabamento": None, "evidencia": "esquerda", "confianca": .9},
                {"indice": 2, "quantidade": 3, "largura_cm": 20, "altura_cm": 20, "material": None, "acabamento": None, "evidencia": "direita", "confianca": .9},
            ],
        }
        self.assertTrue(precisa_adjudicacao(resultado, mapa))
        mesclar_analise_visual(resultado, mapa)
        self.assertEqual(len(resultado["itens"]), 1)

    def test_falha_exploratoria_forca_adjudicacao(self):
        self.assertTrue(precisa_adjudicacao({"itens": [{"indice": 1}]}, {"itens": [], "_falha_modelo": "truncado"}))

    def test_normaliza_de_cada_e_contagem_visual(self):
        mapa = {"itens": [
            {"indice": 1, "quantidade": 2, "evidencia": "30 UNI DE CADA"},
            {"indice": 2, "quantidade": 1, "evidencia": "60 UNI"},
        ]}
        normalizar_mapa_visual(mapa)
        self.assertEqual([i["quantidade"] for i in mapa["itens"]], [30, 30, 60])

    def test_ocr_orfao_entra_no_mapa_e_forca_adjudicacao(self):
        mapa = {
            "itens": [
                {"indice": 1, "quantidade": 4, "largura_cm": 37, "altura_cm": 24.5, "confianca": .9},
                {"indice": 2, "quantidade": 12, "largura_cm": 46.5, "altura_cm": 9, "confianca": .9},
            ],
            "_ocr_visual": [{"texto": "4 UN (46,5X9)", "confianca": .99}],
        }
        estrutural = {"itens": [{}, {}]}

        incorporar_instrucoes_ocr(mapa)

        self.assertEqual(len(mapa["itens"]), 3)
        self.assertEqual(mapa["itens"][2]["quantidade"], 4)
        self.assertEqual(mapa["itens"][2]["largura_cm"], 46.5)
        self.assertEqual(mapa["_instrucoes_ocr_orfas"], ["4 UN (46,5X9)"])
        self.assertTrue(precisa_adjudicacao(estrutural, mapa))

    def test_adjudicacao_recupera_item_omitido_mesmo_se_modelo_diz_estrutura_confere(self):
        resultado = {
            "itens": [
                {"indice": 1, "quantidade": {"valor": 4}, "dimensoes": {"largura_mm": 370, "altura_mm": 245}, "material": {"valor": None}, "acabamento": {"valor": None}},
                {"indice": 2, "quantidade": {"valor": 12}, "dimensoes": {"largura_mm": 465, "altura_mm": 90}, "material": {"valor": None}, "acabamento": {"valor": None}},
            ],
            "alertas": [],
        }
        visual = {
            "_fase": "adjudicacao", "estrutura_confere": "sim", "documento_misto": False,
            "instrucoes_visuais": [], "observacoes": [],
            "itens": [
                {"indice": 1, "quantidade": 4, "largura_cm": 37, "altura_cm": 24.5, "material": None, "acabamento": None, "evidencia": "4 UN (37X24,5 CM)", "confianca": .9},
                {"indice": 2, "quantidade": 12, "largura_cm": 46.5, "altura_cm": 9, "material": None, "acabamento": None, "evidencia": "12 UN (46,5X9 CM)", "confianca": .9},
            ],
            "_ocr_visual": [{"texto": "4 UN (46,5X9)", "confianca": .99}],
        }

        incorporar_instrucoes_ocr(visual)
        mesclar_analise_visual(resultado, visual, fonte="modelo_local")

        self.assertEqual(len(resultado["itens"]), 3)
        self.assertEqual(resultado["total_unidades"], 20)
        self.assertEqual(resultado["itens"][2]["dimensoes"]["altura_mm"], 90)
        self.assertIn("ITEM_RECUPERADO_DE_OCR_ORFAO", [a["codigo"] for a in resultado["alertas"]])

    def test_item_proposto_so_pelo_modelo_nao_entra_na_lista(self):
        resultado = {
            "itens": [
                {"indice": 1, "quantidade": {"valor": 4}, "dimensoes": {"largura_mm": 370, "altura_mm": 245}, "material": {"valor": None}, "acabamento": {"valor": None}},
                {"indice": 2, "quantidade": {"valor": 12}, "dimensoes": {"largura_mm": 465, "altura_mm": 90}, "material": {"valor": None}, "acabamento": {"valor": None}},
            ],
            "alertas": [],
        }
        visual = {
            "_fase": "adjudicacao", "estrutura_confere": "sim", "documento_misto": False,
            "observacoes": [],
            "itens": [
                {"indice": 1, "quantidade": 4, "largura_cm": 37, "altura_cm": 24.5, "material": None, "acabamento": None, "evidencia": "4 UN (37X24,5 CM)", "confianca": .9},
                {"indice": 2, "quantidade": 4, "largura_cm": 46.5, "altura_cm": 9, "material": None, "acabamento": None, "evidencia": "4 UN (46,5X9)", "confianca": .9},
                {"indice": 3, "quantidade": 12, "largura_cm": 46.5, "altura_cm": 9, "material": None, "acabamento": None, "evidencia": "12 UN (46,5X9 CM)", "confianca": .9},
            ],
        }

        mesclar_analise_visual(resultado, visual, fonte="modelo_local")

        self.assertEqual(len(resultado["itens"]), 2)
        self.assertEqual(resultado["total_unidades"], 16)
        self.assertEqual(len(resultado["sugestoes_visuais"]), 3)

    def test_instrucoes_auxiliares_nao_duplicam_lista_adjudicada(self):
        resultado = {
            "itens": [{"indice": 1, "quantidade": {"valor": 4}, "dimensoes": {"largura_mm": 370, "altura_mm": 245}, "material": {"valor": None}, "acabamento": {"valor": None}}],
            "alertas": [],
        }
        visual = {
            "_fase": "adjudicacao", "estrutura_confere": "nao", "observacoes": [],
            "itens": [
                {"indice": 1, "quantidade": 4, "largura_cm": 37, "altura_cm": 24.5, "material": None, "acabamento": None, "evidencia": "4 UN", "confianca": .9},
                {"indice": 2, "quantidade": 4, "largura_cm": 46.5, "altura_cm": 9, "material": None, "acabamento": None, "evidencia": "4 UN", "confianca": .9},
                {"indice": 3, "quantidade": 12, "largura_cm": 46.5, "altura_cm": 9, "material": None, "acabamento": None, "evidencia": "12 UN", "confianca": .9},
            ],
            "instrucoes_visuais": [
                {"quantidade": 10, "largura_cm": 37, "altura_cm": 24.5, "texto": "interpretação auxiliar incorreta"},
                {"quantidade": 10, "largura_cm": 90, "altura_cm": 28.7, "texto": "texto interno da arte"},
            ],
        }

        mesclar_analise_visual(resultado, visual, fonte="modelo_local")

        self.assertEqual(len(resultado["itens"]), 1)
        self.assertEqual(resultado["total_unidades"], 4)
        # A seção auxiliar não é promovida quando o modelo já produziu itens.
        self.assertEqual(len(resultado["sugestoes_visuais"]), 3)

    def test_inventario_profundo_vira_sugestao_quando_visual_nao_tem_medidas(self):
        resultado = {
            "itens": [{"indice": 1, "quantidade": {"valor": 1}, "dimensoes": {"largura_mm": 10, "altura_mm": 10}, "material": {"valor": None}, "acabamento": {"valor": None}}],
            "evidencias_textuais": [], "alertas": [],
            "hipoteses": {"inventario_geometrico": [
                {"id": "G1", "origem": "bloco_numerico", "quantidade_sugerida": 1, "largura_cm": 112.33, "altura_cm": 63.64, "posicoes_centro_cm": [{"x": 0, "y": 0}], "tipos": ["texto_artistico"]},
                {"id": "G2", "origem": "objetos_mesma_medida", "quantidade_sugerida": 2, "largura_cm": 106.25, "altura_cm": 99.98, "posicoes_centro_cm": [{"x": 200, "y": 0}, {"x": 200, "y": 110}], "tipos": ["curva"]},
            ]},
        }
        visual = {
            "_fase": "adjudicacao", "estrutura_confere": "incerto", "observacoes": [],
            "instrucoes_visuais": [],
            "itens": [{"indice": 1, "quantidade": 102304055, "largura_cm": None, "altura_cm": None, "material": None, "acabamento": None, "evidencia": "0102030405", "confianca": .98}],
        }

        mesclar_analise_visual(resultado, visual, fonte="modelo_local")

        self.assertEqual(len(resultado["itens"]), 1)
        self.assertEqual(resultado["total_unidades"], 1)
        inventario = [(s["quantidade"], s["largura_cm"]) for s in resultado["sugestoes_visuais"] if s.get("largura_cm")]
        self.assertEqual(inventario, [(1, 112.33), (2, 106.25)])


if __name__ == "__main__":
    unittest.main()
