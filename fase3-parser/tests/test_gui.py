from __future__ import annotations

import unittest

from zcfreader.gui import coletar_conflitos


class TestConflitosInterface(unittest.TestCase):
    def test_reune_conflito_regional_e_preserva_evidencia(self):
        resultado = {
            "materiais_regionais": [{
                "candidato_id": "A01",
                "conflitos": [{"campo": "material", "valores": ["adesivo", "banner"]}],
                "evidencias": [{"texto": "BANNER"}, {"texto": "ADESIVO"}],
            }],
        }

        conflitos = coletar_conflitos(resultado)

        self.assertEqual(len(conflitos), 1)
        self.assertEqual(conflitos[0]["candidato_id"], "A01")
        self.assertEqual(conflitos[0]["valores"], ["adesivo", "banner"])
        self.assertEqual([item["texto"] for item in conflitos[0]["evidencias"]], ["BANNER", "ADESIVO"])

    def test_remove_conflito_duplicado(self):
        conflito = {
            "candidato_id": "A01", "campo": "acabamento",
            "valor_do_arquivo": "sem recorte", "valor_confirmado": "recorte especial",
        }
        resultado = {"conflitos_revisao": [conflito, dict(conflito)]}

        self.assertEqual(coletar_conflitos(resultado), [conflito])


if __name__ == "__main__":
    unittest.main()
