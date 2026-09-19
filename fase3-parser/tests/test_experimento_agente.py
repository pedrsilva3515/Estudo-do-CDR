from __future__ import annotations

import unittest

from zcfreader.experimento_agente import _anotar_hierarquia, avaliar_cobertura_geometrica


def candidato(identificador, largura, altura, caixa, quantidade=1):
    return {
        "id": identificador, "origem": "objetos_mesma_medida",
        "quantidade_geometrica": quantidade, "largura_cm": largura, "altura_cm": altura,
        "caixa_cm": caixa, "posicoes_centro_cm": [], "tipos": [],
    }


class TestHierarquiaCandidatos(unittest.TestCase):
    def test_oculta_repeticao_individual_mas_expoe_produto_significativo(self):
        itens = [
            candidato("A01", 40, 20, {"esquerda": 0, "direita": 160, "base": 0, "topo": 20}, 4),
            candidato("A02", 40, 20, {"esquerda": 0, "direita": 40, "base": 0, "topo": 20}),
            candidato("A03", 30, 15, {"esquerda": 45, "direita": 75, "base": 2, "topo": 17}),
        ]

        _anotar_hierarquia(itens)

        self.assertTrue(itens[0]["visivel_inicialmente"])
        self.assertFalse(itens[1]["visivel_inicialmente"])
        self.assertTrue(itens[2]["visivel_inicialmente"])
        self.assertEqual(itens[2]["pai_id"], "A01")


class TestCoberturaGeometrica(unittest.TestCase):
    def test_quantidade_do_pedido_nao_elimina_medida_existente(self):
        itens = [
            candidato("A01", 28, 33, {"esquerda": 0, "direita": 28, "base": 0, "topo": 33}),
        ]
        esperado = {
            "itens": [{
                "quantidade": {"valor": 30},
                "dimensoes": {"largura_mm": 280, "altura_mm": 330},
            }],
        }

        resultado = avaliar_cobertura_geometrica(itens, esperado)

        self.assertEqual(resultado["itens_encontrados"], 1)
        self.assertFalse(resultado["detalhes"][0]["quantidade_geometrica_compativel"])


if __name__ == "__main__":
    unittest.main()
