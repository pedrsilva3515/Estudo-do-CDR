"""Testes da arvore RIFF de content/root.dat."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_AQUI = Path(__file__).resolve().parent
_RAIZ_PROJETO = _AQUI.parents[1]
sys.path.insert(0, str(_AQUI.parent))

from zcfreader import abrir_cdr  # noqa: E402
from zcfreader.structure import _parse_geometria_curva  # noqa: E402

CASOS = _RAIZ_PROJETO / "casos-de-teste"


class TestEstruturaRoot(unittest.TestCase):
    def test_todos_os_casos_numerados_tem_arvore_legivel(self):
        casos = sorted(CASOS.glob("caso_*.cdr"))
        self.assertGreaterEqual(len(casos), 33)
        for caminho in casos:
            with self.subTest(caso=caminho.name), abrir_cdr(caminho) as doc:
                objetos = doc.estrutura()
                self.assertTrue(objetos)
                self.assertTrue(any(obj.tipo == "obj" for obj in objetos))

    def test_grupo_contem_objetos_na_hierarquia(self):
        with abrir_cdr(CASOS / "caso_13_grupo.cdr") as doc:
            objetos = doc.estrutura()
        filhos_de_grupo = [obj for obj in objetos if obj.tipo == "obj" and "grp" in obj.ancestrais]
        self.assertGreaterEqual(len(filhos_de_grupo), 2)

    def test_ids_de_stream_sao_zero_based(self):
        with abrir_cdr(CASOS / "caso_00_base.cdr") as doc:
            objetos = doc.estrutura()
        objetos_da_pagina = [
            obj for obj in objetos
            if obj.tipo == "obj" and obj.membro == "content/data/page1.dat"
        ]
        self.assertTrue(objetos_da_pagina)
        self.assertTrue(any(obj.caixa is not None for obj in objetos_da_pagina))

    def test_bitmap_ocupa_posicao_no_indice_de_streams(self):
        with abrir_cdr(CASOS / "caso_01_add_bitmap_jpeg.cdr") as doc:
            objetos = doc.estrutura()
        self.assertTrue(any(
            obj.membro == "content/data/page1.dat" and obj.caixa is not None
            for obj in objetos
        ))

    def test_codigo_identifica_tipos_controlados(self):
        casos = {
            "caso_00_base.cdr": {"retangulo": 1},
            "caso_12_dois_objetos.cdr": {"retangulo": 1, "elipse": 1},
            "caso_11_texto.cdr": {"retangulo": 1, "texto": 1},
            "caso_01_add_bitmap_jpeg.cdr": {"retangulo": 1, "bitmap": 1},
        }
        for nome, esperado in casos.items():
            with self.subTest(caso=nome), abrir_cdr(CASOS / nome) as doc:
                objetos = [obj for obj in doc.estrutura() if obj.tipo == "obj"]
                obtido = {
                    tipo: sum(obj.tipo_objeto == tipo for obj in objetos)
                    for tipo in esperado
                }
                self.assertEqual(obtido, esperado)

    def test_contagens_de_tipos_batem_com_metadata(self):
        chaves = {
            "retangulo": "Rect",
            "elipse": "Ellipse",
            "curva": "Curve",
            "texto": "Text",
            "bitmap": "Bitmap",
        }
        for caminho in sorted(CASOS.glob("caso_*.cdr")):
            with self.subTest(caso=caminho.name), abrir_cdr(caminho) as doc:
                metadata = doc.metadados()
                objetos = [obj for obj in doc.estrutura() if obj.tipo == "obj"]
                for tipo, chave in chaves.items():
                    self.assertEqual(
                        sum(obj.tipo_objeto == tipo for obj in objetos),
                        metadata.contagem_objetos.get(chave, 0),
                    )

    def test_rotacao_de_trinta_graus(self):
        with abrir_cdr(CASOS / "caso_25_rotaciona_retangulo.cdr") as doc:
            objeto = next(obj for obj in doc.estrutura() if obj.tipo == "obj")
        self.assertAlmostEqual(objeto.matriz.rotacao_graus, 30.0, places=6)

    def test_objeto_da_pagina_recebe_indice(self):
        with abrir_cdr(CASOS / "caso_00_base.cdr") as doc:
            objeto = next(obj for obj in doc.estrutura() if obj.tipo == "obj")
        self.assertEqual(objeto.pagina, 1)

    def test_powerclips_na_mesma_pagina_recebem_indice(self):
        caminho = CASOS / "caso_33_powerclip_duplo_mesma_pagina.cdr"
        with abrir_cdr(caminho) as doc:
            objetos = [obj for obj in doc.estrutura() if obj.tipo == "obj"]
        self.assertEqual(len(objetos), 4)
        self.assertEqual({obj.pagina for obj in objetos}, {1})
        recipientes = [obj for obj in objetos if obj.grupo_powerclip is not None]
        self.assertEqual([obj.grupo_powerclip for obj in recipientes], [1, 4])

    def test_powerclip_herda_pagina_do_recipiente(self):
        caminho = CASOS / "caso_34_powerclip_duas_paginas.cdr"
        with abrir_cdr(caminho) as doc:
            objetos = [obj for obj in doc.estrutura() if obj.tipo == "obj"]
        por_pagina = {
            pagina: [obj.tipo_objeto for obj in objetos if obj.pagina == pagina]
            for pagina in (1, 2)
        }
        self.assertEqual(por_pagina, {1: ["elipse", "retangulo"], 2: ["elipse", "retangulo"]})

    def test_powerclip_aninhado_propaga_pagina(self):
        caminho = CASOS / "caso_35_powerclip_aninhado.cdr"
        with abrir_cdr(caminho) as doc:
            objetos = [obj for obj in doc.estrutura() if obj.tipo == "obj"]
        self.assertEqual(len(objetos), 3)
        self.assertEqual({obj.pagina for obj in objetos}, {1})
        self.assertEqual(
            sorted(obj.grupo_powerclip for obj in objetos if obj.grupo_powerclip is not None),
            [1, 4],
        )

    def test_conferencia_inclui_conteudo_de_powerclip(self):
        caminho = CASOS / "caso_36_powerclip_fora_da_pagina.cdr"
        with abrir_cdr(caminho) as doc:
            ocorrencias = doc.conferencia_limites()
        self.assertEqual(len(ocorrencias), 2)
        self.assertEqual(
            {ocorrencia.objeto.membro for ocorrencia in ocorrencias},
            {"content/data/data1.dat", "content/data/page1.dat"},
        )
        self.assertTrue(all(ocorrencia.excede_direita_mm > 20 for ocorrencia in ocorrencias))

    def test_layout_compacto_de_curva(self):
        import struct

        # Tabela minima coerente: os cinco offsets finais delimitam o vetor.
        pontos = ((10, -20, 12), (30, 40, 68), (-50, 60, 192))
        inicio = 40
        fim_geometria = inicio + 8 + 9 * len(pontos)
        tamanho = fim_geometria + 8
        cabecalho = struct.pack(
            "<10I",
            tamanho, 4, 20, 40, 3,
            inicio, inicio + 4, fim_geometria, tamanho - 4, tamanho,
        )
        coordenadas = b"".join(struct.pack("<ii", x, y) for x, y, _ in pontos)
        flags = bytes(flag for _, _, flag in pontos)
        dados = cabecalho + struct.pack("<II", 7, len(pontos)) + coordenadas + flags
        dados += struct.pack("<II", 3, 1)

        geometria = _parse_geometria_curva(dados)
        self.assertIsNotNone(geometria)
        self.assertEqual(geometria.indice_logico, 7)
        self.assertEqual(
            [(p.x, p.y, p.flag) for p in geometria.pontos],
            list(pontos),
        )

    def test_curva_controlada_aberta_e_fechada(self):
        esperados = {
            "caso_62_curva_aberta.cdr": (1, [False]),
            "caso_63_curva_fechada.cdr": (1, [True]),
            "caso_64_curva_dois_subcaminhos.cdr": (2, [False, True]),
            "caso_65_curva_dois_subcaminhos_abertos.cdr": (2, [False, False]),
        }
        for nome, (quantidade, fechados) in esperados.items():
            with self.subTest(caso=nome), abrir_cdr(CASOS / nome) as doc:
                objeto = next(obj for obj in doc.estrutura() if obj.tipo == "obj")
            geometria = objeto.geometria_curva
            self.assertEqual(geometria.numero_subcaminhos, quantidade)
            self.assertEqual([s.fechado for s in geometria.subcaminhos], fechados)
            self.assertEqual(geometria.possui_subcaminho_aberto, not all(fechados))

    def test_papeis_dos_pontos_de_curva(self):
        casos = {
            "caso_62_curva_aberta.cdr": ["inicio", "fim_linha", "fim_linha"],
            "caso_66_curva_bezier_aberta.cdr": [
                "inicio", "controle", "controle", "fim_curva"
            ],
        }
        for nome, esperado in casos.items():
            with self.subTest(caso=nome), abrir_cdr(CASOS / nome) as doc:
                objeto = next(obj for obj in doc.estrutura() if obj.tipo == "obj")
            self.assertEqual(
                [ponto.papel for ponto in objeto.geometria_curva.pontos],
                esperado,
            )

    def test_conferencia_de_curvas_abertas(self):
        for nome, esperado in (
            ("caso_62_curva_aberta.cdr", 1),
            ("caso_63_curva_fechada.cdr", 0),
            ("caso_64_curva_dois_subcaminhos.cdr", 1),
        ):
            with self.subTest(caso=nome), abrir_cdr(CASOS / nome) as doc:
                self.assertEqual(len(doc.curvas_com_subcaminhos_abertos()), esperado)

    def test_tamanho_personalizado_por_pagina(self):
        caminho = CASOS / "caso_32_paginas_tamanhos_diferentes.cdr"
        with abrir_cdr(caminho) as doc:
            paginas = doc.paginas_estruturais()
            metadata = doc.metadados()
        self.assertEqual(
            [(p.indice, p.largura_mm, p.altura_mm, p.tamanho_personalizado) for p in paginas],
            [(1, 210.0, 297.0, False), (2, 100.0, 200.0, True)],
        )
        # O resumo XMP continua representando a primeira pagina A4.
        self.assertEqual((metadata.largura_pagina_mm, metadata.altura_pagina_mm), (210.0, 297.0))

    def test_detecta_objeto_cruzando_cada_borda(self):
        caminho = CASOS / "caso_29_cruza_quatro_bordas.cdr"
        with abrir_cdr(caminho) as doc:
            ocorrencias = doc.conferencia_limites()
        self.assertEqual(len(ocorrencias), 4)
        self.assertEqual(sum(o.excede_esquerda_mm > 0 for o in ocorrencias), 1)
        self.assertEqual(sum(o.excede_direita_mm > 0 for o in ocorrencias), 1)
        self.assertEqual(sum(o.excede_topo_mm > 0 for o in ocorrencias), 1)
        self.assertEqual(sum(o.excede_base_mm > 0 for o in ocorrencias), 1)
        self.assertTrue(all(o.ultrapassa_sangria for o in ocorrencias))

    def test_origem_da_regua_nao_muda_resultado_de_limites(self):
        with abrir_cdr(CASOS / "caso_29_cruza_quatro_bordas.cdr") as original:
            caixas_original = sorted(
                (o.caixa.esquerda, o.caixa.topo, o.caixa.direita, o.caixa.base)
                for o in original.estrutura() if o.tipo == "obj"
            )
            fora_original = len(original.conferencia_limites())
        with abrir_cdr(CASOS / "caso_30_origem_alterada.cdr") as alterado:
            caixas_alterado = sorted(
                (o.caixa.esquerda, o.caixa.topo, o.caixa.direita, o.caixa.base)
                for o in alterado.estrutura() if o.tipo == "obj"
            )
            fora_alterado = len(alterado.conferencia_limites())
        self.assertEqual(caixas_original, caixas_alterado)
        self.assertEqual((fora_original, fora_alterado), (4, 4))

    def test_objeto_pode_ficar_fora_do_corte_mas_dentro_da_sangria(self):
        with abrir_cdr(CASOS / "caso_31_sangria_3mm.cdr") as doc:
            paginas = doc.paginas_estruturais()
            ocorrencias = doc.conferencia_limites()
        self.assertEqual(paginas[0].sangria_mm, 3.0)
        self.assertEqual(len(ocorrencias), 1)
        self.assertFalse(ocorrencias[0].ultrapassa_sangria)

    def test_no_suave_adiciona_bit_confirmado(self):
        cuspide = CASOS / "caso_97_curva_bezier_no_cuspide.cdr"
        suave = CASOS / "caso_96_curva_bezier_no_suave.cdr"
        if not cuspide.exists() or not suave.exists():
            self.skipTest("fixtures de nós de Bézier ausentes")
        with abrir_cdr(cuspide) as original, abrir_cdr(suave) as alterado:
            curva_original = next(
                o.geometria_curva for o in original.estrutura() if o.tipo_objeto == "curva"
            )
            curva_alterada = next(
                o.geometria_curva for o in alterado.estrutura() if o.tipo_objeto == "curva"
            )
        self.assertEqual(curva_original.pontos[3].tipo_no, "cuspide")
        self.assertEqual(curva_alterada.pontos[3].tipo_no, "suave")


if __name__ == "__main__":
    unittest.main()
