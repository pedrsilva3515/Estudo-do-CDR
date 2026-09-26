"""Texto de quantidade embaixo da peça e um texto por cópia (pedidos GGF, JJ, fernanda)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from zcfreader.experimento_agente import associar_instrucoes_regionais, resumir_catalogo_regional  # noqa: E402

LIMITES = {"esquerda": 0.0, "direita": 100.0, "base": 0.0, "topo": 100.0}
TAMANHO = (100, 100)  # 1 px = 1 cm


def _leitura(texto, esquerda, direita, base, topo):
    # Imagem com y para baixo: topo da página = 0 px.
    return {"texto": texto, "confianca": 1.0, "poligono_px": [
        [esquerda, 100 - topo], [direita, 100 - topo], [direita, 100 - base], [esquerda, 100 - base]]}


def _candidato(id_, esquerda, direita, base, topo, centros=None):
    centros = centros or [{"x": (esquerda + direita) / 2, "y": (base + topo) / 2}]
    return {"id": id_, "largura_cm": (direita - esquerda) / len(centros) if len(centros) > 1 else direita - esquerda,
            "altura_cm": topo - base, "quantidade_geometrica": len(centros), "posicoes_centro_cm": centros,
            "caixa_cm": {"esquerda": esquerda, "direita": direita, "base": base, "topo": topo}}


def _quantidades(candidatos, leituras):
    associacoes = associar_instrucoes_regionais(leituras, candidatos, LIMITES, TAMANHO)
    auditoria = resumir_catalogo_regional({"candidatos": candidatos, "ocr_regional": {"associacoes": associacoes}})
    return {item["candidato_id"]: item.get("quantidade_pedido") for item in auditoria["itens"]}


class TestQuantidadeAbaixo(unittest.TestCase):
    def test_texto_embaixo_da_peca(self):
        peca = _candidato("A01", 10, 40, 30, 70)
        self.assertEqual(_quantidades([peca], [_leitura("20und", 20, 28, 25, 28)])["A01"], 20)

    def test_um_texto_por_copia_soma(self):
        # Duas cópias de 20 x 10 lado a lado, "9 unid" embaixo de uma e "1 unid" embaixo da outra.
        peca = _candidato("A01", 10, 60, 40, 50, centros=[{"x": 20, "y": 45}, {"x": 50, "y": 45}])
        leituras = [_leitura("9 unid", 16, 24, 37, 39), _leitura("1 unid", 46, 54, 37, 39)]
        self.assertEqual(_quantidades([peca], leituras)["A01"], 10)

    def test_mesmo_texto_embaixo_de_cada_copia_soma(self):
        peca = _candidato("A01", 10, 60, 40, 50, centros=[{"x": 20, "y": 45}, {"x": 50, "y": 45}])
        leituras = [_leitura("25und", 16, 24, 37, 39), _leitura("25und", 46, 54, 37, 39)]
        self.assertEqual(_quantidades([peca], leituras)["A01"], 50)

    def test_texto_em_cima_continua_preferido(self):
        de_cima = _candidato("A01", 10, 40, 50, 80)
        de_baixo = _candidato("A02", 10, 40, 5, 20)
        quantidades = _quantidades([de_cima, de_baixo], [_leitura("3 und", 20, 28, 22, 24)])
        self.assertEqual(quantidades["A02"], 3)
        self.assertIsNone(quantidades["A01"])


if __name__ == "__main__":
    unittest.main()
