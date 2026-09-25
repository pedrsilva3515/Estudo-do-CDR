"""Testes da ligacao entre instancias e registros de Bitmaps.dat."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_AQUI = Path(__file__).resolve().parent
_RAIZ_PROJETO = _AQUI.parents[1]
sys.path.insert(0, str(_AQUI.parent))

from zcfreader import abrir_cdr  # noqa: E402

CASOS = _RAIZ_PROJETO / "casos-de-teste"


class TestReferenciasBitmap(unittest.TestCase):
    def test_bitmap_duplicado_tem_duas_instancias_e_uma_imagem(self):
        with abrir_cdr(CASOS / "caso_17_bitmap_duplicado.cdr") as doc:
            bitmaps = doc.bitmaps()
            instancias = doc.instancias_bitmaps()
        self.assertEqual(len(bitmaps), 1)
        self.assertEqual(len(instancias), 2)
        self.assertEqual(
            {i.identificador_bitmap for i in instancias},
            {bitmaps[0].identificador},
        )

    def test_dois_bitmaps_diferentes_sao_mapeados(self):
        with abrir_cdr(CASOS / "caso_16_dois_bitmaps_diferentes.cdr") as doc:
            bitmaps = doc.bitmaps()
            instancias = doc.instancias_bitmaps()
        self.assertEqual(len(bitmaps), 2)
        self.assertEqual(len(instancias), 2)
        self.assertEqual(
            {i.identificador_bitmap for i in instancias},
            {b.identificador for b in bitmaps},
        )

    def test_cmyk_usa_bpp_do_descritor(self):
        with abrir_cdr(CASOS / "caso_19_bitmap_cmyk.cdr") as doc:
            instancias = doc.instancias_bitmaps()
        self.assertEqual(len(instancias), 1)
        self.assertEqual(instancias[0].registro.imagem.bits_por_pixel, 32)

    def test_contagem_bate_com_metadata_em_todos_os_casos(self):
        for caminho in sorted(CASOS.glob("caso_*.cdr")):
            with self.subTest(caso=caminho.name), abrir_cdr(caminho) as doc:
                meta = doc.metadados()
                esperado = meta.contagem_objetos.get("Bitmap", 0)
                self.assertEqual(len(doc.instancias_bitmaps()), esperado)


class TestGeometriaLocalBitmap(unittest.TestCase):
    def test_movimento_altera_so_translacao_da_matriz(self):
        with abrir_cdr(CASOS / "caso_01_add_bitmap_jpeg.cdr") as base:
            m1 = base.instancias_bitmaps()[0].matriz_local
        with abrir_cdr(CASOS / "caso_06_move_bitmap.cdr") as movido:
            m2 = movido.instancias_bitmaps()[0].matriz_local

        self.assertIsNotNone(m1)
        self.assertIsNotNone(m2)
        self.assertEqual((m1.a, m1.b, m1.c, m1.d), (m2.a, m2.b, m2.c, m2.d))
        self.assertAlmostEqual(m2.tx - m1.tx, 200_000, places=6)
        self.assertAlmostEqual(m2.ty - m1.ty, -200_000, places=6)

    def test_bitmap_duplicado_tem_matriz_por_instancia(self):
        with abrir_cdr(CASOS / "caso_17_bitmap_duplicado.cdr") as doc:
            instancias = doc.instancias_bitmaps()
        self.assertEqual(len(instancias), 2)
        self.assertNotEqual(instancias[0].matriz_local.tx, instancias[1].matriz_local.tx)
        self.assertNotEqual(instancias[0].matriz_local.ty, instancias[1].matriz_local.ty)

    def test_dpi_local_sem_escala_bate_com_dpi_nativo(self):
        with abrir_cdr(CASOS / "caso_01_add_bitmap_jpeg.cdr") as doc:
            instancia = doc.instancias_bitmaps()[0]
        self.assertAlmostEqual(instancia.matriz_local.escala_x, 1.0)
        self.assertAlmostEqual(instancia.matriz_local.escala_y, 1.0)
        self.assertAlmostEqual(
            instancia.dpi_efetivo_local_x,
            instancia.registro.imagem.resolucao_x_dpi,
        )
        self.assertAlmostEqual(
            instancia.dpi_efetivo_local_y,
            instancia.registro.imagem.resolucao_y_dpi,
        )
        self.assertAlmostEqual(instancia.largura_local_mm, 947 / 300 * 25.4, places=3)
        self.assertAlmostEqual(instancia.altura_local_mm, 947 / 300 * 25.4, places=3)

    def test_root_liga_instancia_ao_objeto_e_confirma_matriz(self):
        for nome in (
            "caso_01_add_bitmap_jpeg.cdr",
            "caso_16_dois_bitmaps_diferentes.cdr",
            "caso_17_bitmap_duplicado.cdr",
            "caso_19_bitmap_cmyk.cdr",
        ):
            with self.subTest(caso=nome), abrir_cdr(CASOS / nome) as doc:
                for instancia in doc.instancias_bitmaps():
                    self.assertIsNotNone(instancia.objeto)
                    self.assertEqual(instancia.objeto.tipo, "obj")
                    self.assertIsNotNone(instancia.matriz_final)
                    self.assertEqual(instancia.matriz_final, instancia.matriz_local)
                    self.assertIsNotNone(instancia.objeto.caixa)

    def test_bbox_move_exatamente_dois_centimetros(self):
        with abrir_cdr(CASOS / "caso_01_add_bitmap_jpeg.cdr") as base:
            c1 = base.instancias_bitmaps()[0].objeto.caixa
        with abrir_cdr(CASOS / "caso_06_move_bitmap.cdr") as movido:
            c2 = movido.instancias_bitmaps()[0].objeto.caixa
        self.assertEqual(c2.esquerda - c1.esquerda, 200_000)
        self.assertEqual(c2.direita - c1.direita, 200_000)
        self.assertEqual(c2.topo - c1.topo, -200_000)
        self.assertEqual(c2.base - c1.base, -200_000)


if __name__ == "__main__":
    unittest.main()


class TestDescritorComCampo32Variavel(unittest.TestCase):
    """Pedido real ("Adesivos Jerdson") traz 8 bytes tipo ponteiro em +32."""

    def test_descritor_com_ponteiro_em_32_e_reconhecido(self):
        import struct

        from zcfreader.bitmaps import ArquivoBitmaps, ImagemBruta, RegistroBitmap
        from zcfreader.references import parse_instancias_bitmap

        imagem = ImagemBruta(3169, 3169, 24, 9508, 1000.0, 1000.0, b"")
        bitmaps = ArquivoBitmaps([RegistroBitmap(1, 22, 0, imagem)])
        descritor = (
            struct.pack("<HHIIII", 2, 24, 3169, 3169, 1, 22)
            + b"\x00" * 8 + b"\xff" * 4
            + bytes.fromhex("20e7d45d46020000")
            + struct.pack("<I", 5)
        )
        dados = b"\x00" * 7 + descritor + b"\x00" * 300
        instancias = parse_instancias_bitmap(dados, "content/data/page1.dat", bitmaps)
        self.assertEqual([i.offset for i in instancias], [7])
        self.assertEqual(instancias[0].identificador_bitmap, 22)
