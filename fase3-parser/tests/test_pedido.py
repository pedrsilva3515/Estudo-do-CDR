"""Testes do contrato inicial de interpretação de pedidos."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

_AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(_AQUI.parent))

from zcfreader import interpretar_nome_arquivo, parse_dimensoes, parse_material, parse_quantidade  # noqa: E402
from zcfreader.pedido import _aplicar_nome_arquivo, _associar_um_a_um, _inventario_geometrico, _itens_de_instrucoes_explicitas, selecionar_inventario_geometrico  # noqa: E402


def _caixa_cm(x, y, largura, altura):
    return SimpleNamespace(
        esquerda=x * 100_000, base=y * 100_000,
        direita=(x + largura) * 100_000, topo=(y + altura) * 100_000,
    )


def _objeto(tipo, caixa, ancestrais=()):
    return SimpleNamespace(tipo="obj", tipo_objeto=tipo, caixa=caixa, ancestrais=ancestrais)


class TestQuantidade(unittest.TestCase):
    def test_formas_usuais(self):
        for texto, esperado in (
            ("1und", 1),
            ("2 un", 2),
            ("3 unidades", 3),
            ("qtd: 5", 5),
            ("Quantidade = 12", 12),
            ("30 UNI DE CADA", 30),
            ("60 UNI", 60),
            ("50 ADESIVOS 8CM", 50),
            ("1 ADESIVO 30 CM", 1),
            ("2 LONAS 3X1", 2),
        ):
            with self.subTest(texto=texto):
                self.assertEqual(parse_quantidade(texto), (esperado, "unidade"))

    def test_numero_sem_contexto_nao_e_quantidade(self):
        self.assertIsNone(parse_quantidade("Banner 90x120 cm"))
        self.assertIsNone(parse_quantidade("ADESIVO 1,5 PLACAS"))
        self.assertIsNone(parse_quantidade("LONA 440G"))
        # "x" entre duas medidas não é quantidade (pedido "lona fosca" lia 15 em "2,15 x 1,95").
        self.assertIsNone(parse_quantidade("5,40 x 1,40"))
        self.assertIsNone(parse_quantidade("10x20"))
        self.assertEqual(parse_quantidade("Lona fosca com ilhoes _2,15 x 1,95_1 un"), (1, "unidade"))
        self.assertEqual(parse_quantidade("6x"), (6, "unidade"))


class TestInventarioGeometrico(unittest.TestCase):
    def test_encontra_produtos_dentro_de_grupo_profundo(self):
        wheat_a = _caixa_cm(0, 0, 46, 49)
        wheat_b = _caixa_cm(50, 0, 46, 49)
        foto = _caixa_cm(120, 0, 13.44, 20.54)
        grande = _caixa_cm(150, 0, 200, 190.11)
        pequeno_a = _caixa_cm(370, 0, 106.25, 99.98)
        pequeno_b = _caixa_cm(370, 110, 106.25, 99.98)
        bitmap = _caixa_cm(500, 0, 20, 20)
        numeros = _caixa_cm(-130, 0, 112.33, 63.64)
        grupo = SimpleNamespace(tipo="grp", tipo_objeto=None, caixa=_caixa_cm(0, 0, 96, 60), ancestrais=())
        estrutura = [
            grupo,
            _objeto("curva", wheat_a, ("grp",)), _objeto("curva", wheat_b, ("grp",)),
            _objeto("retangulo", foto), _objeto("bitmap", foto),
            _objeto("curva", grande), _objeto("curva", grande),
            _objeto("curva", pequeno_a), _objeto("curva", pequeno_b),
            _objeto("bitmap", bitmap), _objeto("texto", numeros),
        ]
        fluxo_numeros = SimpleNamespace(
            fluxo=SimpleNamespace(texto="0102030405060708091011121314151617181920"),
            objeto=estrutura[-1],
        )
        doc = SimpleNamespace(
            estrutura=lambda: estrutura,
            textos_por_objeto=lambda: [fluxo_numeros],
        )

        inventario = _inventario_geometrico(doc)
        chaves = {(i["quantidade_sugerida"], round(i["largura_cm"], 2), round(i["altura_cm"], 2)) for i in inventario}

        self.assertIn((1, 112.33, 63.64), chaves)
        self.assertIn((1, 13.44, 20.54), chaves)
        self.assertIn((1, 200.0, 190.11), chaves)
        self.assertIn((2, 106.25, 99.98), chaves)
        self.assertIn((1, 20.0, 20.0), chaves)
        self.assertIn((1, 96.0, 49.0), chaves)

        selecionados = selecionar_inventario_geometrico(inventario)
        self.assertEqual(
            {(i["quantidade_sugerida"], round(i["largura_cm"], 2), round(i["altura_cm"], 2)) for i in selecionados},
            {(1, 112.33, 63.64), (1, 13.44, 20.54), (1, 200.0, 190.11), (2, 106.25, 99.98), (1, 20, 20), (1, 96, 49)},
        )


class TestMaterial(unittest.TestCase):
    def test_banner_e_lona_com_acabamento_banner(self):
        self.assertEqual(parse_material("BANNER"), {"material": "lona", "acabamento": "banner"})

    def test_brilhoso_nao_e_ilhos(self):
        from zcfreader.experimento_agente import _especificacao_material

        self.assertIsNone(_especificacao_material("VINIL BRILHOSO")["acabamento"])
        self.assertEqual(_especificacao_material("Lona fosca com ilhoes")["acabamento"], "ilhós")

    def test_material_so_como_palavra(self):
        # OCR do nome desenhado "Qd_Institucional" contém "lona" no meio (pedido 6_etapa).
        self.assertIsNone(parse_material("Qd_Instltuclonal_B"))
        self.assertEqual(parse_material("LONA 440G")["material"], "lona")

    def test_descricao_completa_do_adesivo(self):
        # "blackout" muda o material: não pode virar só "adesivo fosco" (pedido 4_etapa).
        for texto, esperado in (
            ("3 UNIDADES DE CADA IMPRIMIR NO ADESIVO BRANCO FOSCO BLACKOUT", "adesivo branco fosco blackout"),
            ("VINIL FOSCO - CAIXA MONET", "adesivo fosco"),
            ("VINIL SUPER COLA - TSCAR", "adesivo super cola"),
            ("ADESIVO TRASNPARENTE", "adesivo transparente"),
        ):
            with self.subTest(texto=texto):
                self.assertEqual(parse_material(texto)["material"], esperado)

    def test_material_e_acabamento(self):
        self.assertEqual(
            parse_material("adesivo transparente recortado\n15 unid"),
            {"material": "adesivo transparente", "acabamento": "recortado"},
        )
        self.assertEqual(
            parse_material("TODOS ADESIVO NORMAL"),
            {"material": "adesivo normal", "acabamento": None},
        )
        self.assertEqual(
            parse_material("adesivo leitoso recortados"),
            {"material": "adesivo leitoso", "acabamento": "recortado"},
        )
        self.assertEqual(
            parse_material("adesivo trasnparente com recorte especial"),
            {"material": "adesivo transparente", "acabamento": "recorte especial"},
        )

    def test_transparente_com_erro_de_digitacao(self):
        for texto in ("adesivo trasparente", "vinil tranparente", "adesivo trasnparente"):
            with self.subTest(texto=texto):
                self.assertEqual(parse_material(texto)["material"], "adesivo transparente")

    def test_texto_sem_material(self):
        self.assertIsNone(parse_material("14und"))
        self.assertIsNone(parse_material("Google Ads"))  # "ads" só é adesivo no nome do arquivo

    def test_vinil_transparente_no_nome(self):
        self.assertEqual(
            parse_material("VINIL TRANSPARENTE - ANMG 014"),
            {"material": "adesivo transparente", "acabamento": None},
        )

    def test_lona_fosca_nao_vira_lona_padrao(self):
        self.assertEqual(parse_material("Lona fosca com ilhoes _2,15 x 1,95_1 un")["material"], "lona fosca")
        self.assertEqual(parse_material("Banner 80 cm X 53cm")["material"], "lona")

    def test_painel_e_outdoor_no_nome_do_arquivo_sao_papel_outdoor(self):
        from zcfreader.pedido import interpretar_nome_arquivo

        for nome in ("Panel_Futebol_Heitor.cdr", "paineis thiago.cdr", "2 outdoor.cdr"):
            self.assertEqual(interpretar_nome_arquivo(nome)["material"]["material"], "papel outdoor", nome)
        self.assertIsNone(interpretar_nome_arquivo("paineis e adesivo alecia.cdr")["material"])  # misto

    def test_materiais_adicionais_e_documento_misto(self):
        self.assertEqual(parse_material("VINIL FOSCO")["material"], "adesivo fosco")
        self.assertEqual(parse_material("LONA COM ILHOS")["material"], "lona")
        self.assertIsNone(parse_material("banner e adesivo sem recorte"))


class TestDimensoes(unittest.TestCase):
    def test_quantidade_com_dimensoes_decimais(self):
        resultado = parse_dimensoes("9 UN (23,4X18,4 CM)")
        self.assertEqual(resultado["largura_mm"], 234)
        self.assertEqual(resultado["altura_mm"], 184)

    def test_instrucao_explicita_vira_um_unico_item_autoritativo(self):
        origem = {
            "valor": 9, "unidade": "unidade", "texto_origem": "9 UN (23,4X18,4 CM)",
            "dimensoes": parse_dimensoes("9 UN (23,4X18,4 CM)"),
            "objeto": SimpleNamespace(caixa=object()),
        }
        itens = _itens_de_instrucoes_explicitas([origem])
        self.assertEqual(len(itens), 1)
        self.assertEqual(itens[0]["quantidade"]["valor"], 9)
        self.assertEqual(itens[0]["dimensoes"]["largura_mm"], 234)
        self.assertEqual(itens[0]["dimensoes"]["altura_mm"], 184)
        self.assertEqual(itens[0]["dimensoes"]["fonte"], "texto_cdr")

    def test_sem_unidade_exige_contexto_de_quantidade(self):
        self.assertEqual(parse_dimensoes("4 UN (46,5 X 9)")["largura_mm"], 465)
        self.assertIsNone(parse_dimensoes("telefone 46,5 x 9"))

    def test_de_cada_e_associado_a_todas_as_pecas_da_regiao(self):
        def caixa(esquerda, base, direita, topo):
            return SimpleNamespace(esquerda=esquerda, base=base, direita=direita, topo=topo)
        candidatos = [
            {"caixa": caixa(-390_0000, -150_0000, -110_0000, 180_0000)},
            {"caixa": caixa(-100_0000, -760_0000, 140_0000, 180_0000)},
            {"caixa": caixa(300_0000, -70_0000, 500_0000, 180_0000)},
        ]
        referencias = [{
            "texto_origem": "30 UNI DE CADA", "objeto": SimpleNamespace(
                caixa=caixa(-395_0000, 265_0000, 125_0000, 315_0000)
            ),
        }]
        associacoes = _associar_um_a_um(candidatos, referencias)
        self.assertEqual(associacoes, {0: 0, 1: 0})


def _item_sem_material(material=None):
    return {"material": {"valor": material, "fonte": None, "confianca": 0.0},
            "acabamento": {"valor": None, "fonte": None, "confianca": 0.0},
            "quantidade": {"valor": 1, "fonte": "texto_cdr"}}


class TestUnidadeGrudadaELaminacao(unittest.TestCase):
    def test_und_grudado_em_ads(self):
        texto = "5x5\n50undads recortados"
        self.assertEqual(parse_quantidade(texto), (50, "unidade"))
        self.assertEqual(parse_dimensoes(texto)["largura_mm"], 50.0)
        self.assertEqual(parse_material(texto), {"material": "adesivo", "acabamento": "recortado"})

    def test_transparente_aplicado_em_cima_e_laminacao(self):
        self.assertEqual(
            parse_material("50x50 1und ads leitoso com trasparente aplicado em cima"),
            {"material": "adesivo leitoso", "acabamento": "laminação"},
        )
        self.assertEqual(parse_material("adesivo recortado e laminado")["acabamento"], "recortado + laminação")

    def test_medida_e_quantidade_em_linhas_separadas(self):
        texto = "ads recortados \n4x4\n100und"
        self.assertEqual(parse_quantidade(texto), (100, "unidade"))
        dimensoes = parse_dimensoes(texto)
        self.assertEqual((dimensoes["largura_mm"], dimensoes["altura_mm"]), (40.0, 40.0))

    def test_painel_outdoor_e_papel_outdoor(self):
        self.assertEqual(parse_material("painel outdoor")["material"], "papel outdoor")
        self.assertEqual(parse_material("paineis outdoor 1und de cada")["material"], "papel outdoor")

    def test_ads_solto_na_arte_nao_e_material(self):
        self.assertIsNone(parse_material("Google Ads"))


class TestPlacaPS(unittest.TestCase):
    def test_ps_adesivado_tem_quantidade_e_material(self):
        texto = "1 PS ADESIVADO NO TAMANHO 20X30 CM"
        self.assertEqual(parse_quantidade(texto), (1, "unidade"))
        self.assertEqual(parse_material(texto), {"material": "ps adesivado", "acabamento": None})

    def test_espessura_e_ps_solto_na_arte(self):
        self.assertEqual(parse_material("placa de PS 2mm")["material"], "ps 2 mm")
        self.assertIsNone(parse_material("PS: obrigado pela preferência"))


class TestDimensoesComUnidadeNasDuasMedidas(unittest.TestCase):
    def test_metros_nas_duas_medidas(self):
        dimensoes = parse_dimensoes("1,10M X 2,40M")
        self.assertEqual((dimensoes["largura_mm"], dimensoes["altura_mm"]), (1100.0, 2400.0))


class TestNomeArquivo(unittest.TestCase):
    def test_material_do_nome_vale_para_todas_as_pecas(self):
        itens = [_item_sem_material() for _ in range(4)]
        _aplicar_nome_arquivo(itens, interpretar_nome_arquivo("ADESIVOS CLIENTE.cdr"))
        self.assertEqual([item["material"]["valor"] for item in itens], ["adesivo"] * 4)
        self.assertTrue(all(item["material"]["fonte"] == "nome_arquivo" for item in itens))

    def test_material_do_nome_nao_entra_quando_o_cdr_diz_outro(self):
        itens = [_item_sem_material("lona"), _item_sem_material()]
        _aplicar_nome_arquivo(itens, interpretar_nome_arquivo("ADESIVOS CLIENTE.cdr"))
        self.assertEqual([item["material"]["valor"] for item in itens], ["lona", None])

    def test_nome_generico_nao_completa_quando_o_cdr_e_mais_especifico(self):
        itens = [_item_sem_material("adesivo transparente"), _item_sem_material()]
        _aplicar_nome_arquivo(itens, interpretar_nome_arquivo("logo cliente ads.cdr"))
        self.assertEqual([item["material"]["valor"] for item in itens], ["adesivo transparente", None])

    def test_nome_com_outro_produto_nao_vale_para_todas(self):
        itens = [_item_sem_material() for _ in range(2)]
        _aplicar_nome_arquivo(itens, interpretar_nome_arquivo("paineis e adesivo cliente.cdr"))
        self.assertEqual([item["material"]["valor"] for item in itens], [None, None])

    def test_acabamento_do_nome_completa_material_generico_do_cdr(self):
        itens = [_item_sem_material("adesivo") for _ in range(2)]
        _aplicar_nome_arquivo(itens, interpretar_nome_arquivo("VINIL_BRILHOSO_RECORTADO.cdr"))
        self.assertEqual([item["acabamento"]["valor"] for item in itens], ["recortado"] * 2)

    def test_variacoes_de_recorte_e_prismatico(self):
        for nome, esperado in (
            ("VINIL BRANCO - APENAS RECORTE NO BRANCO.cdr", {"material": "adesivo branco", "acabamento": "somente recorte"}),
            ("adesivos impressos com corte especial.cdr", {"material": "adesivo", "acabamento": "recorte especial"}),
            ("VINIL PRISMATICO AMARELO - 502.cdr", {"material": "adesivo prismatico", "acabamento": None}),
            ("Adesivos_Perfurado_Cliente.cdr", {"material": "adesivo perfurado", "acabamento": None}),
        ):
            with self.subTest(nome=nome):
                self.assertEqual(interpretar_nome_arquivo(nome)["material"], esperado)

    def test_sufixo_de_copia_nao_vira_quantidade(self):
        resultado = interpretar_nome_arquivo("guanarabara iza ads (1).cdr")
        self.assertIsNone(resultado["quantidade"])

    def test_material_e_sem_recorte(self):
        resultado = interpretar_nome_arquivo("adesivos BK set - sem rec.cdr")
        self.assertEqual(resultado["material"]["material"], "adesivo")
        self.assertEqual(resultado["material"]["acabamento"], "sem recorte")

    def test_ads_transparente_recortado(self):
        resultado = interpretar_nome_arquivo("logo cliente ADS TRASPARENTE RECORTADO.cdr")
        self.assertEqual(resultado["material"], {"material": "adesivo transparente", "acabamento": "recortado"})

    def test_quantidade_e_dimensao_explicitas(self):
        resultado = interpretar_nome_arquivo("20und adesivo 30x40cm.cdr")
        self.assertEqual(resultado["quantidade"], (20, "unidade"))
        self.assertEqual(resultado["dimensoes"]["largura_mm"], 300)
        self.assertEqual(resultado["dimensoes"]["altura_mm"], 400)

    def test_dimensao_inteira_sem_unidade_no_nome(self):
        # Pedido ARTHUR: "71X61" no nome, sem unidade, são centímetros; "3x1" são metros.
        for nome, esperado in (
            ("ARTHUR FINHA ADESIVO SEM RECORTE 71X61.cdr", (710, 610)),
            ("BANNER 60 X90 MONTADO.cdr", (600, 900)),
            ("lona 3x2.cdr", (3000, 2000)),
        ):
            with self.subTest(nome=nome):
                dimensoes = interpretar_nome_arquivo(nome)["dimensoes"]
                self.assertEqual((dimensoes["largura_mm"], dimensoes["altura_mm"]), esperado)

    def test_dimensao_em_metros_sem_unidade_no_nome(self):
        resultado = interpretar_nome_arquivo("ADESIVO TRANSPARENTE 1,00X0,55.cdr")
        self.assertEqual(resultado["dimensoes"]["largura_mm"], 1000)
        self.assertEqual(resultado["dimensoes"]["altura_mm"], 550)


if __name__ == "__main__":
    unittest.main()
