"""Cache da leitura dos CDR usado pela régua."""
from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from zcfreader import cache_leitura  # noqa: E402


class TestCacheLeitura(unittest.TestCase):
    def test_mesma_entrada_nao_recalcula_e_entrada_nova_sim(self):
        chamadas = []

        def lenta(entrada, fator=1):
            chamadas.append(entrada)
            return {"tamanho": len(entrada) * fator}

        with tempfile.TemporaryDirectory() as tmp:
            guardada = cache_leitura._guardado(Path(tmp), "teste", "ocr", lenta)
            self.assertEqual(guardada(b"abc"), {"tamanho": 3})
            self.assertEqual(guardada(b"abc"), {"tamanho": 3})
            self.assertEqual(len(chamadas), 1)
            self.assertEqual(guardada(b"abcd"), {"tamanho": 4})      # outro conteúdo
            self.assertEqual(guardada(b"abc", fator=2), {"tamanho": 6})  # outros argumentos
            self.assertEqual(len(chamadas), 3)

    def test_arquivo_e_lido_pelo_conteudo(self):
        with tempfile.TemporaryDirectory() as tmp:
            pasta = Path(tmp)
            (pasta / "a.cdr").write_bytes(b"conteudo")
            (pasta / "b.cdr").write_bytes(b"conteudo")
            chamadas = []
            guardada = cache_leitura._guardado(pasta / "cache", "teste", "ocr", lambda c: chamadas.append(c) or 1)
            guardada(pasta / "a.cdr")
            guardada(pasta / "b.cdr")  # mesmo conteúdo, outro nome: já está no cache
            self.assertEqual(len(chamadas), 1)

    def test_versao_muda_com_o_codigo_importado(self):
        # experimento_agente importa pedido: a versão dele cobre o código de pedido.py.
        self.assertIn("pedido", cache_leitura._imports_locais("experimento_agente"))
        self.assertNotEqual(cache_leitura.versao_codigo("ocr"), cache_leitura.versao_codigo("render_proprio"))


if __name__ == "__main__":
    unittest.main()
