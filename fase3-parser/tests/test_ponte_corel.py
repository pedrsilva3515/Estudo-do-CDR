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
        self.assertEqual(len(campos), 14)
        self.assertEqual(campos[12:], ["arquivo", "arquivo"])
        self.assertEqual(campos[:7], ["ITEM", "1", "6", "40.000", "30.000", "adesivo fosco", ""])
        self.assertEqual(campos[7:11], ["-47.100", "-7.100", "-20.200", "9.800"])
        self.assertEqual(linhas[2], "PERGUNTA\tQual o acabamento?")

    def test_item_sem_posicao_tem_coordenadas_vazias(self):
        resultado = {"itens": [{"quantidade": {"valor": 1}, "dimensoes": {"largura_mm": 100, "altura_mm": 100}}]}
        campos = linhas_de_saida(resultado, {}, 1)[1].split("\t")
        self.assertEqual(campos[7:11], ["", "", "", ""])

    def test_quantidade_padrao_sai_na_ultima_coluna(self):
        resultado = {"itens": [{"quantidade": {"valor": 1}, "dimensoes": {"largura_mm": 100, "altura_mm": 100},
                                "origem_campos": {"quantidade": "padrao_grafica"}}]}
        self.assertEqual(linhas_de_saida(resultado, {}, 1)[1].split("\t")[13], "padrao_grafica")



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

    def test_folhas_de_um_painel_nao_viram_item_a_mais(self):
        from zcfreader.ponte_corel import _analisar_regras

        painel = {"esquerda": 0, "direita": 133.4, "base": 0, "topo": 200}
        regra = lambda id_, l, a: {"candidato_id": id_, "papel": "sem_classificacao", "largura_cm": l, "altura_cm": a,
                                   "quantidade_pedido": None, "quantidade_desenhada": 1, "material": None, "acabamento": None}
        fatos = {"auditoria_regional": {"itens": [regra("A01", 133.4, 200), regra("A02", 33.35, 50)]},
                 "candidatos": {"A01": {"caixa_cm": painel, "quantidade_geometrica": 1},
                                "A02": {"caixa_cm": dict(painel), "quantidade_geometrica": 12}}}
        resultado = _analisar_regras(None, fatos)
        self.assertEqual([i["candidatos"] for i in resultado["itens"]], [["A01"]])

    def test_material_vem_do_nome_do_arquivo_como_no_leitor(self):
        from zcfreader.ponte_corel import _analisar_regras

        fatos = {"auditoria_regional": {"itens": [{
            "candidato_id": "A01", "papel": "sem_classificacao", "largura_cm": 125, "altura_cm": 40,
            "quantidade_pedido": None, "quantidade_desenhada": 1, "material": None, "acabamento": None,
        }]}}
        resultado = _analisar_regras(Path("arte gabriel lava jato adesivo perfurado.cdr"), fatos)
        self.assertEqual(resultado["itens"][0]["material"]["valor"], "adesivo perfurado")
        self.assertEqual(resultado["itens"][0]["dimensoes"]["largura_mm"], 1250)


class TestMedidaDaFaca(unittest.TestCase):
    @staticmethod
    def _caixa(e, d, b, t):
        return {"esquerda": e, "direita": d, "base": b, "topo": t}

    def _candidato(self, e, d, b, t, tipos):
        return {"caixa_cm": self._caixa(e, d, b, t), "largura_cm": d - e, "altura_cm": t - b, "tipos": tipos}

    def test_peca_com_faca_em_volta_fica_com_a_medida_da_faca_e_sem_recorte_inventado(self):
        from zcfreader.ponte_corel import aplicar_medida_da_faca

        candidatos = {
            "A07": self._candidato(0, 27, 0, 27, ["bitmap"]),
            "A03": self._candidato(-0.8, 27.7, -0.1, 27.8, ["curva"]),     # faca: borda branca
            "A90": self._candidato(-20, 80, -20, 80, ["curva"]),           # moldura grande: não é faca
        }
        item = {"quantidade": {"valor": 1}, "dimensoes": {"largura_mm": 270, "altura_mm": 270},
                "acabamento": {"valor": None}, "candidatos": ["A07"]}
        faca_listada = {"quantidade": {"valor": 1}, "dimensoes": {"largura_mm": 285, "altura_mm": 279},
                        "candidatos": ["A03"], "situacao": "sem texto - confirmar"}
        itens = aplicar_medida_da_faca({"itens": [item, faca_listada]}, candidatos)["itens"]
        self.assertEqual(len(itens), 1)  # a faca não fica como item a mais
        self.assertEqual((itens[0]["dimensoes"]["largura_mm"], itens[0]["dimensoes"]["altura_mm"]), (285.0, 279.0))
        self.assertEqual(itens[0]["faca"]["arte_cm"], [27.0, 27.0])
        self.assertIsNone(itens[0]["acabamento"]["valor"])

    def test_sem_faca_a_medida_nao_muda(self):
        from zcfreader.ponte_corel import aplicar_medida_da_faca

        candidatos = {"A01": self._candidato(0, 50, 0, 30, ["bitmap"]),
                      "A02": self._candidato(0, 50, 0, 30, ["curva"])}  # mesma caixa: não há borda
        item = {"dimensoes": {"largura_mm": 500, "altura_mm": 300}, "candidatos": ["A01"]}
        itens = aplicar_medida_da_faca({"itens": [item]}, candidatos)["itens"]
        self.assertEqual(itens[0]["dimensoes"]["largura_mm"], 500)
        self.assertNotIn("faca", itens[0])


class TestGradeMontada(unittest.TestCase):
    @staticmethod
    def _candidato(colunas: int, linhas: int, lado: float = 5.0) -> dict:
        posicoes = [{"x": c * lado + lado / 2, "y": l * lado + lado / 2} for c in range(colunas) for l in range(linhas)]
        return {"largura_cm": lado, "altura_cm": lado, "posicoes_centro_cm": posicoes, "artes": "iguais",
                "caixa_cm": {"esquerda": 0, "direita": colunas * lado, "base": 0, "topo": linhas * lado}}

    @staticmethod
    def _item(id_: str, quantidade: int, lado: float = 5.0) -> dict:
        return {"quantidade": {"valor": quantidade}, "dimensoes": {"largura_mm": lado * 10, "altura_mm": lado * 10},
                "material": {"valor": "adesivo"}, "acabamento": {"valor": "recorte"}, "candidatos": [id_]}

    def test_muitas_pecas_desenhadas_viram_1_grade_e_camada_repetida_some(self):
        from zcfreader.ponte_corel import separar_ocorrencias

        candidatos = {"A01": self._candidato(10, 9), "A02": self._candidato(10, 9),
                      "A03": {"largura_cm": 50, "altura_cm": 45, "caixa_cm": {"esquerda": 0, "direita": 50, "base": 0, "topo": 45}}}
        resultado = {"itens": [self._item("A01", 90), {**self._item("A03", 1, 50), "dimensoes": {"largura_mm": 500, "altura_mm": 450}},
                               self._item("A02", 90)]}
        itens = separar_ocorrencias(resultado, candidatos)["itens"]
        self.assertEqual(len(itens), 1)
        self.assertEqual(itens[0]["quantidade"]["valor"], 1)
        self.assertEqual((itens[0]["dimensoes"]["largura_mm"], itens[0]["dimensoes"]["altura_mm"]), (500, 450))
        self.assertEqual(itens[0]["grade"]["pecas"], 90)

    def test_poucas_pecas_grandes_continuam_com_quantidade(self):
        from zcfreader.ponte_corel import separar_ocorrencias

        candidatos = {"A01": self._candidato(1, 5, 20.0)}
        itens = separar_ocorrencias({"itens": [self._item("A01", 5, 20.0)]}, candidatos)["itens"]
        self.assertEqual([i["quantidade"]["valor"] for i in itens], [5])
        self.assertNotIn("grade", itens[0])

    def test_seis_artes_grandes_nao_sao_grade(self):
        from zcfreader.ponte_corel import separar_ocorrencias

        candidatos = {"A01": {**self._candidato(3, 2, 20.0), "artes": "distintas"}}
        itens = separar_ocorrencias({"itens": [self._item("A01", 6, 20.0)]}, candidatos)["itens"]
        self.assertEqual([i["quantidade"]["valor"] for i in itens], [1] * 6)


if __name__ == "__main__":
    unittest.main()
