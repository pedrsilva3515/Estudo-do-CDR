"""Testes da renderização própria (sem CorelDRAW)."""
from __future__ import annotations

import sys
import unittest
from io import BytesIO
from pathlib import Path
from unittest import mock

_AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(_AQUI.parent))

from zcfreader import visao_api  # noqa: E402
from zcfreader.render_proprio import _rgb, renderizar_pagina  # noqa: E402

CASOS = _AQUI.parent.parent / "casos-de-teste"


class TestRenderProprio(unittest.TestCase):
    def test_cores_cmyk_rgb_e_cmyk255(self):
        self.assertEqual(_rgb("CMYK,USER,0,0,0,100,100,x"), (0, 0, 0))
        self.assertEqual(_rgb("CMYK255,USER,0,0,0,0,100,x"), (255, 255, 255))
        self.assertEqual(_rgb("RGB255,USER,255,0,0,100,x"), (255, 0, 0))

    def test_renderiza_casos_com_curvas_bitmaps_e_texto(self):
        from PIL import Image

        for nome in ("caso_00_base.cdr", "caso_01_add_bitmap_jpeg.cdr", "caso_11_texto.cdr", "caso_62_curva_aberta.cdr"):
            caminho = CASOS / nome
            if not caminho.exists():
                continue
            with self.subTest(nome=nome):
                png = renderizar_pagina(caminho, lado_maximo_px=800)
                self.assertIsNotNone(png)
                with Image.open(BytesIO(png)) as imagem:
                    self.assertEqual(max(imagem.size), 800)
                    # Algo além do fundo branco foi desenhado.
                    self.assertLess(min(imagem.convert("L").getextrema()), 250)

    def test_analise_usa_render_proprio_sem_abrir_o_corel(self):
        caminho = CASOS / "caso_00_base.cdr"
        with mock.patch.object(visao_api, "renderizar_com_corel") as corel:
            imagem = visao_api.extrair_imagem_analise(caminho)
        corel.assert_not_called()
        self.assertEqual(imagem[2], "render_proprio")


if __name__ == "__main__":
    unittest.main()
