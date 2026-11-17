"""Régua dos pacotes revisados: gabarito ajustado, faca de recorte e nomes vindos do WhatsApp."""
from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from zcfreader.avaliacao_caminhos import carregar_casos, gabarito_ajustado, sem_faca_de_recorte  # noqa: E402


def _pacote(pasta: Path, nome_zip: str, membro_cdr: str, caso_id: str, sha: str) -> None:
    with ZipFile(pasta / nome_zip, "w") as pacote:
        pacote.writestr("diagnostico.json", json.dumps({"caso_id": caso_id, "arquivo": {"nome": "x", "sha256": sha}}))
        pacote.writestr("resultado-correto.json", json.dumps({"itens": []}))
        pacote.writestr(membro_cdr, b"cdr")


class TestRegua(unittest.TestCase):
    def test_faca_de_recorte_nao_e_produto(self):
        esperado = {"itens": [
            {"material": {"valor": "Faca de recorte"}},
            {"material": {"valor": "Adesivo Leitoso Interm."}},
            {"material": {"valor": None}},
        ]}
        self.assertEqual(
            [i["material"]["valor"] for i in sem_faca_de_recorte(esperado)["itens"]],
            ["Adesivo Leitoso Interm.", None],
        )

    def test_acabamento_nao_separa_linhas_na_nota(self):
        # TROFEL: "110 verniz e recorte + 110 verniz" é o mesmo pedido que "220 verniz".
        from zcfreader.avaliacao_caminhos import comparar_tolerante

        def item(quantidade, acabamento):
            return {"quantidade": {"valor": quantidade}, "dimensoes": {"largura_mm": 18, "altura_mm": 21},
                    "material": {"valor": "Adesivo Leitoso Interm."}, "acabamento": {"valor": acabamento}}

        esperado = {"itens": [item(110, "Verniz + Recorte"), item(110, "Verniz")]}
        obtido = {"itens": [item(220, "Verniz")]}
        self.assertTrue(comparar_tolerante(obtido, esperado)["pedido_correto"])

    def test_so_soma_linhas_da_mesma_medida(self):
        # Peônias: 3x6 não entra na linha de 3x5. BETH: 5,3x5,3 e 5x5 são o mesmo "5 x 5cm".
        from zcfreader.avaliacao_caminhos import consolidar_linhas

        def item(quantidade, largura, altura):
            return {"quantidade": {"valor": quantidade}, "dimensoes": {"largura_mm": largura, "altura_mm": altura},
                    "material": {"valor": "adesivo"}}

        linhas = consolidar_linhas([item(50, 30, 50), item(40, 30, 60), item(93, 53, 53), item(31, 50, 50)])
        self.assertEqual([i["quantidade"]["valor"] for i in linhas], [50, 40, 124])

    def test_texto_livre_antigo_e_nome_do_portal_sao_o_mesmo_material(self):
        from zcfreader.avaliacao_caminhos import materiais_compativeis

        self.assertTrue(materiais_compativeis("Adesivo Fosco Blackout", "adesivo branco fosco blackout"))
        self.assertTrue(materiais_compativeis("Lona Brilho 440g", "Banner"))
        self.assertFalse(materiais_compativeis("Lona Brilho 440g", "Lona fosca"))
        self.assertFalse(materiais_compativeis(None, "adesivo"))

    def test_cdr_do_whatsapp_com_numero_entra_na_regua(self):
        with tempfile.TemporaryDirectory() as tmp:
            pasta = Path(tmp)
            _pacote(pasta, "a.zip", "arquivo-original/ADESIVO.cdr (1).zip", "c1", "s1")
            _pacote(pasta, "b.zip", "arquivo-original/outro.cdr.zip", "c2", "s2")
            _pacote(pasta, "c.zip", "arquivo-original/foto.png", "c3", "s3")
            self.assertEqual(sorted(c["caso_id"] for c in carregar_casos(pasta)), ["c1", "c2"])

    def test_pedido_fora_da_regua_nao_e_medido(self):
        with tempfile.TemporaryDirectory() as tmp:
            pasta = Path(tmp)
            _pacote(pasta, "a.zip", "arquivo-original/a.cdr", "c1", "s1")
            _pacote(pasta, "b.zip", "arquivo-original/b.cdr", "c2", "s2")
            (pasta / "fora_da_regua.txt").write_text("# grande demais\nc2  # Joyce\n", encoding="utf-8")
            self.assertEqual([c["caso_id"] for c in carregar_casos(pasta)], ["c1"])

    def test_gabarito_ajustado_tem_prioridade(self):
        with tempfile.TemporaryDirectory() as tmp:
            pasta = Path(tmp)
            self.assertIsNone(gabarito_ajustado(pasta, "c1"))
            (pasta / "gabarito").mkdir()
            (pasta / "gabarito" / "c1.json").write_text(json.dumps({"itens": [{"indice": 1}]}), encoding="utf-8")
            self.assertEqual(gabarito_ajustado(pasta, "c1"), {"itens": [{"indice": 1}]})


if __name__ == "__main__":
    unittest.main()
