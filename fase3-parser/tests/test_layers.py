"""Testes de propriedades estruturais de layers."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_AQUI = Path(__file__).resolve().parent
_RAIZ_PROJETO = _AQUI.parents[1]
sys.path.insert(0, str(_AQUI.parent))

from zcfreader import abrir_cdr  # noqa: E402

CASOS = _RAIZ_PROJETO / "casos-de-teste"


def _layer_estudo(nome: str):
    with abrir_cdr(CASOS / nome) as doc:
        camada = next(c for c in doc.camadas() if c.nome == "LayerEstudo")
        objeto = next(o for o in doc.estrutura() if o.tipo == "obj")
    return camada, objeto


class TestLayers(unittest.TestCase):
    def test_layer_padrao(self):
        camada, objeto = _layer_estudo("caso_45_layer_padrao.cdr")
        self.assertEqual((camada.pagina, camada.visivel, camada.imprimivel, camada.editavel),
                         (1, True, True, True))
        self.assertEqual(camada.quantidade_objetos_diretos, 1)
        self.assertEqual(objeto.camada, "LayerEstudo")

    def test_layer_oculta(self):
        camada, _ = _layer_estudo("caso_46_layer_oculta.cdr")
        self.assertEqual(camada.flags ^ 0x98000000, 0x140)
        self.assertFalse(camada.visivel)
        self.assertTrue(camada.imprimivel)

    def test_layer_nao_imprimivel(self):
        camada, _ = _layer_estudo("caso_47_layer_nao_imprimivel.cdr")
        self.assertEqual(camada.flags ^ 0x98000000, 0x08)
        self.assertFalse(camada.imprimivel)
        self.assertTrue(camada.visivel)

    def test_layer_bloqueada(self):
        camada, _ = _layer_estudo("caso_48_layer_bloqueada.cdr")
        self.assertEqual(camada.flags ^ 0x98000000, 0x10)
        self.assertFalse(camada.editavel)
        self.assertTrue(camada.visivel)

    def test_powerclip_herda_nome_da_layer(self):
        with abrir_cdr(CASOS / "caso_35_powerclip_aninhado.cdr") as doc:
            camadas = {obj.camada for obj in doc.estrutura() if obj.tipo == "obj"}
        self.assertEqual(camadas, {"Camada 1"})


if __name__ == "__main__":
    unittest.main()
