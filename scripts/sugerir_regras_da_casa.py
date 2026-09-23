r"""Sugere regras da casa a partir das correções marcadas como "Padrão da gráfica".

Uso:
    $env:PYTHONPATH="fase3-parser"
    python scripts/sugerir_regras_da_casa.py "$env:USERPROFILE\Documents\LeitorPedidosCDR\Relatorios"

Agrupa, em todos os pacotes de revisão, os valores que o operador preencheu sem
estarem no pedido por serem convenção da gráfica. Um valor que se repete é
candidato a virar regra em %APPDATA%\LeitorPedidosCDR\regras_da_casa.md. O script
só sugere; quem decide e escreve a regra é o operador. Mostra também quantos
campos faltaram no pedido, por tipo.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import json
from pathlib import Path
from zipfile import ZipFile

from zcfreader.origem_campos import campos_com_origem

ROTULOS = {"quantidade": "Quantidade", "medida": "Medida", "material": "Material", "acabamento": "Acabamento"}


def _valor(item: dict, campo: str):
    if campo == "medida":
        dim = item.get("dimensoes") or {}
        if dim.get("largura_mm") and dim.get("altura_mm"):
            return f"{dim['largura_mm'] / 10:g} x {dim['altura_mm'] / 10:g} cm"
        return None
    return (item.get(campo) or {}).get("valor")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pasta", type=Path)
    parser.add_argument("--minimo", type=int, default=2, help="repetições mínimas para sugerir uma regra")
    args = parser.parse_args()

    padroes: dict[tuple[str, str], list[str]] = defaultdict(list)
    faltas: Counter = Counter()
    for zip_path in sorted(args.pasta.glob("*.zip")):
        with ZipFile(zip_path) as pacote:
            if "resultado-correto.json" not in pacote.namelist():
                continue
            correto = json.loads(pacote.read("resultado-correto.json"))
            nome = json.loads(pacote.read("diagnostico.json"))["arquivo"]["nome"] if "diagnostico.json" in pacote.namelist() else zip_path.name
        for item in correto.get("itens", []):
            for campo in campos_com_origem(item, "padrao_grafica"):
                valor = _valor(item, campo)
                if valor:
                    padroes[(campo, str(valor).strip().casefold())].append(nome)
            for campo in campos_com_origem(item, "faltou_no_pedido"):
                faltas[campo] += 1

    print("SUGESTÕES DE REGRAS DA CASA (valores marcados como padrão da gráfica)\n")
    sugeridas = sorted(((len(arquivos), campo, valor, arquivos) for (campo, valor), arquivos in padroes.items()), reverse=True)
    if not sugeridas:
        print("  Nenhum campo marcado como 'Padrão da gráfica' ainda.")
    for vezes, campo, valor, arquivos in sugeridas:
        marca = "SUGERIDA" if vezes >= args.minimo else "observada"
        exemplos = ", ".join(dict.fromkeys(arquivos))[:120]
        print(f"  [{marca}] {ROTULOS[campo]} = {valor}  ({vezes}x) — ex.: {exemplos}")
        if vezes >= args.minimo:
            print(f"      Regra possível: \"Quando o pedido não informar {ROTULOS[campo].lower()}, use {valor}.\"")
    print("\nCAMPOS QUE FALTARAM NO PEDIDO (precisaram de contato com o cliente)")
    if not faltas:
        print("  Nenhum ainda.")
    for campo, vezes in faltas.most_common():
        print(f"  {ROTULOS[campo]}: {vezes}")


if __name__ == "__main__":
    main()
