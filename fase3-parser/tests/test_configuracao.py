from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from zcfreader import configuracao


class TestConfiguracao(unittest.TestCase):
    def test_arquitetura_experimental_vem_desligada_por_padrao(self):
        with tempfile.TemporaryDirectory() as pasta, patch.object(
            configuracao, "caminho_configuracao", return_value=Path(pasta) / "config.json"
        ):
            self.assertFalse(configuracao.carregar_configuracao()["arquitetura_regional_experimental"])

    def test_persiste_opcao_experimental_explicitamente(self):
        with tempfile.TemporaryDirectory() as pasta, patch.object(
            configuracao, "caminho_configuracao", return_value=Path(pasta) / "config.json"
        ) as caminho_mock:
            configuracao.salvar_configuracao({
                "modo": "estrutural", "modelo": configuracao.MODELOS_OPENAI[0],
                "arquitetura_regional_experimental": True,
            })
            dados = json.loads(caminho_mock.return_value.read_text(encoding="utf-8"))

            self.assertEqual(dados["versao_config"], 4)
            self.assertTrue(configuracao.carregar_configuracao()["arquitetura_regional_experimental"])

    def test_persiste_provedor_e_modelo_openrouter(self):
        with tempfile.TemporaryDirectory() as pasta, patch.object(
            configuracao, "caminho_configuracao", return_value=Path(pasta) / "config.json"
        ):
            configuracao.salvar_configuracao({
                "modo": "api", "provedor": "openrouter",
                "modelo": configuracao.MODELOS_OPENAI[0], "modelo_openrouter": " google/gemini-3.5-flash ",
            })
            carregada = configuracao.carregar_configuracao()

            self.assertEqual(carregada["provedor"], "openrouter")
            self.assertEqual(configuracao.modelo_do_provedor(carregada), "google/gemini-3.5-flash")

    def test_configuracao_antiga_continua_na_openai(self):
        with tempfile.TemporaryDirectory() as pasta, patch.object(
            configuracao, "caminho_configuracao", return_value=Path(pasta) / "config.json"
        ) as caminho_mock:
            caminho_mock.return_value.write_text(json.dumps({
                "versao_config": 3, "modo": "api", "provedor": "openai", "modelo": "gpt-5.6-sol",
            }), encoding="utf-8")
            carregada = configuracao.carregar_configuracao()

            self.assertEqual(carregada["provedor"], "openai")
            self.assertEqual(configuracao.modelo_do_provedor(carregada), "gpt-5.6-sol")


if __name__ == "__main__":
    unittest.main()
