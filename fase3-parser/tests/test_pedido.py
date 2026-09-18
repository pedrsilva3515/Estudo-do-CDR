"""Testes do contrato inicial de interpretação de pedidos."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

_AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(_AQUI.parent))

from zcfreader import interpretar_nome_arquivo, parse_dimensoes, parse_material, parse_quantidade  # noqa: E402
from zcfreader.pedido import _itens_de_instrucoes_explicitas  # noqa: E402


class TestQuantidade(unittest.TestCase):
    def test_formas_usuais(self):
        for texto, esperado in (
            ("1und", 1),
            ("2 un", 2),
            ("3 unidades", 3),
            ("qtd: 5", 5),
            ("Quantidade = 12", 12),
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


if __name__ == "__main__":
    unittest.main()
