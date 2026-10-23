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

    def test_gabarito_ajustado_tem_prioridade(self):
        with tempfile.TemporaryDirectory() as tmp:
            pasta = Path(tmp)
            self.assertIsNone(gabarito_ajustado(pasta, "c1"))
            (pasta / "gabarito").mkdir()
            (pasta / "gabarito" / "c1.json").write_text(json.dumps({"itens": [{"indice": 1}]}), encoding="utf-8")
            self.assertEqual(gabarito_ajustado(pasta, "c1"), {"itens": [{"indice": 1}]})


if __name__ == "__main__":
    unittest.main()
