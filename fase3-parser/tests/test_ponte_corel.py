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

    def test_item_com_duas_copias_manda_a_caixa_de_cada_uma(self):
        # 2 lonas de 70x100 lado a lado: a macro seleciona as duas, mesmo com a caixa do item só na primeira.
        resultado = {"itens": [{"quantidade": {"valor": 2}, "dimensoes": {"largura_mm": 700, "altura_mm": 1000},
                                "candidatos": ["A12"], "caixa_cm": {"esquerda": 0, "direita": 70, "base": 0, "topo": 100}}]}
        candidatos = {"A12": {"largura_cm": 70, "altura_cm": 100, "caixa_cm": {"esquerda": 0, "direita": 150, "base": 0, "topo": 100},
                              "posicoes_centro_cm": [{"x": 35, "y": 50}, {"x": 115, "y": 50}]}}
        linhas = linhas_de_saida(resultado, candidatos, 1)
        self.assertEqual(linhas[1].split("\t")[7:11], ["0.000", "70.000", "0.000", "100.000"])
        self.assertEqual(linhas[2].split("\t"), ["COPIAS", "1", "0.000", "70.000", "0.000", "100.000",
                                                 "80.000", "150.000", "0.000", "100.000"])



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


class TestTextosDoPedido(unittest.TestCase):
    @staticmethod
    def _caixa(e, d, b, t):
        return {"esquerda": e, "direita": d, "base": b, "topo": t}

    @staticmethod
    def _regra(id_, largura, altura, material=None):
        return {"candidato_id": id_, "papel": "sem_classificacao", "largura_cm": largura, "altura_cm": altura,
                "quantidade_pedido": None, "quantidade_desenhada": 1, "material": material, "acabamento": None}

    def _candidato(self, e, d, b, t, centros=None):
        return {"caixa_cm": self._caixa(e, d, b, t), "largura_cm": d - e, "altura_cm": t - b,
                "posicoes_centro_cm": centros or [{"x": (e + d) / 2, "y": (b + t) / 2}],
                "quantidade_geometrica": len(centros or [1])}

    def test_titulo_de_material_vale_para_a_coluna_inteira(self):
        # "VINIL FOSCO" em cima de duas fileiras: as regras só ligam a primeira.
        from zcfreader.ponte_corel import _analisar_regras

        fatos = {
            "auditoria_regional": {"itens": [self._regra("A01", 40, 40, "adesivo fosco"), self._regra("A02", 50, 50)]},
            "candidatos": {"A01": self._candidato(0, 40, 50, 90), "A02": self._candidato(0, 50, -10, 40)},
            "textos": {"T01": {"texto": "VINIL FOSCO", "caixa_cm": self._caixa(0, 60, 95, 100)}},
        }
        itens = _analisar_regras(None, fatos)["itens"]
        self.assertEqual([i["material"]["valor"] for i in itens], ["adesivo fosco", "adesivo fosco"])

    def test_sem_material_escrito_vale_o_adesivo(self):
        from zcfreader.ponte_corel import _analisar_regras

        fatos = {"auditoria_regional": {"itens": [self._regra("A01", 40, 40)]},
                 "candidatos": {"A01": self._candidato(0, 40, 0, 40)}}
        self.assertEqual(_analisar_regras(None, fatos)["itens"][0]["material"]["valor"], "adesivo")

    def test_quantidade_em_cima_de_cada_copia_e_somada(self):
        # VINIL PRISMATICO 509: "5 UN (67X102 CM)", "12 UN (67X102 CM)" em cima de cada placa.
        from zcfreader.ponte_corel import _analisar_regras

        centros = [{"x": 33.5, "y": 51}, {"x": 103.5, "y": 51}]
        fatos = {
            "auditoria_regional": {"itens": [{**self._regra("A01", 67, 102, "adesivo"), "quantidade_desenhada": 2}]},
            "candidatos": {"A01": self._candidato(0, 137, 0, 102, centros) | {"largura_cm": 67}},
            "textos": {
                "T01": {"texto": "5 UN (67X102 CM)", "caixa_cm": self._caixa(10, 55, 103, 108)},
                "T02": {"texto": "12 UN (67X102 CM)", "caixa_cm": self._caixa(80, 125, 103, 108)},
            },
        }
        self.assertEqual(_analisar_regras(None, fatos)["itens"][0]["quantidade"]["valor"], 17)

    def test_de_cada_sem_unidade_vale_para_cada_peca(self):
        from zcfreader.ponte_corel import _analisar_regras

        fatos = {
            "auditoria_regional": {"itens": [self._regra("A01", 9, 9, "adesivo"), self._regra("A02", 11, 11, "adesivo")]},
            "candidatos": {"A01": self._candidato(0, 9, 0, 9), "A02": self._candidato(20, 31, 0, 11)},
            "textos": {"T01": {"texto": "70 DE CADA", "caixa_cm": self._caixa(5, 25, 20, 22)}},
        }
        self.assertEqual([i["quantidade"]["valor"] for i in _analisar_regras(None, fatos)["itens"]], [70, 70])

    def test_instrucao_escrita_em_curvas_nao_vira_item(self):
        # FACHADA: "VINIL BLACKOUT 65cm x 1,03m" em curvas; o OCR lê o texto em cima da faixa.
        from zcfreader.ponte_corel import _analisar_regras

        fatos = {
            "auditoria_regional": {"itens": [self._regra("A01", 65, 103, "adesivo blackout"), self._regra("A02", 114, 16)]},
            "candidatos": {"A01": self._candidato(0, 65, 0, 103), "A02": self._candidato(-25, 89, 110, 126)},
            "textos": {"T01": {"texto": "VINIL BLACKOUT 65cm x 1,03m", "caixa_cm": self._caixa(-24, 88, 110, 126)}},
        }
        self.assertEqual([i["candidatos"] for i in _analisar_regras(None, fatos)["itens"]], [["A01"]])

    def test_moldura_em_volta_da_peca_com_texto_nao_vira_item(self):
        # Placa de 105,6x106,8 dentro de um retângulo de 105,6x140,5: a peça é a placa.
        from zcfreader.ponte_corel import _analisar_regras

        fatos = {
            "auditoria_regional": {"itens": [{**self._regra("A01", 105.6, 106.8, "adesivo"), "papel": "produto_plausivel"},
                                             self._regra("A02", 105.6, 140.5)]},
            "candidatos": {"A01": self._candidato(0, 105.6, 0, 106.8), "A02": self._candidato(0, 105.6, 0, 140.5)},
        }
        self.assertEqual([i["candidatos"] for i in _analisar_regras(None, fatos)["itens"]], [["A01"]])

    def test_peca_grande_com_texto_ligado_a_um_detalhe_dentro_leva_o_texto(self):
        # Lona de 70x100 com "LONA COM VERNIZ" ligado só ao bitmap de 33x30 dentro dela:
        # o item é a lona, com o material do texto (revisão do pedido "4 - laminação").
        from zcfreader.ponte_corel import _analisar_regras

        fatos = {
            "auditoria_regional": {"itens": [{**self._regra("A01", 33.6, 30.2, "lona"), "papel": "produto_plausivel"},
                                             self._regra("A02", 70, 100)]},
            "candidatos": {"A01": self._candidato(0, 33.6, 0, 30.2), "A02": self._candidato(0, 70, 0, 100)},
        }
        itens = _analisar_regras(None, fatos)["itens"]
        self.assertEqual([i["candidatos"] for i in itens], [["A02"]])
        self.assertEqual(itens[0]["material"]["valor"], "lona")
        self.assertEqual(itens[0]["situacao"], "a confirmar")

    def test_pasta_em_volta_de_pecas_diferentes_sai_da_lista(self):
        # Grupo de 60x40 com o adesivo de 30x40 e a placa de 30x20 lado a lado: as peças ficam.
        from zcfreader.ponte_corel import _pastas_em_volta

        candidatos = {
            "A01": self._candidato(0, 60, 0, 40),
            "A02": {**self._candidato(0, 30, 0, 40), "pai_id": "A01"},
            "A03": {**self._candidato(30, 60, 0, 20), "pai_id": "A01"},
        }
        itens = [{"candidatos": ["A01"], "situacao": "sem texto - confirmar"},
                 {"candidatos": ["A02"], "situacao": "a confirmar"}]
        self.assertEqual(sorted(i["candidatos"][0] for i in _pastas_em_volta(itens, candidatos)), ["A02", "A03"])

    def test_painel_com_quadros_iguais_continua_uma_peca(self):
        # Adesivo de 50x200 com 3 fotos de 43x64 empilhadas: é um painel só.
        from zcfreader.ponte_corel import _pastas_em_volta

        candidatos = {"A01": self._candidato(0, 50, 0, 200)}
        for n, base in enumerate((2, 68, 134), 2):
            candidatos[f"A0{n}"] = {**self._candidato(3, 46, base, base + 64), "pai_id": "A01"}
        itens = [{"candidatos": ["A01"], "situacao": "a confirmar"}]
        self.assertEqual(_pastas_em_volta(itens, candidatos), itens)

    def test_pedido_so_escrito_com_medida_vira_item(self):
        # "ads recortados 4x4 100und" sem peça de 4x4 desenhada.
        from zcfreader.ponte_corel import _itens_pela_medida_escrita

        itens = [{"dimensoes": {"largura_mm": 300, "altura_mm": 400}, "candidatos": ["A01"]}]
        fatos = {"candidatos": {"A01": self._candidato(0, 30, 0, 40)},
                 "textos": {"T01": {"texto": "ads recortados 4x4 100und",
                                    "caixa_cm": {"esquerda": 40, "direita": 60, "base": 0, "topo": 2}}}}
        _itens_pela_medida_escrita(itens, fatos)
        self.assertEqual(len(itens), 2)
        self.assertEqual(itens[1]["quantidade"]["valor"], 100)
        self.assertEqual((itens[1]["dimensoes"]["largura_mm"], itens[1]["dimensoes"]["altura_mm"]), (40, 40))
        self.assertEqual(itens[1]["material"]["valor"], "adesivo")

    def test_medida_aproximada_sem_quantidade_nao_vira_item(self):
        # "50X78 CM VINIL" ao lado da peça de 45x80: é a medida aproximada dela.
        from zcfreader.ponte_corel import _itens_pela_medida_escrita

        itens = [{"dimensoes": {"largura_mm": 451, "altura_mm": 807}, "candidatos": ["A01"]}]
        fatos = {"candidatos": {"A01": self._candidato(0, 45.1, 0, 80.7)},
                 "textos": {"T01": {"texto": "50X78 CM VINIL", "caixa_cm": {"esquerda": 0, "direita": 20, "base": 81, "topo": 83}}}}
        _itens_pela_medida_escrita(itens, fatos)
        self.assertEqual(len(itens), 1)

    def test_medida_e_material_escritos_sem_peca_parecida_vira_item(self):
        # "50x50 papel outdoor" e nenhuma peça desenhada perto dessa medida (lona repiteco).
        from zcfreader.ponte_corel import _itens_pela_medida_escrita

        itens = [{"dimensoes": {"largura_mm": 700, "altura_mm": 700}, "candidatos": ["A01"]}]
        fatos = {"candidatos": {"A01": self._candidato(0, 70, 0, 70)},
                 "textos": {"T01": {"texto": "50x50 papel outdoor", "caixa_cm": self._caixa(80, 100, 0, 2)}}}
        _itens_pela_medida_escrita(itens, fatos)
        self.assertEqual(len(itens), 2)
        self.assertEqual(itens[1]["quantidade"]["valor"], 1)
        self.assertEqual(itens[1]["material"]["valor"], "papel outdoor")

    @staticmethod
    def _item(id_, quantidade, origem):
        return {"candidatos": [id_], "quantidade": {"valor": quantidade, "origem": origem}, "origem_campos": {}}

    def test_quantidade_entre_duas_pecas_fica_com_a_que_nao_tem_a_sua(self):
        # "15und" entre duas peças; a de baixo já tem o seu "15und" embaixo (emanuel).
        from zcfreader.ponte_corel import _quantidade_escrita

        itens = [self._item("A01", 1, "desenho"), self._item("A02", 1, "desenho")]
        fatos = {
            "candidatos": {"A01": self._candidato(0, 10, 8, 12), "A02": self._candidato(0, 4, 2.5, 6.5)},
            "textos": {"T01": {"texto": "15und", "caixa_cm": self._caixa(1, 3, 6.9, 7.6)},
                       "T02": {"texto": "15und", "caixa_cm": self._caixa(1, 3, 1.7, 2.2)}},
        }
        _quantidade_escrita(itens, fatos)
        self.assertEqual([i["quantidade"]["valor"] for i in itens], [15, 15])

    def test_peca_com_quantidade_de_outra_fica_com_a_sua(self):
        # As regras deram "50und" às duas peças; a grande tem o "2und" ao lado (refilado).
        from zcfreader.ponte_corel import _quantidade_escrita

        itens = [self._item("A01", 50, "texto"), self._item("A02", 50, "texto")]
        fatos = {
            "candidatos": {"A01": self._candidato(-14.6, 15.1, -26.9, -5.9), "A02": self._candidato(-9, 9, -3.2, 3.2)},
            "textos": {"T01": {"texto": "50und", "caixa_cm": self._caixa(-17.2, -11.3, -0.5, 1.1)},
                       "T02": {"texto": "2und", "caixa_cm": self._caixa(-21.2, -16.5, -18.4, -16.8)}},
        }
        _quantidade_escrita(itens, fatos)
        self.assertEqual([i["quantidade"]["valor"] for i in itens], [2, 50])

    def test_faixa_repetida_dentro_de_pecas_diferentes_sai_da_lista(self):
        # A mesma faixa de 40,5x8,5 dentro da arte de 40,5x66 e da de 40,5x55 (ADESIVO TRANSPARENTE).
        from zcfreader.ponte_corel import _juntar_partes_na_peca

        faixa = self._candidato(0, 40.5, 50, 58.5, centros=[{"x": 20.25, "y": 54.25}, {"x": 70.25, "y": 54.25}])
        candidatos = {"A01": self._candidato(0, 40.5, 0, 66), "A02": self._candidato(50, 90.5, 5, 60), "A03": faixa}
        itens = [{"candidatos": ["A01"], "situacao": "a confirmar"}, {"candidatos": ["A02"], "situacao": "a confirmar"},
                 {"candidatos": ["A03"], "situacao": "sem texto - confirmar"}]
        self.assertEqual([i["candidatos"] for i in _juntar_partes_na_peca(itens, candidatos)], [["A01"], ["A02"]])

    def test_moldura_repetida_em_volta_das_fotos_e_a_peca(self):
        # 3 retângulos de 70x50, cada um com uma foto de ~67x46 dentro (IMPRESSÃO ADESIVO).
        from zcfreader.ponte_corel import _pecas_pela_moldura

        moldura = self._candidato(0, 70, 0, 150, centros=[{"x": 35, "y": 25}, {"x": 35, "y": 75}, {"x": 35, "y": 125}])
        moldura.update(largura_cm=70, altura_cm=50)
        candidatos = {"A01": moldura, "A03": self._candidato(1.4, 68.6, 52, 98), "A05": self._candidato(2, 68, 101.5, 148.3)}
        itens = [{"candidatos": ["A03"], "quantidade": {"valor": 1, "origem": "desenho"}, "situacao": "sem texto - confirmar"},
                 {"candidatos": ["A05"], "quantidade": {"valor": 1, "origem": "desenho"}, "situacao": "a confirmar"}]
        novos = _pecas_pela_moldura(itens, candidatos)
        self.assertEqual([(i["candidatos"], i["quantidade"]["valor"]) for i in novos], [(["A01"], 3)])
        self.assertEqual(novos[0]["situacao"], "a confirmar")

    def test_fundo_coberto_por_copias_da_arte_vira_as_copias(self):
        # Fundo de 21x30 com 2 adesivos de 21x15 em cima (leitoso sem recorte).
        from zcfreader.ponte_corel import _pecas_pela_moldura

        arte = self._candidato(0, 21, 0, 30, centros=[{"x": 10.5, "y": 7.5}, {"x": 10.5, "y": 22.5}])
        arte.update(largura_cm=21, altura_cm=15, tipos=["bitmap"])
        candidatos = {"A01": {**self._candidato(0, 21, 0, 30), "tipos": ["retangulo"]}, "A02": arte}
        itens = [{"candidatos": ["A01"], "quantidade": {"valor": 1, "origem": "desenho"}, "situacao": "sem texto - confirmar"}]
        self.assertEqual([(i["candidatos"], i["quantidade"]["valor"]) for i in _pecas_pela_moldura(itens, candidatos)],
                         [(["A02"], 2)])

    def test_fundo_coberto_por_molduras_com_artes_diferentes_continua(self):
        # 4 molduras de 30x20 com artes diferentes no fundo de 60x40: grade montada (lixeiras).
        from zcfreader.ponte_corel import _pecas_pela_moldura

        molduras = self._candidato(0, 60, 0, 40, centros=[{"x": 15, "y": 10}, {"x": 45, "y": 10}, {"x": 15, "y": 30}, {"x": 45, "y": 30}])
        molduras.update(largura_cm=30, altura_cm=20, tipos=["retangulo"])
        candidatos = {"A02": {**self._candidato(0, 60, 0, 40), "tipos": ["retangulo"]}, "A01": molduras}
        itens = [{"candidatos": ["A02"], "quantidade": {"valor": 1, "origem": "desenho"}, "situacao": "sem texto - confirmar"}]
        self.assertEqual([i["candidatos"] for i in _pecas_pela_moldura(itens, candidatos)], [["A02"]])

    def test_de_cada_vale_para_as_vizinhas_iguais_sem_texto(self):
        # "15 UNI DE CADA" ligado à fileira de cima; a de baixo, encostada, é o mesmo pedido (JOSES FAZENDA).
        from zcfreader.ponte_corel import _de_cada_nos_vizinhos

        candidatos = {"A01": self._candidato(0, 6, 10, 16), "A02": self._candidato(0, 6, 1.7, 7.7),
                      "A03": self._candidato(40, 46, 10, 16)}
        itens = [{"candidatos": ["A01"], "quantidade": {"valor": 15, "origem": "texto"}, "acabamento": {"valor": None}},
                 {"candidatos": ["A02"], "quantidade": {"valor": 1, "origem": "desenho"}, "acabamento": {"valor": "recorte"}},
                 {"candidatos": ["A03"], "quantidade": {"valor": 1, "origem": "desenho"}}]
        _de_cada_nos_vizinhos(itens, candidatos, {15})
        self.assertEqual([i["quantidade"]["valor"] for i in itens], [15, 15, 1])
        self.assertIsNone(itens[1]["acabamento"]["valor"])

    def test_fundo_e_arte_no_mesmo_lugar_com_texto_sao_uma_peca(self):
        # O fundo de 111x212 e a arte de 111x211,9 em cima, os dois ligados ao texto (ADESIVO PERFURADO).
        from zcfreader.ponte_corel import _analisar_regras

        fatos = {
            "auditoria_regional": {"itens": [{**self._regra("A01", 111, 212, "adesivo perfurado"), "papel": "produto_plausivel"},
                                             {**self._regra("A02", 111, 211.9, "adesivo perfurado"), "papel": "produto_plausivel"}]},
            "candidatos": {"A01": self._candidato(0, 111, 0, 212), "A02": self._candidato(0, 111, 0.1, 212)},
        }
        self.assertEqual([i["candidatos"] for i in _analisar_regras(None, fatos)["itens"]], [["A01"]])

    def test_mesma_peca_em_outra_camada_nao_vira_item_a_mais(self):
        # Placa de 51x51 com o fundo de 50x50 dentro: um item só.
        from zcfreader.ponte_corel import _analisar_regras

        fatos = {
            "auditoria_regional": {"itens": [self._regra("A01", 51, 51, "adesivo"), self._regra("A02", 50, 50)]},
            "candidatos": {"A01": self._candidato(0, 51, 0, 51), "A02": self._candidato(0.5, 50.5, 0.5, 50.5)},
        }
        self.assertEqual([i["candidatos"] for i in _analisar_regras(None, fatos)["itens"]], [["A01"]])


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

    def test_grade_com_quantidade_escrita_por_peca_vira_quantidade_de_grades(self):
        # "15 UNI DE CADA" sobre a grade de 8 adesivos: 120 peças = 15 grades (JOSES FAZENDA).
        from zcfreader.ponte_corel import separar_ocorrencias

        candidatos = {"A01": self._candidato(4, 2, 7.0)}
        item = {**self._item("A01", 120, 7.0), "quantidade": {"valor": 120, "origem": "texto"}}
        itens = separar_ocorrencias({"itens": [item]}, candidatos)["itens"]
        self.assertEqual(itens[0]["grade"]["pecas"], 8)
        self.assertEqual(itens[0]["quantidade"]["valor"], 15)

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
