from __future__ import annotations

import unittest

from zcfreader.experimento_agente import (
    _anotar_hierarquia,
    avaliar_cobertura_geometrica,
    detectar_blocos_producao,
)


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


class TestBlocoProducaoDerivado(unittest.TestCase):
    def test_une_objetos_abaixo_da_instrucao_sem_incluir_moldura(self):
        moldura = candidato(
            "A01", 75.4, 167.32,
            {"esquerda": 292.76, "direita": 368.17, "base": -72.06, "topo": 95.27},
        )
        evidencias = [
            {
                "texto": "ADESIVOS BRANCO RECORTADOS", "caixa_mm": {
                    "esquerda": 3039.343, "direita": 3563.755, "base": 655.127, "topo": 876.28,
                },
                "material": {"material": "adesivo", "acabamento": "recortado"}, "dimensoes": None,
            },
            {
                "texto": "DO MESMO TAMANHO", "caixa_mm": {
                    "esquerda": 3103.868, "direita": 3492.164, "base": 578.064, "topo": 605.121,
                },
                "material": None, "dimensoes": None,
            },
            {
                "texto": "CAIXA", "caixa_mm": {
                    "esquerda": 3074.097, "direita": 3524.097, "base": 310.519, "topo": 390.519,
                },
                "material": None, "dimensoes": None,
            },
            {
                "texto": "REAL FARMA", "caixa_mm": {
                    "esquerda": 3082.705, "direita": 3542.705, "base": 55.041, "topo": 105.041,
                },
                "material": None, "dimensoes": None,
            },
            {
                "texto": "84 98631-8973", "caixa_mm": {
                    "esquerda": 3108.076, "direita": 3511.979, "base": -630.553, "topo": -580.544,
                },
                "material": None, "dimensoes": None,
            },
            {
                "texto": "FRALDAS", "caixa_mm": {
                    "esquerda": 3086.202, "direita": 3546.202, "base": -441.161, "topo": -391.161,
                },
                "material": None, "dimensoes": None,
            },
        ]

        blocos = detectar_blocos_producao([moldura], evidencias)

        self.assertEqual(len(blocos), 1)
        self.assertEqual(blocos[0]["largura_cm"], 47.21)
        self.assertEqual(blocos[0]["altura_cm"], 102.107)
        self.assertEqual(blocos[0]["material_sugerido"], "adesivo branco")
        self.assertNotIn("ADESIVOS BRANCO RECORTADOS", blocos[0]["objetos_incluidos"])

    def test_nao_cria_bloco_sem_instrucao_mesmo_tamanho(self):
        moldura = candidato(
            "A01", 100, 100,
            {"esquerda": 0, "direita": 100, "base": 0, "topo": 100},
        )
        evidencias = [{
            "texto": "ADESIVO RECORTADO", "caixa_mm": {
                "esquerda": 100, "direita": 400, "base": 800, "topo": 900,
            },
            "material": {"material": "adesivo", "acabamento": "recortado"}, "dimensoes": None,
        }]

        self.assertEqual(detectar_blocos_producao([moldura], evidencias), [])


if __name__ == "__main__":
    unittest.main()
