"""Grupo que embrulha o pedido inteiro (artes + textos "6x", "3x"), como no pedido Avante."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from zcfreader.experimento_agente import _aplicar_montagens, _grupos_montagem  # noqa: E402

CM = 100_000  # unidades internas por centímetro


def _obj(offset, ancestrais, tipo, tipo_objeto, x0, y0, x1, y1):
    caixa = SimpleNamespace(esquerda=x0 * CM, base=y0 * CM, direita=x1 * CM, topo=y1 * CM)
    return SimpleNamespace(tipo=tipo, tipo_objeto=tipo_objeto, ancestrais=("grp",) * ancestrais, caixa=caixa,
                           membro="content/data/page1.dat", offset_root=offset)


def _documento(textos: dict):
    estrutura = [
        _obj(1, 0, "grp", None, 0, 0, 94, 40),              # o grupo que embrulha tudo
        _obj(2, 1, "grp", None, 0, 0, 40, 30),              # arte 40 x 30
        _obj(3, 2, "obj", "curva", 0, 0, 40, 30),
        _obj(4, 1, "grp", None, 45, 0, 70, 11),             # arte 25 x 11
        _obj(5, 2, "obj", "curva", 45, 0, 70, 11),
        _obj(6, 1, "obj", "texto", 10, 32, 20, 39),         # instrução
    ]
    itens = [SimpleNamespace(objeto=o, fluxo=SimpleNamespace(texto=textos.get(o.offset_root, "")))
             for o in estrutura if o.tipo_objeto == "texto"]
    return SimpleNamespace(textos_por_objeto=lambda: itens), estrutura


class TestGruposMontagem(unittest.TestCase):
    def test_grupo_com_artes_e_quantidade_e_montagem(self):
        doc, estrutura = _documento({6: "6x"})
        montagens = _grupos_montagem(doc, estrutura)
        self.assertEqual(len(montagens), 1)
        medidas = sorted((round(f["caixa_cm"]["direita"] - f["caixa_cm"]["esquerda"]),
                          round(f["caixa_cm"]["topo"] - f["caixa_cm"]["base"])) for f in montagens[0]["filhos"])
        self.assertEqual(medidas, [(25, 11), (40, 30)])

    def test_sem_texto_de_quantidade_e_arte_composta(self):
        doc, estrutura = _documento({6: "PROMOÇÃO"})
        self.assertEqual(_grupos_montagem(doc, estrutura), [])

    def test_aplicar_esconde_o_embrulho_e_mostra_as_pecas(self):
        doc, estrutura = _documento({6: "6x"})
        montagens = _grupos_montagem(doc, estrutura)
        embrulho = {"id": "A01", "caixa_cm": {"esquerda": 0, "direita": 94, "base": 0, "topo": 40},
                    "visivel_inicialmente": True}
        peca = {"id": "A02", "caixa_cm": {"esquerda": 0, "direita": 40, "base": 0, "topo": 30},
                "visivel_inicialmente": False}
        _aplicar_montagens([embrulho, peca], montagens)
        self.assertFalse(embrulho["visivel_inicialmente"])
        self.assertTrue(peca["visivel_inicialmente"])


if __name__ == "__main__":
    unittest.main()
