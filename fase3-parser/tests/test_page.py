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


class TestPreenchimentoETransparencia(unittest.TestCase):
    def _estilo(self, nome):
        caminho = _pular_se_sem_fixture(nome)
        with abrir_cdr(caminho) as doc:
            item = _por_nome(doc.pagina(1), "RetanguloBase")
            return item.estilo_tipado

    def test_sem_preenchimento(self):
        estilo = self._estilo("caso_67_sem_preenchimento.cdr")
        self.assertEqual(estilo.preenchimento.tipo, "nenhum")
        self.assertEqual(estilo.preenchimento.codigo_tipo, 0)

    def test_preenchimento_cmyk(self):
        estilo = self._estilo("caso_68_preenchimento_cmyk_ciano.cdr")
        self.assertEqual(estilo.preenchimento.tipo, "uniforme")
        self.assertEqual(estilo.preenchimento.cor_primaria.modelo, "CMYK")
        self.assertEqual(estilo.preenchimento.cor_primaria.componentes, (100, 0, 0, 0))

    def test_preenchimento_rgb(self):
        estilo = self._estilo("caso_69_preenchimento_rgb_azul.cdr")
        self.assertEqual(estilo.preenchimento.cor_primaria.modelo, "RGB255")
        self.assertEqual(estilo.preenchimento.cor_primaria.componentes, (0, 0, 255))

    def test_preenchimento_cinza(self):
        estilo = self._estilo("caso_91_preenchimento_cinza_128.cdr")
        self.assertEqual(estilo.preenchimento.cor_primaria.modelo, "GRAY255")
        self.assertEqual(estilo.preenchimento.cor_primaria.componentes, (128,))

    def test_preenchimento_lab(self):
        estilo = self._estilo("caso_92_preenchimento_lab.cdr")
        self.assertEqual(estilo.preenchimento.cor_primaria.modelo, "LAB")
        self.assertEqual(estilo.preenchimento.cor_primaria.componentes, (50, 20, -30))

    def test_preenchimento_hsb(self):
        estilo = self._estilo("caso_93_preenchimento_hsb.cdr")
        self.assertEqual(estilo.preenchimento.cor_primaria.modelo, "HSB")
        self.assertEqual(estilo.preenchimento.cor_primaria.componentes, (120, 50, 75))

    def test_preenchimento_hls(self):
        estilo = self._estilo("caso_94_preenchimento_hls.cdr")
        self.assertEqual(estilo.preenchimento.cor_primaria.componentes, (240, 50, 60))

    def test_sobreimpressao_do_preenchimento(self):
        estilo = self._estilo("caso_70_preenchimento_sobreimpressao.cdr")
        self.assertTrue(estilo.preenchimento.sobreimpressao)

    def test_transparencia_uniforme(self):
        estilo = self._estilo("caso_71_transparencia_uniforme_50.cdr")
        self.assertIsNotNone(estilo.transparencia)
        self.assertEqual(estilo.transparencia.uniforme, 0.5)
        self.assertEqual(estilo.transparencia.aplica_a, 2)

    def test_degrade_linear(self):
        estilo = self._estilo("caso_72_degrade_linear.cdr")
        preenchimento = estilo.preenchimento
        self.assertEqual(preenchimento.tipo, "degrade")
        self.assertEqual(preenchimento.tipo_degrade, "linear")
        self.assertEqual(preenchimento.cor_primaria.componentes, (0, 100, 100, 0))
        self.assertEqual(preenchimento.cor_secundaria.componentes, (100, 0, 0, 0))

    def test_angulo_de_degrade_linear(self):
        estilo = self._estilo("caso_82_degrade_linear_45graus.cdr")
        self.assertEqual(estilo.preenchimento.tipo_degrade, "linear")
        self.assertEqual(estilo.preenchimento.angulo, 45.0)

    def test_ponto_medio_de_degrade_linear(self):
        estilo = self._estilo("caso_83_degrade_linear_ponto_medio_25.cdr")
        self.assertEqual(estilo.preenchimento.ponto_medio, 25.0)

    def test_cor_intermediaria_de_degrade(self):
        estilo = self._estilo("caso_84_degrade_linear_cor_intermediaria.cdr")
        (parada,) = estilo.preenchimento.cores_intermediarias
        self.assertEqual(parada.posicao, 50.0)
        self.assertEqual(parada.cor.componentes, (0, 0, 100, 0))
        self.assertEqual(parada.opacidade, 255)

    def test_numero_de_passos_do_degrade(self):
        estilo = self._estilo("caso_85_degrade_linear_10_passos.cdr")
        self.assertEqual(estilo.preenchimento.passos, 10)

    def test_margem_do_degrade_reduz_escala(self):
        estilo = self._estilo("caso_86_degrade_linear_margem_15.cdr")
        self.assertEqual(estilo.preenchimento.escala_x, 0.7)
        self.assertEqual(estilo.preenchimento.escala_y, 0.7)

    def test_modo_de_mistura_do_degrade(self):
        estilo = self._estilo("caso_87_degrade_linear_mistura_1.cdr")
        self.assertEqual(estilo.preenchimento.modo_mistura, 1)

    def test_escala_explicita_do_degrade(self):
        estilo = self._estilo("caso_89_degrade_escala_70_80.cdr")
        self.assertAlmostEqual(estilo.preenchimento.escala_x, 0.7)
        self.assertAlmostEqual(estilo.preenchimento.escala_y, 0.8)

    def test_inclinacao_do_degrade(self):
        estilo = self._estilo("caso_90_degrade_inclinacao_15.cdr")
        self.assertAlmostEqual(estilo.preenchimento.inclinacao, 15.0)

    def test_tipos_de_degrade(self):
        casos = {
            "caso_73_degrade_radial.cdr": "radial",
            "caso_74_degrade_conico.cdr": "conico",
            "caso_75_degrade_quadrado.cdr": "quadrado",
        }
        for nome, tipo in casos.items():
            with self.subTest(nome=nome):
                estilo = self._estilo(nome)
                self.assertEqual(estilo.preenchimento.tipo, "degrade")
                self.assertEqual(estilo.preenchimento.tipo_degrade, tipo)

    def test_transparencia_degrade_linear(self):
        estilo = self._estilo("caso_76_transparencia_degrade_linear.cdr")
        transparencia = estilo.transparencia
        self.assertEqual(transparencia.tipo, "degrade")
        self.assertEqual(transparencia.tipo_degrade, "linear")
        self.assertEqual(transparencia.inicio, 0.0)
        self.assertEqual(transparencia.fim, 1.0)

    def test_tipos_de_transparencia_degrade(self):
        casos = {
            "caso_77_transparencia_degrade_radial.cdr": "radial",
            "caso_78_transparencia_degrade_conica.cdr": "conico",
            "caso_79_transparencia_degrade_quadrada.cdr": "quadrado",
        }
        for nome, tipo in casos.items():
            with self.subTest(nome=nome):
                transparencia = self._estilo(nome).transparencia
                self.assertEqual(transparencia.tipo, "degrade")
                self.assertEqual(transparencia.tipo_degrade, tipo)

    def test_preenchimento_padrao_duas_cores(self):
        estilo = self._estilo("caso_80_padrao_duas_cores.cdr")
        preenchimento = estilo.preenchimento
        self.assertEqual(preenchimento.tipo, "padrao")
        self.assertEqual(preenchimento.codigo_tipo, 8)
        self.assertEqual(preenchimento.id_padrao, 5)
        self.assertEqual(preenchimento.largura_repeticao, 1_000_000)
        self.assertEqual(preenchimento.altura_repeticao, 1_000_000)

    def test_padrao_xadrez_tem_id_e_repeticao_proprios(self):
        estilo = self._estilo("caso_81_padrao_duas_cores_xadrez.cdr")
        preenchimento = estilo.preenchimento
        self.assertEqual(preenchimento.tipo, "padrao")
        self.assertEqual(preenchimento.id_padrao, 1)
        self.assertEqual(preenchimento.largura_repeticao, 100_000)
        self.assertEqual(preenchimento.altura_repeticao, 100_000)


if __name__ == "__main__":
    unittest.main()
