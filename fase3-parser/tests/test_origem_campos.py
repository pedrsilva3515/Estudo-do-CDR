"""Testes da origem das informações corrigidas (arquivo, padrão da gráfica, faltou no pedido)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(_AQUI.parent))

from zcfreader.avaliacao_caminhos import comparar_tolerante  # noqa: E402
from zcfreader.origem_campos import campos_com_origem, definir_origens, marca, origem  # noqa: E402
from zcfreader.relatorios import _resumo_texto  # noqa: E402


def _item(qtd, material, origens=None, acabamento=None):
    item = {
        "quantidade": {"valor": qtd}, "dimensoes": {"largura_mm": 400, "altura_mm": 400},
        "material": {"valor": material}, "acabamento": {"valor": acabamento},
    }
    return definir_origens(item, origens or {})


class TestOrigemCampos(unittest.TestCase):
    def test_padrao_e_arquivo_e_so_especiais_sao_gravados(self):
        item = _item(15, "adesivo", {"material": "faltou_no_pedido", "quantidade": "arquivo"})
        self.assertEqual(item["origem_campos"], {"material": "faltou_no_pedido"})
        self.assertEqual(origem(item, "quantidade"), "arquivo")
        self.assertEqual(campos_com_origem(item, "faltou_no_pedido"), ["material"])
        self.assertEqual(marca(item, "material"), " (faltou)")
        self.assertNotIn("origem_campos", definir_origens(item, {"material": "arquivo"}))

    def test_avaliador_nao_cobra_adivinhacao_quando_faltou_no_pedido(self):
        esperado = {"itens": [_item(15, "adesivo", {"material": "faltou_no_pedido"})]}
        vazio = comparar_tolerante({"itens": [_item(15, None)]}, esperado)
        self.assertTrue(vazio["pedido_correto"])
        self.assertEqual((vazio["faltas_esperadas"], vazio["faltas_detectadas"], vazio["chutes"]), (1, 1, 0))
        chute = comparar_tolerante({"itens": [_item(15, "lona")]}, esperado)
        self.assertTrue(chute["pedido_correto"])  # material não é cobrado...
        self.assertEqual(chute["chutes"], 1)       # ...mas o chute é registrado
        perguntou = comparar_tolerante({"itens": [_item(15, "lona")], "perguntas": [{"pergunta": "Qual material?"}]}, esperado)
        self.assertEqual(perguntou["faltas_detectadas"], 1)

    def test_padrao_da_grafica_continua_sendo_cobrado(self):
        esperado = {"itens": [_item(15, "adesivo branco", {"material": "padrao_grafica"})]}
        self.assertFalse(comparar_tolerante({"itens": [_item(15, "lona")]}, esperado)["pedido_correto"])
        self.assertTrue(comparar_tolerante({"itens": [_item(15, "adesivo branco")]}, esperado)["pedido_correto"])

    def test_resumo_do_relatorio_mostra_as_origens(self):
        correto = {"itens": [dict(_item(15, None, {"material": "faltou_no_pedido", "acabamento": "padrao_grafica"},
                                        acabamento="recortado"), indice=1)]}
        diagnostico = {"caso_id": "x", "arquivo": {"nome": "a.cdr"}, "situacao": "corrigido",
                       "versao_aplicacao": "0.9", "categorias": []}
        texto = _resumo_texto({"itens": []}, correto, diagnostico)
        self.assertIn("Faltou no pedido (perguntar ao cliente): material", texto)
        self.assertIn("Padrão da gráfica: acabamento", texto)


if __name__ == "__main__":
    unittest.main()
