"""Testes do fluxo em camadas com agentes falsos (sem chamadas de API)."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(_AQUI.parent))

from zcfreader.camadas import interpretar_em_camadas, motivos_para_escalar, regras_resolvem  # noqa: E402


def _regra(cid, papel, estado, qp, w, h, material="adesivo"):
    return {"candidato_id": cid, "papel": papel, "estado": estado, "quantidade_pedido": qp,
            "largura_cm": w, "altura_cm": h, "material": material, "acabamento": None, "evidencias": []}


CONFIRMADA = {"itens": [_regra("A01", "produto_confirmado", "confirmado_por_evidencia", 30, 28, 33)], "conflitos_fontes": []}
AMBIGUA = {"itens": [
    _regra("A01", "produto_confirmado", "confirmado_por_evidencia", 9, 23.4, 18.4),
    _regra("A04", "sem_classificacao", "revisao_necessaria", None, 23.4, 14.1),
], "conflitos_fontes": []}
ESTRUTURAL = {"itens": [{"indice": 1, "quantidade": {"valor": 1}, "dimensoes": {"largura_mm": 10, "altura_mm": 10}}], "alertas": []}


def _resultado(qtd, w, h, perguntas=(), erros=(), custo=0.004):
    return {
        "itens": [{"quantidade": {"valor": qtd}, "dimensoes": {"largura_mm": w * 10, "altura_mm": h * 10},
                   "material": {"valor": "adesivo"}, "acabamento": {"valor": None}}],
        "perguntas": [{"pergunta": p, "ids": []} for p in perguntas],
        "rastro_agente": {"custo_usd": custo, "erros_restantes": list(erros)},
    }


class AgenteFalso:
    def __init__(self, respostas):
        self.respostas = respostas
        self.chamados = []

    def __call__(self, caminho, chave, modelo, fatos=None, custo_maximo_usd=None):
        self.chamados.append((modelo, custo_maximo_usd))
        resposta = self.respostas[modelo]
        if isinstance(resposta, Exception):
            raise resposta
        return resposta


def _rodar(auditoria, agente, chave="k"):
    return interpretar_em_camadas(
        Path("x.cdr"), chave, ESTRUTURAL, modelo_rapido="rapido", modelo_forte="forte",
        custo_maximo_usd=0.08, executar_agente=agente, fatos={"auditoria_regional": auditoria},
    )


class TestCamadas(unittest.TestCase):
    def test_regras_confirmadas_dispensam_ia(self):
        agente = AgenteFalso({})
        resultado = _rodar(CONFIRMADA, agente)
        self.assertEqual(agente.chamados, [])
        self.assertEqual(resultado["processamento"]["camada_final"], "regras")
        self.assertEqual(resultado["total_unidades"], 30)

    def test_peca_em_revisao_impede_regras(self):
        self.assertFalse(regras_resolvem(AMBIGUA))
        self.assertFalse(regras_resolvem({"itens": [_regra("A01", "produto_confirmado", "confirmado_por_evidencia", None, 1, 1)]}))

    def test_modelo_rapido_sem_sinais_nao_escala(self):
        agente = AgenteFalso({"rapido": _resultado(9, 23.4, 18.4)})
        resultado = _rodar(AMBIGUA, agente)
        self.assertEqual([m for m, _ in agente.chamados], ["rapido"])
        self.assertEqual(resultado["processamento"]["camada_final"], "modelo_rapido")
        self.assertEqual(resultado["itens_estruturais"], ESTRUTURAL["itens"])

    def test_pergunta_escala_para_o_forte_com_orcamento_restante(self):
        agente = AgenteFalso({"rapido": _resultado(9, 23.4, 18.4, perguntas=["Qual material?"], custo=0.01),
                              "forte": _resultado(9, 23.4, 18.4, custo=0.02)})
        resultado = _rodar(AMBIGUA, agente)
        self.assertEqual([m for m, _ in agente.chamados], ["rapido", "forte"])
        self.assertAlmostEqual(agente.chamados[1][1], 0.07)
        self.assertEqual(resultado["processamento"]["camada_final"], "modelo_forte")
        self.assertAlmostEqual(resultado["processamento"]["custo_usd"], 0.03)
        self.assertEqual(resultado["perguntas_operador"], [])

    def test_contradizer_regra_confirmada_escala(self):
        motivos = motivos_para_escalar(_resultado(1, 23.4, 18.4), AMBIGUA)
        self.assertTrue(any("contradiz" in m for m in motivos))

    def test_quantidade_incompativel_com_pecas_desenhadas_escala(self):
        fatos = {"candidatos": {"A08": {"quantidade_geometrica": 12}, "A10": {"quantidade_geometrica": 4}, "A47": {"quantidade_geometrica": 1}}}
        nove_de_doze = _resultado(9, 9, 5)
        nove_de_doze["itens"][0]["candidatos"] = ["A08"]
        self.assertTrue(any("12 peças" in m for m in motivos_para_escalar(nove_de_doze, {"itens": []}, fatos)))
        for qtd, cid in ((4, "A10"), (12, "A47"), (8, "A10"), (9, "A47")):
            ok = _resultado(qtd, 46.5, 9)
            ok["itens"][0]["candidatos"] = [cid]
            self.assertEqual(motivos_para_escalar(ok, {"itens": []}, fatos), [], (qtd, cid))

    def test_divergencia_entre_modelos_e_perguntas_vao_ao_operador(self):
        agente = AgenteFalso({"rapido": _resultado(9, 23.4, 18.4, erros=["x"]),
                              "forte": _resultado(9, 23.4, 18.4, perguntas=["São 5 itens ou 1?"])})
        agente.respostas["forte"]["itens"][0]["quantidade"]["valor"] = 9
        agente.respostas["forte"]["itens"].append({"quantidade": {"valor": 1}, "dimensoes": {"largura_mm": 100, "altura_mm": 100}})
        resultado = _rodar(AMBIGUA, agente)
        codigos = [a["codigo"] for a in resultado["alertas"]]
        self.assertIn("MODELOS_DIVERGEM", codigos)
        self.assertIn("PERGUNTA_AO_OPERADOR", codigos)
        self.assertIn("perguntas", resultado["pendencias"])

    def test_falha_do_forte_mantem_rapido_com_alerta(self):
        agente = AgenteFalso({"rapido": _resultado(9, 23.4, 18.4, perguntas=["?"]), "forte": RuntimeError("limite")})
        resultado = _rodar(AMBIGUA, agente)
        self.assertEqual(resultado["processamento"]["camada_final"], "modelo_rapido")
        self.assertIn("MODELO_FORTE_FALHOU", [a["codigo"] for a in resultado["alertas"]])

    def test_sem_chave_mantem_estrutural(self):
        resultado = _rodar(AMBIGUA, AgenteFalso({}), chave=None)
        self.assertEqual(resultado["processamento"]["camada_final"], "estrutural")
        self.assertIn("AGENTE_SEM_CHAVE", [a["codigo"] for a in resultado["alertas"]])


if __name__ == "__main__":
    unittest.main()
