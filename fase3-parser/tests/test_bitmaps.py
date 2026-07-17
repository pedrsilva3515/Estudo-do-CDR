"""Testes do parser de Bitmaps.dat, usando os casos de teste da Fase 1/1b
(casos-de-teste/*.cdr, gerados pelo CorelDRAW real) como fixtures.

Roda com: python -m unittest discover -s fase3-parser/tests -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_AQUI = Path(__file__).resolve().parent
_RAIZ_PROJETO = _AQUI.parents[1]
sys.path.insert(0, str(_AQUI.parent))  # para importar o pacote zcfreader

from zcfreader import abrir_cdr  # noqa: E402
from zcfreader.bitmaps import FormatoBitmapsInvalido  # noqa: E402

CASOS = _RAIZ_PROJETO / "casos-de-teste"


def _pular_se_sem_fixture(nome: str):
    caminho = CASOS / nome
    if not caminho.exists():
        raise unittest.SkipTest(f"fixture ausente: {caminho}")
    return caminho


class TestSemBitmaps(unittest.TestCase):
    def test_documento_base_nao_tem_bitmaps(self):
        caminho = _pular_se_sem_fixture("caso_00_base.cdr")
        with abrir_cdr(caminho) as doc:
            self.assertIsNone(doc.bitmaps())


class TestUmBitmap(unittest.TestCase):
    def test_dimensoes_e_espaco_de_cor_rgb(self):
        caminho = _pular_se_sem_fixture("caso_01_add_bitmap_jpeg.cdr")
        with abrir_cdr(caminho) as doc:
            bitmaps = doc.bitmaps()
            self.assertEqual(len(bitmaps), 1)
            img = bitmaps[0].imagem
            self.assertEqual((img.largura, img.altura), (947, 947))
            self.assertEqual(img.bits_por_pixel, 24)
            self.assertEqual(img.espaco_de_cor, "RGB")
            self.assertIsNone(bitmaps[0].mascara)
            self.assertEqual(len(img.pixels), img.stride * img.altura)

    def test_resolucao_300dpi(self):
        caminho = _pular_se_sem_fixture("caso_01_add_bitmap_jpeg.cdr")
        with abrir_cdr(caminho) as doc:
            img = doc.bitmaps()[0].imagem
            self.assertAlmostEqual(img.resolucao_x_dpi, 300, delta=1)
            self.assertAlmostEqual(img.resolucao_y_dpi, 300, delta=1)

    def test_par_dpi_diferente_so_muda_resolucao(self):
        c96 = _pular_se_sem_fixture("caso_07_bitmap_dpi_096.cdr")
        c300 = _pular_se_sem_fixture("caso_08_bitmap_dpi_300.cdr")
        with abrir_cdr(c96) as doc96, abrir_cdr(c300) as doc300:
            img96 = doc96.bitmaps()[0].imagem
            img300 = doc300.bitmaps()[0].imagem
            self.assertAlmostEqual(img96.resolucao_x_dpi, 96, delta=1)
            self.assertAlmostEqual(img300.resolucao_x_dpi, 300, delta=1)
            self.assertEqual((img96.largura, img96.altura), (img300.largura, img300.altura))


class TestDeduplicacao(unittest.TestCase):
    def test_bitmap_duplicado_gera_um_so_registro(self):
        original = _pular_se_sem_fixture("caso_01_add_bitmap_jpeg.cdr")
        duplicado = _pular_se_sem_fixture("caso_17_bitmap_duplicado.cdr")
        with abrir_cdr(original) as d1, abrir_cdr(duplicado) as d2:
            b1, b2 = d1.bitmaps(), d2.bitmaps()
            self.assertEqual(len(b1), 1)
            self.assertEqual(len(b2), 1)
            self.assertEqual(b1[0].imagem.pixels, b2[0].imagem.pixels)

    def test_dois_bitmaps_diferentes_geram_dois_registros(self):
        caminho = _pular_se_sem_fixture("caso_16_dois_bitmaps_diferentes.cdr")
        with abrir_cdr(caminho) as doc:
            bitmaps = doc.bitmaps()
            self.assertEqual(len(bitmaps), 2)
            # cada registro deve ser internamente consistente
            for r in bitmaps:
                self.assertEqual(len(r.imagem.pixels), r.imagem.stride * r.imagem.altura)


class TestCmyk(unittest.TestCase):
    def test_cmyk_usa_32_bits_por_pixel(self):
        caminho = _pular_se_sem_fixture("caso_19_bitmap_cmyk.cdr")
        with abrir_cdr(caminho) as doc:
            img = doc.bitmaps()[0].imagem
            self.assertEqual(img.bits_por_pixel, 32)
            self.assertEqual(img.espaco_de_cor, "CMYK")
            self.assertEqual(img.stride, img.largura * 4)


class TestMascaraAlfa(unittest.TestCase):
    def test_mascara_tem_mesmas_dimensoes_da_imagem(self):
        caminho = _pular_se_sem_fixture("caso_20_bitmap_alpha.cdr")
        with abrir_cdr(caminho) as doc:
            registro = doc.bitmaps()[0]
            self.assertIsNotNone(registro.mascara)
            self.assertEqual(
                (registro.mascara.largura, registro.mascara.altura),
                (registro.imagem.largura, registro.imagem.altura),
            )
            self.assertEqual(registro.mascara.bits_por_pixel, 8)


class TestCoresConhecidas(unittest.TestCase):
    """Valida BGR->RGB e a leitura top-down comparando pixels decodificados
    com as cores exatas usadas para gerar a imagem-fonte na macro VBA
    (retangulo CMYK 0,100,100,0 = vermelho; elipse CMYK 100,40,0,0 = ciano)."""

    def test_cor_do_fundo_e_vermelho(self):
        caminho = _pular_se_sem_fixture("caso_02_add_bitmap_png.cdr")
        with abrir_cdr(caminho) as doc:
            from zcfreader.render import para_rgb

            img = doc.bitmaps()[0].imagem
            largura, altura, rgb = para_rgb(img)
            # (20,20): fora da elipse e longe o suficiente da borda do
            # retangulo para nao pegar o pixel anti-serrilhado do contorno
            # preto (o pixel (0,0) cai exatamente sobre essa borda).
            idx = (20 * largura + 20) * 3
            r, g, b = rgb[idx], rgb[idx + 1], rgb[idx + 2]
            self.assertGreater(r, 200)
            self.assertLess(g, 60)
            self.assertLess(b, 60)

    def test_cor_do_circulo_e_azul(self):
        caminho = _pular_se_sem_fixture("caso_02_add_bitmap_png.cdr")
        with abrir_cdr(caminho) as doc:
            from zcfreader.render import para_rgb

            img = doc.bitmaps()[0].imagem
            largura, altura, rgb = para_rgb(img)
            # centro da imagem cai dentro da elipse ciano/azul
            cx, cy = largura // 2, altura // 2
            idx = (cy * largura + cx) * 3
            r, g, b = rgb[idx], rgb[idx + 1], rgb[idx + 2]
            self.assertLess(r, 60)
            self.assertGreater(g, 100)
            self.assertGreater(b, 150)


class TestFotoReal(unittest.TestCase):
    def test_foto_real_sem_falhas_estruturais(self):
        caminho = CASOS / "caso_21_foto_real.cdr"
        if not caminho.exists():
            raise unittest.SkipTest("caso_21 e opcional; fixture ausente")
        with abrir_cdr(caminho) as doc:
            bitmaps = doc.bitmaps()
            self.assertEqual(len(bitmaps), 1)
            img = bitmaps[0].imagem
            self.assertEqual(len(img.pixels), img.stride * img.altura)


class TestErros(unittest.TestCase):
    def test_dados_curtos_levantam_erro(self):
        with self.assertRaises(FormatoBitmapsInvalido):
            from zcfreader.bitmaps import parse_bitmaps

            parse_bitmaps(b"\x00" * 4)


if __name__ == "__main__":
    unittest.main()
