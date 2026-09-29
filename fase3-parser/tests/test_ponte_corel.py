"""Formato de texto que a macro do CorelDRAW lê."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from zcfreader.ponte_corel import linhas_de_saida  # noqa: E402


class TestLinhasDeSaida(unittest.TestCase):
    def test_item_com_caixa_do_candidato(self):
        resultado = {
            "processamento": {"camada_final": "regras", "custo_usd": 0},
            "itens": [{
                "quantidade": {"valor": 6}, "dimensoes": {"largura_mm": 400, "altura_mm": 300},
                "material": {"valor": "adesivo\tfosco"}, "acabamento": {"valor": None}, "candidatos": ["A05"],
            }],
            "perguntas_operador": [{"pergunta": "Qual o acabamento?"}],
        }
        candidatos = {"A05": {"caixa_cm": {"esquerda": -47.1, "direita": -7.1, "base": -20.2, "topo": 9.8}}}
        linhas = linhas_de_saida(resultado, candidatos, 4.25)
        self.assertEqual(linhas[0], "INFO\tregras\t4.2\t0.0000")
        campos = linhas[1].split("\t")
        self.assertEqual(len(campos), 13)
        self.assertEqual(campos[12], "arquivo")
        self.assertEqual(campos[:7], ["ITEM", "1", "6", "40.000", "30.000", "adesivo fosco", ""])
        self.assertEqual(campos[7:11], ["-47.100", "-7.100", "-20.200", "9.800"])
        self.assertEqual(linhas[2], "PERGUNTA\tQual o acabamento?")

    def test_item_sem_posicao_tem_coordenadas_vazias(self):
        resultado = {"itens": [{"quantidade": {"valor": 1}, "dimensoes": {"largura_mm": 100, "altura_mm": 100}}]}
        campos = linhas_de_saida(resultado, {}, 1)[1].split("\t")
        self.assertEqual(campos[7:11], ["", "", "", ""])



class TestCorrecao(unittest.TestCase):
    ORIGINAL = {
        "processamento": {"fluxo": "macro_corel", "camada_final": "regras"},
        "itens": [
            {"quantidade": {"valor": 6}, "dimensoes": {"largura_mm": 400, "altura_mm": 300},
             "material": {"valor": "adesivo"}, "acabamento": {"valor": None}, "candidatos": ["A05"]},
            {"quantidade": {"valor": 1}, "dimensoes": {"largura_mm": 10, "altura_mm": 10},
             "material": {"valor": None}, "acabamento": {"valor": None}, "candidatos": ["A01"]},
        ],
    }

    def test_editar_trocar_peca_remover_e_adicionar(self):
        from zcfreader.ponte_corel import resultado_corrigido

        linhas = [
            "OBS\tpedido de teste",
            # item 1 mantido, acabamento que faltou no pedido
            "ITEM\t1\t6\t40\t30\tadesivo\t\tarquivo\tarquivo\tfaltou_no_pedido\tanalise\t-47.1\t-7.1\t-20.2\t9.8\t\t",
            # item 2 removido (não aparece); item novo escolhido no Corel
            "ITEM\t0\t3\t20.05\t19.95\tadesivo fosco\t\tarquivo\tpadrao_grafica\tarquivo\tcorel\t27\t47\t-15\t5\tnão tinha sido lido\t123:3;124:7",
        ]
        correto, observacao = resultado_corrigido(self.ORIGINAL, linhas)
        self.assertEqual(observacao, "pedido de teste")
        self.assertEqual(len(correto["itens"]), 2)
        primeiro, novo = correto["itens"]
        self.assertEqual(primeiro["origem_campos"], {"acabamento": "faltou_no_pedido"})
        self.assertEqual(primeiro["dimensoes"]["largura_mm"], 400)
        self.assertEqual(novo["quantidade"]["valor"], 3)
        self.assertEqual(novo["dimensoes"]["largura_mm"], 200.5)
        self.assertEqual(novo["material"]["valor"], "adesivo fosco")
        self.assertEqual(novo["origem_campos"], {"material": "padrao_grafica"})
        self.assertEqual(novo["peca_correta"]["objetos_corel"], ["123:3", "124:7"])
        self.assertEqual(novo["observacao_operador"], "não tinha sido lido")

    def test_salvar_gera_pacote(self):
        import json
        import tempfile
        from unittest import mock
        from zipfile import ZipFile

        from zcfreader import ponte_corel

        with tempfile.TemporaryDirectory() as pasta:
            pasta = Path(pasta)
            cdr = pasta / "pedido.cdr"
            cdr.write_bytes(b"conteudo")
            original = pasta / "resultado.txt.json"
            original.write_text(json.dumps({"arquivo": str(cdr), "resultado": self.ORIGINAL}), encoding="utf-8")
            correcao = pasta / "correcao.txt"
            correcao.write_text(
                f"ORIGINAL\t{original}\r\n"
                "ITEM\t1\t6\t40\t30\tadesivo\t\tarquivo\tarquivo\tarquivo\tanalise\t-47.1\t-7.1\t-20.2\t9.8\t\t\r\n",
                encoding="cp1252",
            )
            with mock.patch("zcfreader.relatorios.pasta_relatorios", return_value=pasta / "Relatorios"), \
                 mock.patch("zcfreader.relatorios.extrair_preview", return_value=None), \
                 mock.patch("zcfreader.configuracao.carregar_configuracao", return_value={"incluir_cdr_diagnostico": True}):
                ponte_corel.main([str(cdr), str(correcao), "salvar"])
            resposta = (pasta / "correcao.txt.ok").read_text(encoding="cp1252").split("\t")
            self.assertEqual(resposta[0], "OK", resposta)
            with ZipFile(resposta[1].strip()) as pacote:
                correto = json.loads(pacote.read("resultado-correto.json"))
                self.assertIn("arquivo-original/pedido.cdr", pacote.namelist())
            self.assertEqual(len(correto["itens"]), 1)


class TestPecasSemTexto(unittest.TestCase):
    def test_modo_sem_ia_lista_pecas_sem_texto_de_3_cm(self):
        from zcfreader.ponte_corel import _analisar_regras

        def regra(id_, papel, largura, altura, material=None):
            return {"candidato_id": id_, "papel": papel, "largura_cm": largura, "altura_cm": altura,
                    "quantidade_pedido": None, "quantidade_desenhada": 1, "material": material, "acabamento": None}

        fatos = {"auditoria_regional": {"itens": [
            regra("A01", "produto_plausivel", 40, 30, "adesivo"),
            regra("A02", "sem_classificacao", 20, 28),
            regra("A03", "sem_classificacao", 2, 0.8),        # etiqueta pequena: fica de fora
            regra("A04", "detalhe_interno_do_produto", 10, 10),
        ]}}
        resultado = _analisar_regras(None, fatos)
        self.assertEqual([i["candidatos"] for i in resultado["itens"]], [["A01"], ["A02"]])
        self.assertEqual([i["situacao"] for i in resultado["itens"]], ["a confirmar", "sem texto - confirmar"])


if __name__ == "__main__":
    unittest.main()
