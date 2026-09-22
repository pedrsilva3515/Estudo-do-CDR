"""Testes do validador e da conversão do agente (sem chamadas de API)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(_AQUI.parent))

from zcfreader.agente import resultado_do_agente, validar  # noqa: E402


def _caixa(e, d, b, t):
    return {"esquerda": e, "direita": d, "base": b, "topo": t}


FATOS = {
    "arquivo": "VINIL SUPER COLA - TSCAR 014.cdr",
    "candidatos": {
        "A01": {"largura_cm": 37.0, "altura_cm": 24.5, "quantidade_geometrica": 4, "caixa_cm": _caixa(0, 148, 0, 24.5), "pai_id": None},
        "A02": {"largura_cm": 37.0, "altura_cm": 24.5, "quantidade_geometrica": 1, "caixa_cm": _caixa(0, 37, 0, 24.5), "pai_id": "A01"},
        "A10": {"largura_cm": 46.5, "altura_cm": 9.0, "quantidade_geometrica": 4, "caixa_cm": _caixa(0, 46.5, -60, -24), "pai_id": None},
        "A47": {"largura_cm": 46.5, "altura_cm": 9.0, "quantidade_geometrica": 1, "caixa_cm": _caixa(80, 126.5, -40, -31), "pai_id": None},
        "A20": {"largura_cm": 26.8, "altura_cm": 4.0, "quantidade_geometrica": 1, "caixa_cm": _caixa(5, 31.8, -20, -16), "pai_id": None},
    },
    "textos": {
        "T01": {"texto": "4 UN (37X24,5 CM)"},
        "T11": {"texto": "12 UN (46,5X9 CM)"},
    },
}


def _item(ids, quantidade, origem="texto", texto="T01", combinar="nao", material=None, texto_material=None):
    return {
        "ids": ids, "combinar": combinar, "quantidade": quantidade, "origem_quantidade": origem,
        "texto_quantidade": texto, "material": material, "texto_material": texto_material,
        "acabamento": None, "texto_acabamento": None, "justificativa": "",
    }


class TestValidadorAgente(unittest.TestCase):
    def test_resposta_correta_passa(self):
        resposta = {"itens": [
            _item(["A01"], 4, material="adesivo super cola", texto_material="NOME_ARQUIVO"),
            _item(["A47"], 12, texto="T11"),
            _item(["A10"], 4, origem="ocorrencias_desenhadas", texto=None),
        ]}
        self.assertEqual(validar(FATOS, resposta), [])

    def test_quantidade_sem_texto_que_a_contenha(self):
        erros = validar(FATOS, {"itens": [_item(["A47"], 105, texto="T11")]})
        self.assertTrue(any("não contém a quantidade 105" in e for e in erros))

    def test_ocorrencias_divergentes(self):
        erros = validar(FATOS, {"itens": [_item(["A10"], 3, origem="ocorrencias_desenhadas", texto=None)]})
        self.assertTrue(any("4 ocorrência" in e for e in erros))

    def test_pai_e_filho_no_pedido_contam_em_dobro(self):
        erros = validar(FATOS, {"itens": [_item(["A01"], 4), _item(["A02"], 4)]})
        self.assertTrue(any("um dentro do outro" in e for e in erros))

    def test_id_inexistente_e_repetido(self):
        erros = validar(FATOS, {"itens": [_item(["A99"], 4), _item(["A47"], 12, texto="T11"), _item(["A47"], 12, texto="T11")]})
        self.assertTrue(any("inexistentes" in e for e in erros))
        self.assertTrue(any("já está no item" in e for e in erros))

    def test_material_sem_prova(self):
        erros = validar(FATOS, {"itens": [_item(["A47"], 12, texto="T11", material="lona", texto_material="T11")]})
        self.assertTrue(any("material 'lona'" in e for e in erros))

    def test_medidas_diferentes_sem_uniao(self):
        erros = validar(FATOS, {"itens": [_item(["A47", "A20"], 12, texto="T11")]})
        self.assertTrue(any("medidas diferentes" in e for e in erros))

    def test_medidas_saem_do_cdr_e_uniao_usa_caixa_envolvente(self):
        resultado = resultado_do_agente(FATOS, {"itens": [
            _item(["A47"], 12, texto="T11"),
            _item(["A10", "A20"], 1, origem="ocorrencias_desenhadas", texto=None, combinar="uniao"),
        ], "perguntas": [{"pergunta": "A20 é produto?", "ids": ["A20"]}]})
        self.assertEqual(resultado["itens"][0]["dimensoes"]["largura_mm"], 465)
        self.assertEqual(resultado["itens"][1]["dimensoes"]["largura_mm"], 465)
        self.assertEqual(resultado["itens"][1]["dimensoes"]["altura_mm"], 440)
        self.assertEqual(resultado["total_unidades"], 13)
        self.assertEqual(len(resultado["perguntas"]), 1)


if __name__ == "__main__":
    unittest.main()
