"""As regras leem o texto nativo; o OCR só completa o que não existe como texto."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(_AQUI.parent))

from zcfreader.experimento_agente import associar_instrucoes_regionais, leituras_para_regras  # noqa: E402

LIMITES = {"esquerda": 0.0, "direita": 100.0, "base": 0.0, "topo": 100.0}
TAMANHO = (1000, 1000)


def _ocr(texto, e, d, b, t):
    return {"texto": texto, "confianca": 0.9, "caixa_cm": {"esquerda": e, "direita": d, "base": b, "topo": t},
            "poligono_px": [[e * 10, (100 - t) * 10], [d * 10, (100 - t) * 10], [d * 10, (100 - b) * 10], [e * 10, (100 - b) * 10]]}


class TestLeiturasRegras(unittest.TestCase):
    def test_legenda_nativa_substitui_o_ocr_quebrado(self):
        # O OCR quebrou "1 UNI DE CADA" em dois pedaços; o texto nativo tem a legenda inteira.
        ocr = [_ocr("1UNI", 20, 45, 80, 88), _ocr("DE CADA", 47, 90, 80, 88), _ocr("4 UN (46,5X9)", 5, 15, 20, 24)]
        nativos = [{"texto": "1 UNI DE CADA", "caixa_mm": {"esquerda": 200, "direita": 900, "base": 800, "topo": 880}}]
        leituras = leituras_para_regras(ocr, nativos, LIMITES, TAMANHO)
        self.assertEqual([l["texto"] for l in leituras], ["1 UNI DE CADA", "4 UN (46,5X9)"])  # texto em curva fica

        candidatos = [
            {"id": f"A0{n}", "largura_cm": 20, "altura_cm": 30, "quantidade_geometrica": 1, "visivel_inicialmente": True,
             "caixa_cm": {"esquerda": x, "direita": x + 20, "base": 40, "topo": 70}}
            for n, x in ((1, 22), (2, 45), (3, 68))
        ]
        associacoes = associar_instrucoes_regionais(leituras, candidatos, LIMITES, TAMANHO)
        de_cada = sorted(a["candidato_id"] for a in associacoes if a["regra"] == "quantidade_de_cada")
        self.assertEqual(de_cada, ["A01", "A02", "A03"])


if __name__ == "__main__":
    unittest.main()
