"""Nomes do Portal Flow para material e acabamento."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from zcfreader.catalogo_portal import acabamentos_portal, material_portal  # noqa: E402
from zcfreader.ponte_corel import aplicar_catalogo  # noqa: E402


class TestMaterialPortal(unittest.TestCase):
    def test_material_dito_no_pedido(self):
        for texto, esperado in (
            ("adesivo branco fosco blackout", "Adesivo Fosco Blackout"),
            ("ADESIVO PERFURADO", "Adesivo Perfurado"),
            ("adesivo trasnparente", "Adesivo Transparente"),
            ("Lona fosca com ilhoes", "Lona Fosca"),
            ("Papel outdoor", "Papel Outdoor"),
            ("Material do cliente adesivo", "Material do Cliente Adesivo"),
        ):
            with self.subTest(texto=texto):
                self.assertEqual(material_portal(texto), (esperado, "arquivo"))

    def test_generico_vira_padrao_da_grafica(self):
        self.assertEqual(material_portal("adesivo"), ("Adesivo Leitoso Interm.", "padrao_grafica"))
        self.assertEqual(material_portal("lona", "banner"), ("Lona Brilho 440g", "padrao_grafica"))

    def test_tipo_fora_do_catalogo_fica_para_o_operador(self):
        self.assertEqual(material_portal("adesivo super cola"), (None, ""))
        self.assertEqual(material_portal("Vinil Brilhoso"), (None, ""))

    def test_acabamentos(self):
        self.assertEqual(acabamentos_portal("lona", "banner"), ["Banner"])
        self.assertEqual(acabamentos_portal("adesivo", "recorte especial"), ["Recorte"])
        self.assertEqual(acabamentos_portal("adesivo leitoso", "somente recorte"), ["Somente Recorte"])
        self.assertEqual(acabamentos_portal("lona", "banner + ilhós"), ["Banner", "Ilhós"])
        self.assertEqual(acabamentos_portal("adesivo", "sem recorte"), [])

    def test_aplicar_guarda_o_texto_lido(self):
        resultado = {"itens": [{"material": {"valor": "adesivo"}, "acabamento": {"valor": "recortado"}}]}
        item = aplicar_catalogo(resultado)["itens"][0]
        self.assertEqual(item["material"], {"valor": "Adesivo Leitoso Interm.", "texto_lido": "adesivo"})
        self.assertEqual(item["origem_campos"], {"material": "padrao_grafica"})
        self.assertEqual(item["acabamento"]["valor"], "Recorte")


if __name__ == "__main__":
    unittest.main()
