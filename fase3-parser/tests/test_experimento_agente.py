from __future__ import annotations

import unittest

from zcfreader.experimento_agente import (
    _anotar_hierarquia,
    _separar_regioes_contiguas,
    associar_instrucoes_regionais,
    associar_materiais_acabamentos,
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

    def test_separa_mesma_medida_em_ilhas_espaciais(self):
        item = {
            "largura_cm": 46.5, "altura_cm": 9,
            "quantidade_sugerida": 5,
            "posicoes_centro_cm": [
                {"x": 20, "y": 10}, {"x": 20, "y": 19},
                {"x": 20, "y": 28}, {"x": 20, "y": 37},
                {"x": 100, "y": 37},
            ],
        }

        regioes = _separar_regioes_contiguas(item)

        self.assertEqual([regiao["quantidade_sugerida"] for regiao in regioes], [4, 1])


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

    def test_prefere_regiao_visivel_a_detalhe_interno_da_mesma_medida(self):
        interno = candidato("A01", 46.5, 9, {"esquerda": 0, "direita": 46.5, "base": 0, "topo": 9})
        regional = candidato("A02", 46.5, 9, {"esquerda": 100, "direita": 146.5, "base": 0, "topo": 9})
        interno["visivel_inicialmente"] = False
        regional["visivel_inicialmente"] = True
        esperado = {
            "itens": [{
                "quantidade": {"valor": 12},
                "dimensoes": {"largura_mm": 465, "altura_mm": 90},
            }],
        }

        resultado = avaliar_cobertura_geometrica([interno, regional], esperado)

        self.assertEqual(resultado["detalhes"][0]["candidato"], "A02")


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


class TestAssociacaoRegional(unittest.TestCase):
    def test_de_cada_e_quantidade_individual_usam_faixa_horizontal(self):
        candidatos = [
            candidato("A01", 28, 33, {"esquerda": 10, "direita": 30, "base": 20, "topo": 40}),
            candidato("A02", 24, 94, {"esquerda": 40, "direita": 60, "base": 20, "topo": 40}),
            candidato("A03", 20, 25, {"esquerda": 70, "direita": 90, "base": 20, "topo": 40}),
        ]
        for item in candidatos:
            item["visivel_inicialmente"] = True
        leituras = [
            {
                "texto": "30 UNI DE CADA", "confianca": 0.99,
                "poligono_px": [[100, 100], [600, 100], [600, 150], [100, 150]],
            },
            {
                "texto": "60 UNI", "confianca": 0.99,
                "poligono_px": [[700, 100], [900, 100], [900, 150], [700, 150]],
            },
        ]

        resultado = associar_instrucoes_regionais(
            leituras, candidatos,
            {"esquerda": 0, "direita": 100, "base": 0, "topo": 100},
            (1000, 1000),
        )

        self.assertEqual(
            {(item["candidato_id"], item["quantidade"]) for item in resultado},
            {("A01", 30), ("A02", 30), ("A03", 60)},
        )
        self.assertTrue(all(not item["requer_confirmacao_semantica"] for item in resultado))

    def test_dimensao_explicita_prevalece_sobre_distancia(self):
        candidatos = [
            candidato("A01", 37, 24.5, {"esquerda": 70, "direita": 90, "base": 20, "topo": 40}, 4),
            candidato("A02", 20, 10, {"esquerda": 10, "direita": 30, "base": 60, "topo": 75}),
        ]
        for item in candidatos:
            item["visivel_inicialmente"] = True
        leituras = [{
            "texto": "4 UN (37X24,5 CM)", "confianca": 0.99,
            "poligono_px": [[100, 100], [400, 100], [400, 150], [100, 150]],
        }, {
            "texto": "0,3626 M²", "confianca": 0.99,
            "poligono_px": [[700, 850], [900, 850], [900, 900], [700, 900]],
        }]

        resultado = associar_instrucoes_regionais(
            leituras, candidatos,
            {"esquerda": 0, "direita": 100, "base": 0, "topo": 100},
            (1000, 1000),
        )

        self.assertEqual(resultado[0]["candidato_id"], "A01")
        self.assertEqual(resultado[0]["regra"], "dimensao_explicita")
        self.assertEqual(resultado[0]["quantidade_calculada_area"], 4)
        self.assertTrue(resultado[0]["area_confere_quantidade"])
        self.assertEqual(resultado[0]["interpretacao_quantidade"], "uma_unidade_por_ocorrencia_desenhada")
        self.assertFalse(resultado[0]["requer_confirmacao_semantica"])

    def test_mesma_quantidade_que_ocorrencias_sem_area_permanece_ambigua(self):
        item = candidato("A01", 46.5, 9, {"esquerda": 10, "direita": 56.5, "base": 20, "topo": 56}, 4)
        item["visivel_inicialmente"] = True
        leituras = [{
            "texto": "4 UN (46,5X9 CM)", "confianca": 0.99,
            "poligono_px": [[100, 100], [500, 100], [500, 150], [100, 150]],
        }]

        resultado = associar_instrucoes_regionais(
            leituras, [item],
            {"esquerda": 0, "direita": 100, "base": 0, "topo": 100},
            (1000, 1000),
        )

        self.assertTrue(resultado[0]["requer_confirmacao_semantica"])
        self.assertEqual(resultado[0]["interpretacao_quantidade"], "total_igual_as_ocorrencias_desenhadas_sem_area")


class TestMateriaisRegionais(unittest.TestCase):
    def test_dimensao_no_rotulo_e_legenda_abaixo_separam_documento_misto(self):
        banner = candidato("A01", 80, 80, {"esquerda": 0, "direita": 80, "base": 20, "topo": 100})
        adesivos = candidato("A02", 43, 43, {"esquerda": 100, "direita": 143, "base": 20, "topo": 63}, 5)
        for item in (banner, adesivos):
            item["visivel_inicialmente"] = True
        catalogo = {
            "arquivo": "banner e adesivo sem recorte.cdr",
            "candidatos": [banner, adesivos], "blocos_producao": [],
            "ocr_regional": {"associacoes": [], "leituras_ocr": []},
            "evidencias_textuais": [
                {
                    "texto": "banner 80x80", "quantidade": None, "dimensoes": None,
                    "material": {"material": "banner", "acabamento": None},
                    "caixa_mm": {"esquerda": 100, "direita": 700, "base": 1050, "topo": 1150},
                },
                {
                    "texto": "ads sem recorte", "quantidade": None, "dimensoes": None,
                    "material": None,
                    "caixa_mm": {"esquerda": 1000, "direita": 1430, "base": 0, "topo": 100},
                },
            ],
        }

        resultado = {item["candidato_id"]: item for item in associar_materiais_acabamentos(catalogo)}

        self.assertEqual(resultado["A01"]["material"], "banner")
        self.assertEqual(resultado["A02"]["material"], "adesivo")
        self.assertEqual(resultado["A02"]["acabamento"], "sem recorte")

    def test_preserva_acabamentos_compostos(self):
        item = candidato("A01", 88, 88, {"esquerda": 0, "direita": 88, "base": 0, "topo": 88})
        item["visivel_inicialmente"] = True
        catalogo = {
            "arquivo": "material.cdr", "candidatos": [item], "blocos_producao": [],
            "ocr_regional": {"associacoes": [], "leituras_ocr": []},
            "evidencias_textuais": [{
                "texto": "LONA + VERNIZ - FRENTE E VERSO + ILHÓS",
                "quantidade": None, "dimensoes": None,
                "material": {"material": "lona", "acabamento": None},
                "caixa_mm": {"esquerda": 0, "direita": 880, "base": 900, "topo": 1000},
            }],
        }

        resultado = associar_materiais_acabamentos(catalogo)

        self.assertEqual(resultado[0]["material"], "lona")
        self.assertEqual(resultado[0]["acabamento"], "frente e verso + ilhós + verniz")


if __name__ == "__main__":
    unittest.main()
