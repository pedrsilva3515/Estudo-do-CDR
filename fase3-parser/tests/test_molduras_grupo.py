"""Várias peças com moldura montadas num único grupo de topo, como num pedido de freezer."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from _amostras import amostra, com_amostra  # noqa: E402
from zcfreader.pedido import _candidatos_arte, interpretar_pedido  # noqa: E402

CM = 100_000  # unidades internas por centímetro

def _obj(ancestrais, tipo, tipo_objeto, x0, y0, x1, y1):
    caixa = SimpleNamespace(esquerda=x0 * CM, base=y0 * CM, direita=x1 * CM, topo=y1 * CM)
    return SimpleNamespace(tipo=tipo, tipo_objeto=tipo_objeto, ancestrais=("grp",) * ancestrais, caixa=caixa,
                           geometria_curva=None)


def _freezer():
    """Mesma árvore do arquivo real: título + peça 148 x 83 + duas peças 74 x 74 num grupo só."""
    return [
        _obj(0, "grp", None, -75, -94, 75, 94),
        _obj(1, "grp", None, -75, -94, 75, -20),           # as duas peças de baixo
        _obj(2, "grp", None, 1, -94, 75, -20),
        _obj(3, "obj", "bitmap", 19, -89, 25, -83),
        _obj(3, "obj", "curva", 18, -68, 37, -34),
        _obj(3, "obj", "retangulo", 1, -94, 75, -20),
        _obj(2, "grp", None, -75, -94, -1, -20),
        _obj(3, "obj", "bitmap", -57, -89, -51, -83),
        _obj(3, "obj", "curva", -59, -68, -40, -34),
        _obj(3, "obj", "retangulo", -75, -94, -1, -20),
        _obj(1, "grp", None, -74, -12, 74, 71),            # a peça de cima
        _obj(2, "obj", "bitmap", -15, 0, 24, 26),
        _obj(2, "obj", "curva", -20, 24, -1, 58),
        _obj(2, "obj", "retangulo", -74, -12, 74, 71),
        _obj(1, "obj", "texto", -66, 77, 66, 94),          # título com o material
    ]


def _medidas(estrutura):
    candidatos = _candidatos_arte(SimpleNamespace(estrutura_visivel=lambda: estrutura))
    return sorted((round(c["largura_mm"] / 10), round(c["altura_mm"] / 10)) for c in candidatos)


class TestMoldurasDentroDoGrupo(unittest.TestCase):
    def test_cada_moldura_vira_uma_peca(self):
        self.assertEqual(_medidas(_freezer()), [(74, 74), (74, 74), (148, 83)])

    def test_uma_moldura_so_mantem_o_grupo(self):
        estrutura = _freezer()[:1] + _freezer()[10:]
        self.assertEqual(_medidas(estrutura), [(150, 188)])

    def test_arte_fora_das_molduras_mantem_o_grupo(self):
        estrutura = _freezer() + [_obj(1, "obj", "curva", -70, 75, -60, 90)]
        self.assertEqual(_medidas(estrutura), [(150, 188)])

    def test_molduras_sobrepostas_mantem_o_grupo(self):
        estrutura = _freezer()
        estrutura[10] = _obj(1, "grp", None, -74, -40, 74, 71)
        estrutura[13] = _obj(2, "obj", "retangulo", -74, -40, 74, 71)
        self.assertEqual(_medidas(estrutura), [(150, 188)])


class TestConteudoDePowerClip(unittest.TestCase):
    def test_fotos_dentro_de_powerclip_nao_sao_pecas(self):
        # Colagem: as fotos ficam em grupos de topo,
        # recortadas por retângulos dentro do grupo da peça de 62,5 x 50.
        foto_a = _obj(0, "grp", None, -29, -21, -19, 0)
        foto_a.id_estrutural = 3
        foto_b = _obj(0, "grp", None, -6, 0, 18, 12)
        foto_b.id_estrutural = 5
        peca = _obj(0, "grp", None, -31, -25, 31, 25)
        recipiente_a = _obj(1, "obj", "retangulo", -29, -21, -19, 0)
        recipiente_a.grupo_powerclip = 3
        recipiente_b = _obj(1, "obj", "retangulo", -6, 0, 18, 12)
        recipiente_b.grupo_powerclip = 5
        estrutura = [
            foto_a, _obj(1, "obj", "bitmap", -29, -21, -19, 0),
            foto_b, _obj(1, "obj", "bitmap", -6, 0, 18, 12),
            peca, _obj(1, "obj", "retangulo", -31, -25, 31, 25), recipiente_a, recipiente_b,
        ]
        self.assertEqual(_medidas(estrutura), [(62, 50)])

    def test_pecas_em_powerclip_sem_moldura_do_grupo_continuam_pecas(self):
        # Pôsteres lado a lado num grupo sem moldura própria.
        estrutura = []
        recipientes = []
        for indice, x in enumerate((0, 21, 42)):
            poster = _obj(0, "grp", None, x, 0, x + 21, 30)
            poster.id_estrutural = indice + 1
            estrutura += [poster, _obj(1, "obj", "bitmap", x, 0, x + 21, 30)]
            recipiente = _obj(1, "obj", "retangulo", x, 0, x + 21, 30)
            recipiente.grupo_powerclip = indice + 1
            recipientes.append(recipiente)
        estrutura += [_obj(0, "grp", None, 0, 0, 63, 30), *recipientes]
        self.assertEqual(_medidas(estrutura), [(21, 30)] * 3)


@com_amostra("colagem_powerclip")
class TestAmostraColagem(unittest.TestCase):
    def test_uma_peca_de_62_por_50(self):
        resultado = interpretar_pedido(amostra("colagem_powerclip"))
        itens = [(round(i["dimensoes"]["largura_mm"] / 10), round(i["dimensoes"]["altura_mm"] / 10),
                  i["quantidade"]["valor"], i["material"]["valor"], i["acabamento"]["valor"]) for i in resultado["itens"]]
        self.assertEqual(itens, [(62, 50, 1, "adesivo leitoso", "sem recorte")])


@com_amostra("folha_branca_circulos")
class TestAmostraFolhaBranca(unittest.TestCase):
    def test_folha_branca_em_volta_dos_circulos_nao_e_peca(self):
        # "adesivo vinil leitoso com recorte / 20cm cada circulo" com um retângulo branco atrás.
        resultado = interpretar_pedido(amostra("folha_branca_circulos"))
        itens = [(round(i["dimensoes"]["largura_mm"] / 10), round(i["dimensoes"]["altura_mm"] / 10),
                  i["quantidade"]["valor"], i["material"]["valor"]) for i in resultado["itens"]]
        self.assertEqual(itens, [(20, 20, 1, "adesivo leitoso")] * 6)


@com_amostra("folha_copias_agrupadas")
class TestAmostraCopiasAgrupadas(unittest.TestCase):
    def test_copias_agrupadas_numa_folha_com_recorte(self):
        resultado = interpretar_pedido(amostra("folha_copias_agrupadas"))
        itens = sorted((round(i["dimensoes"]["largura_mm"] / 10), round(i["dimensoes"]["altura_mm"] / 10),
                        i["quantidade"]["valor"]) for i in resultado["itens"])
        self.assertEqual(itens, [(20, 5, 14), (35, 9, 12), (90, 23, 1)])


@com_amostra("folha_sem_recorte")
class TestAmostraSemRecorte(unittest.TestCase):
    def test_sem_recorte_a_folha_continua_uma_peca(self):
        resultado = interpretar_pedido(amostra("folha_sem_recorte"))
        self.assertEqual(len(resultado["itens"]), 1)


@com_amostra("medida_escrita_powerclip")
class TestAmostraMedidaEscrita(unittest.TestCase):
    def test_medida_escrita_identifica_a_peca_inteira(self):
        # "1,10M X 2,40M" escrito no pedido é o tamanho do grupo que recorta as fotos.
        resultado = interpretar_pedido(amostra("medida_escrita_powerclip"))
        itens = [(round(i["dimensoes"]["largura_mm"] / 10), round(i["dimensoes"]["altura_mm"] / 10),
                  i["quantidade"]["valor"], i["material"]["valor"]) for i in resultado["itens"]]
        self.assertEqual(itens, [(110, 240, 1, "adesivo perfurado")])


@com_amostra("grupo_unico_tres_molduras")
class TestAmostraGrupoUnico(unittest.TestCase):
    def test_tres_adesivos(self):
        resultado = interpretar_pedido(amostra("grupo_unico_tres_molduras"))
        itens = sorted((round(i["dimensoes"]["largura_mm"] / 10), round(i["dimensoes"]["altura_mm"] / 10),
                        i["quantidade"]["valor"]) for i in resultado["itens"])
        self.assertEqual(itens, [(74, 74, 2), (148, 83, 1)])
        self.assertEqual(resultado["total_unidades"], 3)


if __name__ == "__main__":
    unittest.main()
