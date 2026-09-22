"""Testes do prazo e do cache da renderização pelo CorelDRAW."""
from __future__ import annotations

import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

_AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(_AQUI.parent))

from zcfreader import render_corel  # noqa: E402


class TestRenderCorel(unittest.TestCase):
    def setUp(self):
        render_corel._cache.clear()
        pasta = tempfile.TemporaryDirectory()
        self.addCleanup(pasta.cleanup)
        self.cdr = Path(pasta.name) / "pedido.cdr"
        self.cdr.write_bytes(b"x")

    def test_corel_travado_expira_e_encerra_somente_instancia_nova(self):
        liberar = threading.Event()
        self.addCleanup(liberar.set)
        pids = iter([{100}, {100, 200}])
        with mock.patch.object(render_corel, "_renderizar", side_effect=lambda *a: liberar.wait(5)), \
             mock.patch.object(render_corel, "_pids_corel", side_effect=lambda: next(pids)), \
             mock.patch.object(render_corel, "_encerrar", side_effect=lambda p: liberar.set()) as encerrar:
            self.assertIsNone(render_corel.renderizar_com_corel(self.cdr, tempo_limite_s=0.05))
        encerrar.assert_called_once_with({200})

    def test_render_e_memorizado_por_arquivo(self):
        with mock.patch.object(render_corel, "_renderizar", return_value=b"png") as renderizar, \
             mock.patch.object(render_corel, "_pids_corel", return_value=set()):
            self.assertEqual(render_corel.renderizar_com_corel(self.cdr), b"png")
            self.assertEqual(render_corel.renderizar_com_corel(self.cdr), b"png")
        self.assertEqual(renderizar.call_count, 1)


if __name__ == "__main__":
    unittest.main()
