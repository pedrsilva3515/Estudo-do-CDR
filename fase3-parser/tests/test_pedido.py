"""Testes do contrato inicial de interpretação de pedidos."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

_AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(_AQUI.parent))

from zcfreader import interpretar_nome_arquivo, parse_dimensoes, parse_material, parse_quantidade  # noqa: E402
from zcfreader.pedido import _associar_um_a_um, _itens_de_instrucoes_explicitas  # noqa: E402


class TestQuantidade(unittest.TestCase):
    def test_formas_usuais(self):
        for texto, esperado in (
            ("1und", 1),
            ("2 un", 2),
            ("3 unidades", 3),
            ("qtd: 5", 5),
            ("Quantidade = 12", 12),
            ("30 UNI DE CADA", 30),
            ("60 UNI", 60),
        ):
            with self.subTest(texto=texto):
                self.assertEqual(parse_quantidade(texto), (esperado, "unidade"))

    def test_numero_sem_contexto_nao_e_quantidade(self):
        self.assertIsNone(parse_quantidade("Banner 90x120 cm"))


class TestMaterial(unittest.TestCase):
    def test_material_e_acabamento(self):
        self.assertEqual(
            parse_material("adesivo transparente recortado\n15 unid"),
            {"material": "adesivo transparente", "acabamento": "recortado"},
        )
        self.assertEqual(
            parse_material("TODOS ADESIVO NORMAL"),
            {"material": "adesivo normal", "acabamento": None},
        )
        self.assertEqual(
            parse_material("adesivo leitoso recortados"),
            {"material": "adesivo leitoso", "acabamento": "recortado"},
        )

    def test_texto_sem_material(self):
        self.assertIsNone(parse_material("14und"))

    def test_vinil_transparente_no_nome(self):
        self.assertEqual(
            parse_material("VINIL TRANSPARENTE - ANMG 014"),
            {"material": "adesivo transparente", "acabamento": None},
        )

    def test_materiais_adicionais_e_documento_misto(self):
        self.assertEqual(parse_material("VINIL FOSCO")["material"], "adesivo fosco")
        self.assertEqual(parse_material("LONA COM ILHOS")["material"], "lona")
        self.assertIsNone(parse_material("banner e adesivo sem recorte"))


class TestDimensoes(unittest.TestCase):
    def test_quantidade_com_dimensoes_decimais(self):
        resultado = parse_dimensoes("9 UN (23,4X18,4 CM)")
        self.assertEqual(resultado["largura_mm"], 234)
        self.assertEqual(resultado["altura_mm"], 184)

    def test_instrucao_explicita_vira_um_unico_item_autoritativo(self):
        origem = {
            "valor": 9, "unidade": "unidade", "texto_origem": "9 UN (23,4X18,4 CM)",
            "dimensoes": parse_dimensoes("9 UN (23,4X18,4 CM)"),
            "objeto": SimpleNamespace(caixa=object()),
        }
        itens = _itens_de_instrucoes_explicitas([origem])
        self.assertEqual(len(itens), 1)
        self.assertEqual(itens[0]["quantidade"]["valor"], 9)
        self.assertEqual(itens[0]["dimensoes"]["largura_mm"], 234)
        self.assertEqual(itens[0]["dimensoes"]["altura_mm"], 184)
        self.assertEqual(itens[0]["dimensoes"]["fonte"], "texto_cdr")

    def test_sem_unidade_exige_contexto_de_quantidade(self):
        self.assertEqual(parse_dimensoes("4 UN (46,5 X 9)")["largura_mm"], 465)
        self.assertIsNone(parse_dimensoes("telefone 46,5 x 9"))

    def test_de_cada_e_associado_a_todas_as_pecas_da_regiao(self):
        def caixa(esquerda, base, direita, topo):
            return SimpleNamespace(esquerda=esquerda, base=base, direita=direita, topo=topo)
        candidatos = [
            {"caixa": caixa(-390_0000, -150_0000, -110_0000, 180_0000)},
            {"caixa": caixa(-100_0000, -760_0000, 140_0000, 180_0000)},
            {"caixa": caixa(300_0000, -70_0000, 500_0000, 180_0000)},
        ]
        referencias = [{
            "texto_origem": "30 UNI DE CADA", "objeto": SimpleNamespace(
                caixa=caixa(-395_0000, 265_0000, 125_0000, 315_0000)
            ),
        }]
        associacoes = _associar_um_a_um(candidatos, referencias)
        self.assertEqual(associacoes, {0: 0, 1: 0})


class TestNomeArquivo(unittest.TestCase):
    def test_sufixo_de_copia_nao_vira_quantidade(self):
        resultado = interpretar_nome_arquivo("guanarabara iza ads (1).cdr")
        self.assertIsNone(resultado["quantidade"])

    def test_material_e_sem_recorte(self):
        resultado = interpretar_nome_arquivo("adesivos BK set - sem rec.cdr")
        self.assertEqual(resultado["material"]["material"], "adesivo")
        self.assertEqual(resultado["material"]["acabamento"], "sem recorte")

    def test_quantidade_e_dimensao_explicitas(self):
        resultado = interpretar_nome_arquivo("20und adesivo 30x40cm.cdr")
        self.assertEqual(resultado["quantidade"], (20, "unidade"))
        self.assertEqual(resultado["dimensoes"]["largura_mm"], 300)
        self.assertEqual(resultado["dimensoes"]["altura_mm"], 400)

    def test_dimensao_em_metros_sem_unidade_no_nome(self):
        resultado = interpretar_nome_arquivo("ADESIVO TRANSPARENTE 1,00X0,55.cdr")
        self.assertEqual(resultado["dimensoes"]["largura_mm"], 1000)
        self.assertEqual(resultado["dimensoes"]["altura_mm"], 550)


if __name__ == "__main__":
    unittest.main()
