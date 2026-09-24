"""Peças dentro de um PowerClip são partes dele, não produtos na lista principal."""
from __future__ import annotations

import sys
import unittest
from pathlib import Path

_AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(_AQUI.parent))

from zcfreader.experimento_agente import _anotar_hierarquia  # noqa: E402


def _cand(cid, e, d, b, t, origem="uniao_grupo_sem_textos", ocorrencias=1):
    return {"id": cid, "origem": origem, "quantidade_geometrica": ocorrencias,
            "largura_cm": d - e, "altura_cm": t - b, "caixa_cm": {"esquerda": e, "direita": d, "base": b, "topo": t}}


class TestHierarquiaPowerClip(unittest.TestCase):
    def test_metades_internas_do_powerclip_saem_da_lista_principal(self):
        # Capa de 39,75 x 27 (PowerClip) com duas metades internas, como em LIVIA_E_MUNDI.
        candidatos = [_cand("A61", 49.19, 88.94, -8.85, 18.15), _cand("A66", 50.30, 65.90, -8.86, 18.13),
                      _cand("A67", 67.60, 88.90, -8.04, 18.14, origem="objetos_mesma_medida")]
        _anotar_hierarquia(candidatos, [{"esquerda": 49.2, "direita": 88.9, "base": -8.9, "topo": 18.1}])
        visiveis = [c["id"] for c in candidatos if c["visivel_inicialmente"]]
        self.assertEqual(visiveis, ["A61"])
        self.assertEqual(sorted(candidatos[0]["filhos_ids"]), ["A66", "A67"])  # continuam investigáveis

    def test_conteudo_quase_do_tamanho_da_mascara_e_parte_dela(self):
        # Arte rosa: máscara de 29 x 45,5 e conteúdo de 29 x 43,88 com faixas internas.
        candidatos = [_cand("A01", -14.04, 14.96, -20.79, 24.71, origem="caixa_externa_rasa"),
                      _cand("A03", -14.04, 14.96, -19.45, 24.43),
                      _cand("A04", -14.04, 14.96, -2.12, 24.43, origem="objetos_mesma_medida", ocorrencias=4)]
        _anotar_hierarquia(candidatos, [{"esquerda": -14.04, "direita": 14.96, "base": -20.79, "topo": 24.71}])
        self.assertEqual([c["id"] for c in candidatos if c["visivel_inicialmente"]], ["A01"])

    def test_montagem_sem_powerclip_continua_mostrando_os_produtos_internos(self):
        # Folha com dois adesivos, sem PowerClip: os produtos internos seguem visíveis.
        candidatos = [_cand("A01", 0, 100, 0, 50), _cand("A02", 5, 45, 5, 45), _cand("A03", 55, 95, 5, 45)]
        _anotar_hierarquia(candidatos, [])
        self.assertEqual([c["id"] for c in candidatos if c["visivel_inicialmente"]], ["A01", "A02", "A03"])


if __name__ == "__main__":
    unittest.main()
