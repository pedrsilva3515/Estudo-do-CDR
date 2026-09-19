from __future__ import annotations

import unittest
from pathlib import Path
from queue import Queue
from unittest.mock import patch

from zcfreader.gui import (
    AplicacaoPedido,
    aplicar_sugestao_regional,
    coletar_conflitos,
    comparar_resultado_com_regional,
)


class TestConflitosInterface(unittest.TestCase):
    def test_reune_conflito_regional_e_preserva_evidencia(self):
        resultado = {
            "materiais_regionais": [{
                "candidato_id": "A01",
                "conflitos": [{"campo": "material", "valores": ["adesivo", "banner"]}],
                "evidencias": [{"texto": "BANNER"}, {"texto": "ADESIVO"}],
            }],
        }

        conflitos = coletar_conflitos(resultado)

        self.assertEqual(len(conflitos), 1)
        self.assertEqual(conflitos[0]["candidato_id"], "A01")
        self.assertEqual(conflitos[0]["valores"], ["adesivo", "banner"])
        self.assertEqual([item["texto"] for item in conflitos[0]["evidencias"]], ["BANNER", "ADESIVO"])

    def test_remove_conflito_duplicado(self):
        conflito = {
            "candidato_id": "A01", "campo": "acabamento",
            "valor_do_arquivo": "sem recorte", "valor_confirmado": "recorte especial",
        }
        resultado = {"conflitos_revisao": [conflito, dict(conflito)]}

        self.assertEqual(coletar_conflitos(resultado), [conflito])


class TestCamadaExperimental(unittest.TestCase):
    def aplicacao_sem_tk(self, ativa=True):
        aplicacao = AplicacaoPedido.__new__(AplicacaoPedido)
        aplicacao.configuracao = {
            "modo": "estrutural", "arquitetura_regional_experimental": ativa,
        }
        aplicacao.fila = Queue()
        return aplicacao

    def test_sucesso_anexa_auditoria_sem_substituir_itens_estaveis(self):
        aplicacao = self.aplicacao_sem_tk()
        estavel = {"itens": [{"indice": 1}], "alertas": [], "processamento": {}}
        auditoria = {"itens": [{"candidato_id": "A01"}], "conflitos_fontes": [], "resumo": {}}
        with patch("zcfreader.gui.interpretar_pedido", return_value=estavel), patch(
            "zcfreader.gui.executar_arquitetura_regional", return_value=auditoria
        ):
            aplicacao._executar_analise(Path("pedido.cdr"))

        estado, conteudo = aplicacao.fila.get_nowait()
        self.assertEqual(estado, "ok")
        self.assertEqual(conteudo["resultado"]["itens"], estavel["itens"])
        self.assertEqual(conteudo["resultado"]["analise_regional_experimental"], auditoria)
        self.assertEqual(conteudo["resultado"]["comparacao_regional"]["resumo"]["somente_principal"], 1)

    def test_falha_experimental_mantem_resultado_estavel(self):
        aplicacao = self.aplicacao_sem_tk()
        estavel = {"itens": [{"indice": 1}], "alertas": []}
        with patch("zcfreader.gui.interpretar_pedido", return_value=estavel), patch(
            "zcfreader.gui.executar_arquitetura_regional", side_effect=RuntimeError("falha controlada")
        ):
            aplicacao._executar_analise(Path("pedido.cdr"))

        estado, conteudo = aplicacao.fila.get_nowait()
        self.assertEqual(estado, "ok")
        self.assertEqual(conteudo["resultado"]["itens"], estavel["itens"])
        self.assertEqual(
            conteudo["resultado"]["alertas"][-1]["codigo"],
            "FALHA_ARQUITETURA_REGIONAL_EXPERIMENTAL",
        )


class TestComparacaoRegional(unittest.TestCase):
    def item_principal(self, quantidade, largura, altura, material="adesivo", acabamento=None):
        return {
            "quantidade": {"valor": quantidade},
            "dimensoes": {"largura_mm": largura * 10, "altura_mm": altura * 10},
            "material": {"valor": material}, "acabamento": {"valor": acabamento},
        }

    def item_regional(self, identificador, quantidade, largura, altura, material="adesivo", acabamento=None):
        return {
            "candidato_id": identificador, "papel": "produto_confirmado",
            "quantidade_pedido": quantidade, "quantidade_desenhada": 1,
            "largura_cm": largura, "altura_cm": altura,
            "material": material, "acabamento": acabamento,
        }

    def test_pareia_por_medida_independente_da_ordem_e_aceita_subtipo(self):
        principal = {"itens": [
            self.item_principal(30, 28, 33),
            self.item_principal(60, 20, 25),
        ]}
        auditoria = {"itens": [
            self.item_regional("A03", 60, 25, 20, "adesivo fosco"),
            self.item_regional("A01", 30, 28, 33, "adesivo fosco"),
        ]}

        comparacao = comparar_resultado_com_regional(principal, auditoria)

        self.assertEqual(comparacao["resumo"]["compativeis"], 2)
        self.assertEqual(comparacao["resumo"]["divergencias"], 0)
        self.assertEqual(
            [item["item_regional"]["candidato_id"] for item in comparacao["correspondencias"]],
            ["A01", "A03"],
        )

    def test_aponta_quantidade_e_acabamento_divergentes(self):
        principal = {"itens": [self.item_principal(4, 46.5, 9, acabamento="recorte especial")]}
        auditoria = {"itens": [self.item_regional(
            "A01", 12, 46.5, 9, acabamento="sem recorte"
        )]}

        correspondencia = comparar_resultado_com_regional(principal, auditoria)["correspondencias"][0]

        self.assertEqual(correspondencia["estado"], "divergencia")
        self.assertEqual(correspondencia["diferencas"], ["quantidade", "acabamento"])

    def test_quantidade_desambigua_produtos_com_a_mesma_medida(self):
        principal = {"itens": [
            self.item_principal(4, 46.5, 9),
            self.item_principal(12, 46.5, 9),
        ]}
        auditoria = {"itens": [
            self.item_regional("A02", 12, 46.5, 9),
            self.item_regional("A01", 4, 46.5, 9),
        ]}

        correspondencias = comparar_resultado_com_regional(principal, auditoria)["correspondencias"]

        self.assertEqual(correspondencias[0]["item_regional"]["candidato_id"], "A01")
        self.assertEqual(correspondencias[1]["item_regional"]["candidato_id"], "A02")
        self.assertTrue(all(item["estado"] == "compativel" for item in correspondencias))

    def test_separa_itens_exclusivos_e_ignora_estrutura_auxiliar(self):
        principal = {"itens": [self.item_principal(1, 10, 10)]}
        auxiliar = self.item_regional("A00", 1, 10, 10)
        auxiliar["papel"] = "detalhe_interno_do_produto"
        auditoria = {"itens": [
            auxiliar,
            self.item_regional("A02", 1, 20, 20),
        ]}

        resumo = comparar_resultado_com_regional(principal, auditoria)["resumo"]

        self.assertEqual(resumo["somente_principal"], 1)
        self.assertEqual(resumo["somente_regional"], 1)


class TestAplicacaoSeletivaRegional(unittest.TestCase):
    def item_principal(self, quantidade, largura, altura, material="adesivo", acabamento=None):
        return {
            "quantidade": {"valor": quantidade},
            "dimensoes": {"largura_mm": largura * 10, "altura_mm": altura * 10},
            "material": {"valor": material}, "acabamento": {"valor": acabamento},
        }

    def item_regional(self, identificador, quantidade, largura, altura, material="adesivo", acabamento=None):
        return {
            "candidato_id": identificador, "papel": "produto_confirmado",
            "quantidade_pedido": quantidade, "quantidade_desenhada": 1,
            "largura_cm": largura, "altura_cm": altura,
            "material": material, "acabamento": acabamento,
        }

    def test_atualiza_somente_linha_escolhida_sem_apagar_campo_ausente(self):
        principal = {"itens": [
            self.item_principal(4, 46.5, 9, acabamento="recorte especial"),
            self.item_principal(1, 20, 20, material="adesivo leitoso"),
        ]}
        regional = self.item_regional("A01", 12, 46.5, 9, "adesivo super cola", None)
        correspondencia = {
            "indice_principal": 0, "item_principal": principal["itens"][0],
            "item_regional": regional,
        }

        registro = aplicar_sugestao_regional(principal, correspondencia)

        self.assertEqual(registro["acao"], "atualizado")
        self.assertEqual(principal["itens"][0]["quantidade"]["valor"], 12)
        self.assertEqual(principal["itens"][0]["material"]["valor"], "adesivo super cola")
        self.assertEqual(principal["itens"][0]["acabamento"]["valor"], "recorte especial")
        self.assertEqual(principal["itens"][1]["material"]["valor"], "adesivo leitoso")
        self.assertEqual(principal["aplicacoes_regionais"][0]["candidato_id"], "A01")

    def test_adiciona_produto_exclusivamente_regional_com_quantidade_confirmada(self):
        principal = {"itens": []}
        regional = self.item_regional("A02", 4, 37, 24.5, "adesivo super cola")

        registro = aplicar_sugestao_regional(principal, {
            "indice_principal": None, "item_principal": None, "item_regional": regional,
        })

        self.assertEqual(registro["acao"], "adicionado")
        self.assertEqual(len(principal["itens"]), 1)
        self.assertEqual(principal["itens"][0]["quantidade"]["valor"], 4)
        self.assertEqual(principal["itens"][0]["dimensoes"]["largura_mm"], 370)

    def test_nao_adiciona_produto_sem_quantidade_de_pedido(self):
        principal = {"itens": []}
        regional = self.item_regional("A02", None, 37, 24.5)

        with self.assertRaisesRegex(ValueError, "quantidade de pedido"):
            aplicar_sugestao_regional(principal, {
                "indice_principal": None, "item_principal": None, "item_regional": regional,
            })

        self.assertEqual(principal["itens"], [])

    def test_aplicacao_resolve_divergencia_na_recomparacao(self):
        principal = {"itens": [self.item_principal(4, 46.5, 9, acabamento="recorte especial")]}
        auditoria = {"itens": [self.item_regional(
            "A01", 12, 46.5, 9, acabamento="sem recorte"
        )]}
        antes = comparar_resultado_com_regional(principal, auditoria)

        aplicar_sugestao_regional(principal, antes["correspondencias"][0])
        depois = comparar_resultado_com_regional(principal, auditoria)

        self.assertEqual(antes["resumo"]["divergencias"], 1)
        self.assertEqual(depois["resumo"]["compativeis"], 1)


if __name__ == "__main__":
    unittest.main()
