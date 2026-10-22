"""Títulos e rótulos de material sobre colunas de peças, como num pedido de painéis e adesivo."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _amostras import amostra, com_amostra  # noqa: E402
from zcfreader.pedido import _aplicar_materiais, interpretar_pedido, parse_material  # noqa: E402

CM = 100_000  # unidades internas por centímetro

def _caixa(x0, y0, x1, y1):
    return SimpleNamespace(esquerda=x0 * CM, base=y0 * CM, direita=x1 * CM, topo=y1 * CM)


def _item(x0, y0, x1, y1):
    return {"_caixa": _caixa(x0, y0, x1, y1), "quantidade": {"valor": 1},
            "material": {"valor": None}, "acabamento": {"valor": None}}


def _titulo(texto, x0, y0, x1, y1):
    return {**parse_material(texto), "texto_origem": texto, "quantidade": None,
            "objeto": SimpleNamespace(caixa=_caixa(x0, y0, x1, y1))}


class TestTitulosDeColuna(unittest.TestCase):
    def test_papel_outdoor_com_erro_de_digitacao(self):
        self.assertEqual(parse_material("Papel outdor"), {"material": "papel outdoor", "acabamento": None})
        self.assertIsNone(parse_material("Outdoor"))  # sem "papel" pode ser só o tema da arte

    def test_cada_peca_recebe_o_titulo_acima_dela(self):
        # Mesma disposição de um pedido real (cm).
        itens = [
            _item(-447, -118, -357, 72),   # 0,9 x 1,9
            _item(-348, -79, -198, 71),    # 1,5 x 1,5
            _item(-346, -164, -201, -104), # 1,45 x 0,6 (abaixo do círculo)
            _item(-182, -36, -127, 34),    # 0,55 x 0,7
        ]
        titulos = [_titulo("Papel outdor", -396, 100, -269, 121), _titulo("Adesivo", -179, 74, -122, 86)]
        ambiguos = _aplicar_materiais(itens, titulos)
        self.assertEqual([item["material"]["valor"] for item in itens],
                         ["papel outdoor", "papel outdoor", "papel outdoor", "adesivo"])
        self.assertEqual(ambiguos, [])

    def test_rotulo_embaixo_e_peca_vizinha(self):
        # Como num pedido de freezer: "LONA" embaixo da lona, "adesivos" embaixo das laterais
        # e um adesivo redondo sem rótulo colado a uma lateral.
        itens = [
            _item(-463, -94, -163, 6),     # lona 300 x 100
            _item(-117, -107, -52, -25),   # lateral
            _item(-99, -22, -73, 3),       # redondo, 3 cm acima da lateral
        ]
        rotulos = [_titulo("LONA", -372, -132, -290, -109), _titulo("adesivos", -64, -164, 56, -141)]
        self.assertEqual(_aplicar_materiais(itens, rotulos), [])
        self.assertEqual([item["material"]["valor"] for item in itens], ["lona", "adesivo", "adesivo"])
        self.assertEqual(itens[2]["material"]["fonte"], "peca_vizinha")

    def test_transparente_com_branco_em_rotulo_curto(self):
        self.assertEqual(parse_material("TRANPARENTE COM BRANCO")["material"], "adesivo transparente com branco")
        self.assertIsNone(parse_material("seja transparente com seus clientes todos os dias"))

    def test_peca_sem_titulo_acima_continua_pendente(self):
        itens = [_item(0, 0, 50, 50), _item(100, 0, 150, 50)]
        ambiguos = _aplicar_materiais(itens, [_titulo("Adesivo", 0, 60, 40, 70)])
        self.assertEqual([item["material"]["valor"] for item in itens], ["adesivo", None])
        self.assertEqual(len(ambiguos), 1)


@com_amostra("colunas_papel_e_adesivo")
class TestAmostraColunas(unittest.TestCase):
    def test_tres_papeis_um_adesivo_e_vestigio_ignorado(self):
        resultado = interpretar_pedido(amostra("colunas_papel_e_adesivo"))
        itens = sorted((round(i["dimensoes"]["largura_mm"] / 10), round(i["dimensoes"]["altura_mm"] / 10),
                        i["material"]["valor"]) for i in resultado["itens"])
        self.assertEqual(itens, [(55, 70, "adesivo"), (90, 190, "papel outdoor"),
                                 (145, 60, "papel outdoor"), (150, 150, "papel outdoor")])
        self.assertIn("OBJETO_MINUSCULO_IGNORADO", [a["codigo"] for a in resultado["alertas"]])


@com_amostra("miniatura_e_paineis")
class TestAmostraMiniatura(unittest.TestCase):
    def test_miniatura_com_quantidade_nao_e_vestigio(self):
        resultado = interpretar_pedido(amostra("miniatura_e_paineis"))
        self.assertNotIn("OBJETO_MINUSCULO_IGNORADO", [a["codigo"] for a in resultado["alertas"]])
        itens = sorted((round(i["dimensoes"]["largura_mm"] / 10), round(i["dimensoes"]["altura_mm"] / 10),
                        i["quantidade"]["valor"], i["material"]["valor"]) for i in resultado["itens"])
        self.assertEqual(itens, [(4, 4, 100, "adesivo"), (40, 60, 1, "papel outdoor"),
                                 (50, 50, 1, "papel outdoor"), (60, 90, 1, "papel outdoor")])


@com_amostra("linhas_explicitas_ps")
class TestAmostraLinhasExplicitas(unittest.TestCase):
    def test_ps_adesivos_e_banner_das_linhas_do_pedido(self):
        resultado = interpretar_pedido(amostra("linhas_explicitas_ps"))
        itens = sorted((round(i["dimensoes"]["largura_mm"]), round(i["dimensoes"]["altura_mm"]),
                        i["material"]["valor"]) for i in resultado["itens"])
        self.assertEqual(itens, [(200, 300, "ps adesivado")] * 2 + [(414, 315, "adesivo fosco")] * 3
                         + [(700, 1000, "lona")])


@com_amostra("und_grudado_e_laminacao")
class TestAmostraUndGrudado(unittest.TestCase):
    def test_cinquenta_recortados_e_laminacao(self):
        resultado = interpretar_pedido(amostra("und_grudado_e_laminacao"))
        itens = sorted((round(i["dimensoes"]["largura_mm"]), round(i["dimensoes"]["altura_mm"]), i["quantidade"]["valor"],
                        i["material"]["valor"], i["acabamento"]["valor"]) for i in resultado["itens"])
        self.assertEqual(itens, [(50, 50, 50, "adesivo", "recortado"), (500, 500, 1, "adesivo leitoso", "laminação")])


@com_amostra("rotulos_embaixo_e_mascaras")
class TestAmostraRotulosEmbaixo(unittest.TestCase):
    def test_pecas_e_materiais(self):
        resultado = interpretar_pedido(amostra("rotulos_embaixo_e_mascaras"))
        itens = sorted((round(i["dimensoes"]["largura_mm"] / 10), round(i["dimensoes"]["altura_mm"] / 10),
                        i["quantidade"]["valor"], i["material"]["valor"]) for i in resultado["itens"])
        self.assertEqual(itens, [
            (26, 25, 1, "adesivo"), (65, 82, 2, "adesivo"), (86, 82, 1, "adesivo"), (94, 75, 1, "adesivo"),
            (126, 86, 1, "adesivo transparente com branco"), (300, 100, 1, "lona"),
        ])


@com_amostra("paineis_de_cada")
class TestAmostraPaineisDeCada(unittest.TestCase):
    def test_paineis_de_cada_e_adesivo(self):
        resultado = interpretar_pedido(amostra("paineis_de_cada"))
        itens = sorted((round(i["dimensoes"]["largura_mm"] / 10), round(i["dimensoes"]["altura_mm"] / 10),
                        i["material"]["valor"]) for i in resultado["itens"])
        self.assertEqual(itens, [(60, 60, "adesivo leitoso"), (68, 200, "papel outdoor"),
                                 (133, 200, "papel outdoor"), (150, 200, "papel outdoor")])


if __name__ == "__main__":
    unittest.main()
