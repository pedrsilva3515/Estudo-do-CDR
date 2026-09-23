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

    def test_de_cada_multiplica_pelas_pecas_desenhadas(self):
        fatos = {
            "arquivo": "4_etapa.cdr",
            "candidatos": {"A02": {"largura_cm": 21.0, "altura_cm": 21.0, "quantidade_geometrica": 3, "caixa_cm": _caixa(0, 63, 0, 21), "pai_id": None}},
            "textos": {"T01": {"texto": "3 UNIDADES DE CADA IMPRIMIR NO ADESIVO BRANCO FOSCO BLACKOUT"}},
        }
        erros = validar(fatos, {"itens": [_item(["A02"], 3, texto="T01")]})
        self.assertTrue(any("3 de cada" in e and "9" in e for e in erros), erros)
        self.assertEqual(validar(fatos, {"itens": [_item(["A02"], 9, texto="T01")]}), [])

    def test_acabamento_nao_pode_repetir_o_material(self):
        fatos = {**FATOS, "textos": {**FATOS["textos"], "T30": {"texto": "VINIL BRILHOSO"}}}
        item = _item(["A47"], 12, texto="T11", material="VINIL BRILHOSO", texto_material="T30")
        item.update(acabamento="VINIL BRILHOSO", texto_acabamento="T30")
        self.assertTrue(any("repete o material" in e for e in validar(fatos, {"itens": [item]})))
        item.update(acabamento=None, texto_acabamento=None)
        self.assertEqual(validar(fatos, {"itens": [item]}), [])

    def test_material_sem_prova(self):
        erros = validar(FATOS, {"itens": [_item(["A47"], 12, texto="T11", material="lona", texto_material="T11")]})
        self.assertTrue(any("material 'lona'" in e for e in erros))

    def test_material_abreviado_e_sinonimos_sao_aceitos(self):
        from zcfreader.agente import _cita
        fatos = {"arquivo": "wadna banner e adesivo sem recorte.cdr", "textos": {
            "T10": {"texto": "ADS SEM REC 45X45 4 UNID"},
            "T17": {"texto": "banner 80x80"},
            "T20": {"texto": "ADESIVOS BRANCO RECORTADOS"},
            "T21": {"texto": "VINIL SUPER COLA"},
        }}
        self.assertTrue(_cita(fatos, "T10", "adesivo"))
        self.assertTrue(_cita(fatos, "T10", "sem recorte"))
        self.assertTrue(_cita(fatos, "T17", "lona"))
        self.assertTrue(_cita(fatos, "T20", "adesivo branco"))
        self.assertTrue(_cita(fatos, "T21", "adesivo super cola"))
        self.assertTrue(_cita(fatos, "NOME_ARQUIVO", "adesivo"))

    def test_citacao_exige_todos_os_termos(self):
        from zcfreader.agente import _cita
        fatos = {"arquivo": "x.cdr", "textos": {"T01": {"texto": "adesivo com recorte"}, "T02": {"texto": "4 UN (37X24,5 CM)"}}}
        self.assertFalse(_cita(fatos, "T01", "sem recorte"))
        self.assertFalse(_cita(fatos, "T01", "adesivo transparente"))
        self.assertFalse(_cita(fatos, "T02", "nenhum"))

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
