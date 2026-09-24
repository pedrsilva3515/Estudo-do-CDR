"""O custo gasto nunca se perde e a trava de orçamento age antes de estourar."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

_AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(_AQUI.parent))

from zcfreader import agente  # noqa: E402
from zcfreader.camadas import interpretar_em_camadas  # noqa: E402

FATOS = {"arquivo": "x.cdr", "candidatos": {}, "textos": {}, "pistas_regras": [], "imagem": None,
         "imagem_origem": None, "limites_cm": {"esquerda": 0, "direita": 1, "base": 0, "topo": 1}}


def _cliente_que_nunca_finaliza(custo_por_chamada: float):
    """Responde sempre pedindo ver_detalhe, cobrando um valor fixo por chamada."""
    chamadas = []

    def criar(**kwargs):
        chamadas.append(kwargs)
        chamada = SimpleNamespace(id=f"c{len(chamadas)}", function=SimpleNamespace(name="ver_detalhe", arguments="{}"),
                                  model_dump=lambda: {"id": "c", "type": "function"})
        mensagem = SimpleNamespace(content="", tool_calls=[chamada])
        uso = SimpleNamespace(cost=custo_por_chamada, prompt_tokens=1000, completion_tokens=100)
        return SimpleNamespace(choices=[SimpleNamespace(message=mensagem)], usage=uso)

    cliente = SimpleNamespace(chat=SimpleNamespace(completions=SimpleNamespace(create=criar)))
    return cliente, chamadas


class TestCustoAgente(unittest.TestCase):
    def test_trava_para_antes_da_chamada_que_estouraria_e_registra_o_gasto(self):
        cliente, chamadas = _cliente_que_nunca_finaliza(0.03)
        with mock.patch("openai.OpenAI", return_value=cliente), \
             mock.patch.object(agente, "regras_da_casa", return_value=""):
            with self.assertRaises(agente.OrcamentoExcedido) as contexto:
                agente.interpretar_com_agente(Path("x.cdr"), "k", "m", fatos=FATOS, custo_maximo_usd=0.05)
        self.assertEqual(len(chamadas), 1)  # a 2ª chamada levaria o gasto a 0,06
        self.assertAlmostEqual(contexto.exception.custo_usd, 0.03)

    def test_erro_da_api_no_meio_leva_o_custo_ja_gasto(self):
        cliente, chamadas = _cliente_que_nunca_finaliza(0.01)
        original = cliente.chat.completions.create

        def falha_na_terceira(**kwargs):
            if len(chamadas) == 2:
                raise RuntimeError("chave sem crédito")
            return original(**kwargs)

        cliente.chat.completions.create = falha_na_terceira
        with mock.patch("openai.OpenAI", return_value=cliente), \
             mock.patch.object(agente, "regras_da_casa", return_value=""):
            with self.assertRaises(RuntimeError) as contexto:
                agente.interpretar_com_agente(Path("x.cdr"), "k", "m", fatos=FATOS)
        self.assertAlmostEqual(contexto.exception.custo_usd, 0.02)

    def test_camadas_somam_o_custo_do_modelo_que_falhou(self):
        def agente_falso(caminho, chave, modelo, fatos=None, custo_maximo_usd=None):
            erro = RuntimeError("limite")
            erro.custo_usd = 0.04 if modelo == "rapido" else 0.07
            raise erro

        auditoria = {"itens": [{"candidato_id": "A01", "papel": "sem_classificacao", "estado": "revisao_necessaria",
                                "quantidade_pedido": None, "largura_cm": 1, "altura_cm": 1}]}
        with self.assertRaises(RuntimeError) as contexto:
            interpretar_em_camadas(Path("x.cdr"), "k", {"itens": []}, modelo_rapido="rapido", modelo_forte="forte",
                                   executar_agente=agente_falso, fatos={"auditoria_regional": auditoria})
        self.assertAlmostEqual(contexto.exception.custo_usd, 0.11)


if __name__ == "__main__":
    unittest.main()
