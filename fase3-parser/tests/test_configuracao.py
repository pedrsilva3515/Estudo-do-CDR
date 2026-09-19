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

            self.assertEqual(dados["versao_config"], 3)
            self.assertTrue(configuracao.carregar_configuracao()["arquitetura_regional_experimental"])


if __name__ == "__main__":
    unittest.main()
