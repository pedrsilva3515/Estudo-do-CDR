"""Testes do contrato inicial de interpretação de pedidos."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

_AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(_AQUI.parent))

from zcfreader import interpretar_nome_arquivo, parse_dimensoes, parse_material, parse_quantidade  # noqa: E402
from zcfreader.pedido import _associar_um_a_um, _inventario_geometrico, _itens_de_instrucoes_explicitas, selecionar_inventario_geometrico  # noqa: E402


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

    def test_texto_sem_material(self):
        self.assertIsNone(parse_material("14und"))

    def test_vinil_transparente_no_nome(self):
        self.assertEqual(
            parse_material("VINIL TRANSPARENTE - ANMG 014"),
            {"material": "adesivo transparente", "acabamento": None},
        )

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


class TestNomeArquivo(unittest.TestCase):
    def test_sufixo_de_copia_nao_vira_quantidade(self):
        resultado = interpretar_nome_arquivo("guanarabara iza ads (1).cdr")
        self.assertIsNone(resultado["quantidade"])

    def test_material_e_sem_recorte(self):
        resultado = interpretar_nome_arquivo("adesivos BK set - sem rec.cdr")
        self.assertEqual(resultado["material"]["material"], "adesivo")
        self.assertEqual(resultado["material"]["acabamento"], "sem recorte")

    def test_quantidade_e_dimensao_explicitas(self):
        resultado = interpretar_nome_arquivo("20und adesivo 30x40cm.cdr")
        self.assertEqual(resultado["quantidade"], (20, "unidade"))
        self.assertEqual(resultado["dimensoes"]["largura_mm"], 300)
        self.assertEqual(resultado["dimensoes"]["altura_mm"], 400)

    def test_dimensao_em_metros_sem_unidade_no_nome(self):
        resultado = interpretar_nome_arquivo("ADESIVO TRANSPARENTE 1,00X0,55.cdr")
        self.assertEqual(resultado["dimensoes"]["largura_mm"], 1000)
        self.assertEqual(resultado["dimensoes"]["altura_mm"], 550)


if __name__ == "__main__":
    unittest.main()
