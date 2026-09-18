import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zcfreader import modelos_locais  # noqa: E402


class TestModelosLocais(unittest.TestCase):
    def test_diretorio_fica_em_localappdata(self):
        with tempfile.TemporaryDirectory() as pasta, patch.dict(os.environ, {"LOCALAPPDATA": pasta}):
            self.assertEqual(
                modelos_locais.diretorio_modelos(),
                Path(pasta) / "LeitorPedidosCDR" / "modelos" / "qwen25-vl-3b",
            )

    def test_modelo_so_esta_pronto_com_tamanhos_e_runtime_corretos(self):
        with tempfile.TemporaryDirectory() as pasta, patch.object(
            modelos_locais, "diretorio_modelos", return_value=Path(pasta)
        ), patch.object(modelos_locais, "TAMANHO_MODELO", 3), patch.object(
            modelos_locais, "TAMANHO_MMPROJ", 2
        ):
            caminhos = modelos_locais.caminhos_instalacao()
            caminhos["modelo"].write_bytes(b"abc")
            caminhos["mmproj"].write_bytes(b"de")
            caminhos["executavel"].parent.mkdir()
            caminhos["executavel"].write_bytes(b"exe")
            self.assertTrue(modelos_locais.modelo_instalado())
            caminhos["modelo"].write_bytes(b"x")
            self.assertFalse(modelos_locais.modelo_instalado())

    def test_extrai_ultimo_json_valido_da_saida(self):
        texto = 'log {"parcial": true}\nresposta {"itens": [], "observacoes": ["ok"]}\n'
        self.assertEqual(modelos_locais._extrair_json(texto)["observacoes"], ["ok"])

    def test_extrai_envelope_e_nao_ultimo_item_aninhado(self):
        texto = '{"itens":[{"indice":1,"quantidade":2}],"observacoes":["ok"]}'
        resultado = modelos_locais._extrair_json(texto)
        self.assertIn("itens", resultado)
        self.assertEqual(resultado["itens"][0]["indice"], 1)

    def test_rejeita_json_fora_do_contrato(self):
        with self.assertRaisesRegex(RuntimeError, "formato esperado"):
            modelos_locais._extrair_json('{"indice": 1}')

    def test_evidencias_compactas_nao_enviam_lista_pesada_de_componentes(self):
        resultado = {
            "arquivo": {"nome": "pedido.cdr"},
            "itens": [{
                "indice": 1, "quantidade": {"valor": 2},
                "dimensoes": {"largura_mm": 300},
                "material": {"valor": None}, "acabamento": {"valor": None},
                "componentes": [{"pixels": {"largura": 9000}} for _ in range(40)],
            }],
            "pendencias": ["material"],
        }
        compacto = modelos_locais._evidencias_compactas(resultado)
        self.assertEqual(compacto["itens"][0]["total_componentes"], 40)
        self.assertNotIn("componentes", compacto["itens"][0])

    def test_schema_local_impede_observacoes_longas(self):
        schema = modelos_locais._schema_resposta_local()
        item = schema["properties"]["itens"]["items"]
        self.assertIn("largura_cm", item["properties"])
        self.assertIn("evidencia", item["properties"])
        self.assertIn("estrutura_confere", schema["properties"])
        self.assertEqual(schema["properties"]["observacoes"]["maxItems"], 0)

    def test_asset_runtime_ignora_release_sem_binario(self):
        releases = [
            {"assets": [{"name": "nightly-tag.txt", "browser_download_url": "x"}]},
            {"assets": [{
                "name": "llama-b123-bin-win-cpu-x64.zip",
                "browser_download_url": "https://example.test/runtime.zip",
            }]},
        ]

        class Resposta:
            def __enter__(self):
                return self

            def __exit__(self, *_args):
                return None

            def read(self):
                return json.dumps(releases).encode()

        with patch.object(modelos_locais, "urlopen", return_value=Resposta()):
            url, nome = modelos_locais._asset_runtime()
        self.assertEqual(url, "https://example.test/runtime.zip")
        self.assertEqual(nome, "llama-b123-bin-win-cpu-x64.zip")


if __name__ == "__main__":
    unittest.main()
