from __future__ import annotations

import unittest
from pathlib import Path
from queue import Queue
from unittest.mock import patch

from zcfreader.gui import AplicacaoPedido, coletar_conflitos


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


if __name__ == "__main__":
    unittest.main()
