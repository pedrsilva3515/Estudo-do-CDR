from __future__ import annotations

import argparse
import json
from pathlib import Path

from zcfreader.avaliacao import avaliar_pasta_relatorios


parser = argparse.ArgumentParser(description="Executa regressão nos relatórios revisados do Leitor CDR")
parser.add_argument("pasta", type=Path, help="Pasta Documentos/LeitorPedidosCDR/Relatorios")
parser.add_argument("--saida", type=Path, help="Arquivo JSON opcional")
args = parser.parse_args()
resultado = avaliar_pasta_relatorios(args.pasta)
texto = json.dumps(resultado, ensure_ascii=False, indent=2) + "\n"
if args.saida:
    args.saida.write_text(texto, encoding="utf-8")
print(texto)
