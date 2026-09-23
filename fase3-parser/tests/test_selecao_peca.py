"""Testes da escolha da peça certa na correção (sem interface)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(_AQUI.parent))

from zcfreader.selecao_peca import (  # noqa: E402
    aplicar_selecao_ao_item,
    candidatos_no_ponto,
    cm_do_px,
    pecas_na_regiao,
    px_do_cm,
    selecao_de_candidato,
    selecao_de_regiao,
    selecao_de_uniao,
)


def _caixa(e, d, b, t):
    return {"esquerda": e, "direita": d, "base": b, "topo": t}


# Um círculo de 4 cm (máscara) com uma foto de 4,13 cm dentro, e uma arte grande ao lado.
FATOS = {
    "limites_cm": _caixa(0, 40, 0, 20),
    "candidatos": {
        "A01": {"largura_cm": 20.0, "altura_cm": 11.0, "quantidade_geometrica": 1, "caixa_cm": _caixa(0, 20, 0, 11)},
        "A02": {"largura_cm": 4.13, "altura_cm": 4.09, "quantidade_geometrica": 1, "caixa_cm": _caixa(29.9, 34.03, 5.9, 9.99)},
        "A03": {"largura_cm": 4.0, "altura_cm": 4.0, "quantidade_geometrica": 1, "caixa_cm": _caixa(30, 34, 6, 10)},
    },
}


class TestSelecaoPeca(unittest.TestCase):
    def test_clique_lista_pecas_da_menor_para_a_maior(self):
        self.assertEqual(candidatos_no_ponto(FATOS, 32, 8), ["A03", "A02"])
        self.assertEqual(candidatos_no_ponto(FATOS, 10, 5), ["A01"])
        self.assertEqual(candidatos_no_ponto(FATOS, 38, 18), [])

    def test_conversao_de_pixels_ida_e_volta(self):
        tamanho = (800, 400)
        x0, y0, x1, y1 = px_do_cm(FATOS, tamanho, FATOS["candidatos"]["A03"]["caixa_cm"])
        self.assertAlmostEqual(cm_do_px(FATOS, tamanho, x0, y0)[0], 30)
        self.assertAlmostEqual(cm_do_px(FATOS, tamanho, x1, y1)[1], 6)

    def test_regiao_desenhada_vira_medida_em_cm(self):
        selecao = selecao_de_regiao(FATOS, (800, 400), 0, 0, 200, 100)
        self.assertEqual((selecao["largura_cm"], selecao["altura_cm"]), (10.0, 5.0))
        self.assertIsNone(selecao["id"])

    def test_arrasto_usa_pecas_do_arquivo_dentro_da_regiao(self):
        # Região folgada em volta do círculo: fica só a peça mais externa (A02, que
        # envolve A03 por 0,1 cm); a arte grande (A01) está fora da região.
        regiao = _caixa(29, 35, 5, 11)
        self.assertEqual(pecas_na_regiao(FATOS, regiao), ["A02"])
        self.assertEqual(pecas_na_regiao(FATOS, _caixa(38, 40, 0, 2)), [])

    def test_uniao_de_varias_pecas_tem_medida_exata(self):
        uniao = selecao_de_uniao(FATOS, ["A01", "A03"])
        self.assertEqual((uniao["largura_cm"], uniao["altura_cm"]), (34.0, 11.0))
        self.assertEqual(uniao["ids"], ["A01", "A03"])
        item = aplicar_selecao_ao_item({"quantidade": {"valor": 2}}, uniao)
        self.assertEqual(item["candidatos"], ["A01", "A03"])
        self.assertEqual(item["peca_correta"]["origem"], "uniao_de_pecas")

    def test_aplicar_troca_peca_e_preserva_quantidade_e_material(self):
        item = {
            "quantidade": {"valor": 15}, "material": {"valor": "adesivo"}, "acabamento": {"valor": "recortado"},
            "dimensoes": {"largura_mm": 41.3, "altura_mm": 40.9}, "candidatos": ["A02"],
        }
        novo = aplicar_selecao_ao_item(item, selecao_de_candidato(FATOS, "A03"))
        self.assertEqual(novo["quantidade"]["valor"], 15)
        self.assertEqual(novo["material"]["valor"], "adesivo")
        self.assertEqual((novo["dimensoes"]["largura_mm"], novo["dimensoes"]["altura_mm"]), (40.0, 40.0))
        self.assertEqual(novo["candidatos"], ["A03"])
        self.assertEqual(novo["peca_correta"]["id"], "A03")
        self.assertEqual(novo["peca_correta"]["antes"], {"ids": ["A02"], "largura_cm": 4.13, "altura_cm": 4.09})


if __name__ == "__main__":
    unittest.main()
