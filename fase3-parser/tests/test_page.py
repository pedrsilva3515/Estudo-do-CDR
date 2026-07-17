"""Testes do parser (parcial) de page1.dat, usando os casos de teste da
Fase 1/1b como fixtures.

Roda com: python -m unittest discover -s fase3-parser/tests -v
"""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_AQUI = Path(__file__).resolve().parent
_RAIZ_PROJETO = _AQUI.parents[1]
sys.path.insert(0, str(_AQUI.parent))

from zcfreader import abrir_cdr  # noqa: E402

CASOS = _RAIZ_PROJETO / "casos-de-teste"


def _pular_se_sem_fixture(nome: str):
    caminho = CASOS / nome
    if not caminho.exists():
        raise unittest.SkipTest(f"fixture ausente: {caminho}")
    return caminho


def _por_nome(itens, nome):
    return next((i for i in itens if i.nome == nome), None)


class TestNomes(unittest.TestCase):
    def test_documento_base_tem_layers_padrao_e_objeto(self):
        caminho = _pular_se_sem_fixture("caso_00_base.cdr")
        with abrir_cdr(caminho) as doc:
            itens = doc.pagina(1)
            nomes = {i.nome for i in itens}
            # layers padrao criadas pelo proprio CorelDRAW, nao pela macro
            self.assertIn("Linhas-guia", nomes)
            self.assertIn("Camada 1", nomes)
            self.assertIn("RetanguloBase", nomes)

    def test_pagina_inexistente_devolve_none(self):
        caminho = _pular_se_sem_fixture("caso_00_base.cdr")
        with abrir_cdr(caminho) as doc:
            self.assertIsNone(doc.pagina(2))

    def test_nova_layer_aparece_pelo_nome_dado_na_macro(self):
        caminho = _pular_se_sem_fixture("caso_09_nova_layer.cdr")
        with abrir_cdr(caminho) as doc:
            nomes = {i.nome for i in doc.pagina(1)}
            self.assertIn("CamadaTeste", nomes)

    def test_dois_objetos_aparecem_com_nomes_distintos(self):
        caminho = _pular_se_sem_fixture("caso_12_dois_objetos.cdr")
        with abrir_cdr(caminho) as doc:
            nomes = {i.nome for i in doc.pagina(1)}
            self.assertIn("RetanguloBase", nomes)
            self.assertIn("ElipseTeste", nomes)

    def test_texto_artistico_nao_gera_falsos_nomes(self):
        # Documentos com texto tem dados binarios (kerning/curvas de glifo)
        # que podem colidir com o padrao heuristico de nome UTF-16LE; o
        # objeto de verdade deve continuar aparecendo, sem lixo.
        caminho = _pular_se_sem_fixture("caso_11_texto.cdr")
        with abrir_cdr(caminho) as doc:
            nomes = [i.nome for i in doc.pagina(1)]
            self.assertIn("RetanguloBase", nomes)
            for n in nomes:
                letras = sum(c.isalpha() for c in n)
                self.assertGreaterEqual(letras / len(n), 0.6)


class TestEstilosBrutos(unittest.TestCase):
    def test_parse_estilos_encontra_todos_mesmo_sem_nome(self):
        # caso_12 tem 2 objetos nomeados com estilo cada -- parse_estilos
        # deve achar os 2, igual parse_page, quando tudo esta nomeado.
        caminho = _pular_se_sem_fixture("caso_12_dois_objetos.cdr")
        with abrir_cdr(caminho) as doc:
            estilos = doc.estilos_da_pagina(1)
            self.assertEqual(len(estilos), 2)
            cores = {e["fill"]["primaryColor"].split(",")[2:6][0] for _, e in estilos}
            self.assertTrue(cores)

    def test_pagina_inexistente_devolve_none(self):
        caminho = _pular_se_sem_fixture("caso_00_base.cdr")
        with abrir_cdr(caminho) as doc:
            self.assertIsNone(doc.estilos_da_pagina(2))


class TestEstiloJson(unittest.TestCase):
    def test_cor_do_retangulo_bate_com_cmyk_definido_na_macro(self):
        caminho = _pular_se_sem_fixture("caso_00_base.cdr")
        with abrir_cdr(caminho) as doc:
            item = _por_nome(doc.pagina(1), "RetanguloBase")
            self.assertIsNotNone(item)
            self.assertIsNotNone(item.estilo)
            cor = item.estilo["fill"]["primaryColor"]
            # macro usa CreateCMYKColor(0, 100, 100, 0) = vermelho
            self.assertEqual(cor.split(",")[:6], ["CMYK", "USER", "0", "100", "100", "0"])

    def test_cor_alterada_reflete_no_json(self):
        base = _pular_se_sem_fixture("caso_00_base.cdr")
        alterado = _pular_se_sem_fixture("caso_10_altera_cor.cdr")
        with abrir_cdr(base) as d1, abrir_cdr(alterado) as d2:
            cor1 = _por_nome(d1.pagina(1), "RetanguloBase").estilo["fill"]["primaryColor"]
            cor2 = _por_nome(d2.pagina(1), "RetanguloBase").estilo["fill"]["primaryColor"]
            self.assertEqual(cor1.split(",")[:6], ["CMYK", "USER", "0", "100", "100", "0"])
            # macro muda para CreateCMYKColor(100, 0, 0, 0) = ciano
            self.assertEqual(cor2.split(",")[:6], ["CMYK", "USER", "100", "0", "0", "0"])

    def test_cores_de_dois_objetos_distintos(self):
        caminho = _pular_se_sem_fixture("caso_12_dois_objetos.cdr")
        with abrir_cdr(caminho) as doc:
            itens = doc.pagina(1)
            ret = _por_nome(itens, "RetanguloBase")
            eli = _por_nome(itens, "ElipseTeste")
            self.assertEqual(
                ret.estilo["fill"]["primaryColor"].split(",")[:6],
                ["CMYK", "USER", "0", "100", "100", "0"],
            )
            # macro usa CreateCMYKColor(100, 0, 100, 0) = verde
            self.assertEqual(
                eli.estilo["fill"]["primaryColor"].split(",")[:6],
                ["CMYK", "USER", "100", "0", "100", "0"],
            )

    def test_layers_nao_tem_estilo(self):
        caminho = _pular_se_sem_fixture("caso_00_base.cdr")
        with abrir_cdr(caminho) as doc:
            camada = _por_nome(doc.pagina(1), "Camada 1")
            self.assertIsNotNone(camada)
            self.assertIsNone(camada.estilo)


if __name__ == "__main__":
    unittest.main()
