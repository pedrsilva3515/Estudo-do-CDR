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

    def test_conteudo_de_powerclip_e_medido_pela_mascara(self):
        from zcfreader.container import abrir_cdr

        caminho = CASOS / "caso_15_powerclip.cdr"
        if not caminho.exists():
            self.skipTest("caso_15 ausente")
        with abrir_cdr(caminho) as doc:
            estrutura = list(doc.estrutura())
            recipientes = doc.recipientes_powerclip(estrutura)
            self.assertTrue(recipientes, "o caso 15 tem um PowerClip")
            visivel = {(o.membro, o.offset_root): o for o in doc.estrutura_visivel()}
        for (membro, offset), recipiente in recipientes.items():
            caixa = visivel[(membro, offset)].caixa
            if caixa is None:
                continue
            self.assertGreaterEqual(caixa.esquerda, recipiente.caixa.esquerda)
            self.assertLessEqual(caixa.direita, recipiente.caixa.direita)
            self.assertGreaterEqual(caixa.base, recipiente.caixa.base)
            self.assertLessEqual(caixa.topo, recipiente.caixa.topo)

    def test_pecas_do_catalogo_caem_sobre_o_desenho(self):
        """Catálogo e desenho usam a mesma referência: a região de cada peça não fica em branco."""
        from PIL import Image

        from zcfreader.experimento_agente import extrair_candidatos_agente
        from zcfreader.selecao_peca import px_do_cm

        for nome in ("caso_15_powerclip.cdr", "caso_26_segundo_retangulo.cdr"):
            caminho = CASOS / nome
            if not caminho.exists():
                continue
            catalogo = extrair_candidatos_agente(caminho)
            with Image.open(BytesIO(renderizar_pagina(caminho, lado_maximo_px=800))) as imagem:
                cinza = imagem.convert("L")
                fatos = {"limites_cm": catalogo["limites_conteudo_cm"]}
                for candidato in catalogo["candidatos"]:
                    x0, y0, x1, y1 = px_do_cm(fatos, cinza.size, candidato["caixa_cm"])
                    corte = cinza.crop((max(0, int(x0)), max(0, int(y0)), min(cinza.size[0], int(x1) + 1), min(cinza.size[1], int(y1) + 1)))
                    with self.subTest(caso=nome, peca=candidato["id"]):
                        self.assertTrue(corte.size[0] and corte.size[1], "peça fora da imagem")
                        self.assertLess(corte.getextrema()[0], 250, "região da peça em branco: desenho e catálogo desalinhados")

    def test_analise_usa_render_proprio_sem_abrir_o_corel(self):
        caminho = CASOS / "caso_00_base.cdr"
        with mock.patch.object(visao_api, "renderizar_com_corel") as corel:
            imagem = visao_api.extrair_imagem_analise(caminho)
        corel.assert_not_called()
        self.assertEqual(imagem[2], "render_proprio")


if __name__ == "__main__":
    unittest.main()
