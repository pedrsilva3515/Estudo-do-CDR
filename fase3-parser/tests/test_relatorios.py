import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from zcfreader.relatorios import (  # noqa: E402
    classificar_diferencas,
    gerar_pacote_diagnostico,
    normalizar_resultado_corrigido,
)


def resultado(qtd=1, largura=100, material=None):
    return {
        "itens": [{
            "indice": 1, "quantidade": {"valor": qtd},
            "dimensoes": {"largura_mm": largura, "altura_mm": 200},
            "material": {"valor": material}, "acabamento": {"valor": None},
        }],
        "total_unidades": qtd, "pendencias": ["material", "acabamento"],
        "processamento": {"provedor": "local", "modelo": "teste"},
    }


class TestRelatorios(unittest.TestCase):
    def test_normaliza_total_indices_e_pendencias(self):
        valor = resultado(qtd=3, material="adesivo")
        valor["itens"][0]["indice"] = 9
        corrigido = normalizar_resultado_corrigido(valor)
        self.assertEqual(corrigido["itens"][0]["indice"], 1)
        self.assertEqual(corrigido["total_unidades"], 3)
        self.assertEqual(corrigido["pendencias"], ["acabamento"])

    def test_classifica_campos_alterados(self):
        antes = resultado()
        depois = resultado(qtd=9, largura=234, material="adesivo transparente")
        self.assertEqual(classificar_diferencas(antes, depois), ["quantidade", "dimensoes", "material"])

    def test_gera_zip_sem_incluir_cdr_por_padrao(self):
        with tempfile.TemporaryDirectory() as pasta:
            raiz = Path(pasta)
            cdr = raiz / "pedido.cdr"
            cdr.write_bytes(b"arquivo de teste")
            with patch.dict(os.environ, {"USERPROFILE": pasta}), patch(
                "zcfreader.relatorios.extrair_preview", return_value=(b"png", "image/png")
            ):
                destino = gerar_pacote_diagnostico(cdr, resultado(), resultado(qtd=2), situacao="corrigido")
            with ZipFile(destino) as pacote:
                nomes = set(pacote.namelist())
                self.assertIn("resultado-original.json", nomes)
                self.assertIn("resultado-correto.json", nomes)
                self.assertIn("diagnostico.json", nomes)
                self.assertIn("resumo.txt", nomes)
                self.assertIn("preview.png", nomes)
                self.assertFalse(any(nome.startswith("arquivo-original/") for nome in nomes))
                diagnostico = json.loads(pacote.read("diagnostico.json"))
                self.assertEqual(diagnostico["situacao"], "corrigido")


if __name__ == "__main__":
    unittest.main()
