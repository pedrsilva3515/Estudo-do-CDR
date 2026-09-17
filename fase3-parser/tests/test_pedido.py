"""Testes do contrato inicial de interpretação de pedidos."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(_AQUI.parent))

from zcfreader import parse_material, parse_quantidade  # noqa: E402


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


if __name__ == "__main__":
    unittest.main()
