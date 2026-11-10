"""CDR salvo em versão antiga (X5 ou anterior): o leitor avisa em vez de ler zero peças."""
from __future__ import annotations

import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from zcfreader.container import FormatoCdrAntigo, abrir_cdr, versao_antiga  # noqa: E402


def _cdr(pasta: Path, membros: dict[str, bytes]) -> Path:
    caminho = pasta / "pedido.cdr"
    with zipfile.ZipFile(caminho, "w") as pacote:
        for nome, dados in membros.items():
            pacote.writestr(nome, dados)
    return caminho


class TestFormatoAntigo(unittest.TestCase):
    def test_cdr_x5_e_reconhecido_e_nao_abre_vazio(self):
        # Pedido "cell1cdr" (10/11/2026): tudo em content/riffData.cdr, CoreVersion 1500.
        with tempfile.TemporaryDirectory() as tmp:
            caminho = _cdr(Path(tmp), {
                "mimetype": b"application/x-vnd.corel.zcf.draw.document+zip",
                "content/riffData.cdr": b"RIFF\x00\x00\x00\x00CDRF",
                "metadata/metadata.xml": b"<x><CoreVersion>1500</CoreVersion></x>",
            })
            self.assertEqual(versao_antiga(caminho), "CorelDRAW versão 15")
            with self.assertRaises(FormatoCdrAntigo):
                abrir_cdr(caminho)

    def test_cdr_atual_nao_e_antigo(self):
        with tempfile.TemporaryDirectory() as tmp:
            caminho = _cdr(Path(tmp), {"content/riffData.cdr": b"RIFF", "content/data/0.dat": b"RIFF"})
            self.assertIsNone(versao_antiga(caminho))

    def test_ponte_responde_antigo_para_a_macro_converter(self):
        from zcfreader.ponte_corel import main

        with tempfile.TemporaryDirectory() as tmp:
            caminho = _cdr(Path(tmp), {"content/riffData.cdr": b"RIFF",
                                       "metadata/metadata.xml": b"<CoreVersion>1500</CoreVersion>"})
            saida = Path(tmp) / "saida.txt"
            main([str(caminho), str(saida), "regras"])
            self.assertTrue(saida.read_text(encoding="cp1252").startswith("ANTIGO\t"))


if __name__ == "__main__":
    unittest.main()
