r"""Refaz todos os pedidos revisados e avisa se algum piorou em relação à referência.

Uso:
    $env:PYTHONPATH="fase3-parser"
    python scripts/provas.py              # compara com a referência; sai com código 1 se algo piorou
    python scripts/provas.py --gravar     # aceita o resultado atual como nova referência

Só usa caminhos sem IA: é gratuito e dá sempre o mesmo resultado. A referência
fica em Documents\LeitorPedidosCDR\provas\referencia.json (fora do Git, porque
os pedidos são de clientes). Grave uma nova referência só depois de conferir
que as mudanças listadas são melhoras de verdade, ou quando entrarem pedidos
revisados novos.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import zcfreader.visao_api as visao_api
from zcfreader.provas import comparar_com_referencia, medir_pasta, totais
from zcfreader.relatorios import pasta_relatorios


def _versao() -> str:
    try:
        return subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True,
                              cwd=Path(__file__).resolve().parent, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return "desconhecida"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--pasta", type=Path, default=pasta_relatorios(), help="pasta com os pacotes revisados")
    parser.add_argument("--referencia", type=Path, default=pasta_relatorios().parent / "provas" / "referencia.json")
    parser.add_argument("--gravar", action="store_true", help="grava o resultado atual como nova referência")
    parser.add_argument("--casos", nargs="+", help="só os pedidos cujo nome contém algum destes trechos")
    args = parser.parse_args()

    # O CorelDRAW nunca participa das provas: o resultado tem que ser igual em qualquer máquina.
    visao_api.renderizar_com_corel = lambda *a, **k: None

    def progresso(nome, medidas):
        if "erro" in medidas:
            print(f"  ERRO  {nome}: {medidas['erro']}", flush=True)
        else:
            marca = "OK" if medidas["regras_pedido_correto"] else "  "
            print(f"  {marca}  {nome}  (peças certas visíveis {medidas['itens_com_peca']}/{medidas['itens_esperados']})",
                  flush=True)

    print(f"Refazendo os pedidos revisados de {args.pasta} ...")
    atual = medir_pasta(args.pasta, somente=args.casos, progresso=progresso)
    t = totais(atual)
    print(
        f"\n{t['pedidos']} pedidos | regras certas {t['regras_pedido_correto']} | linhas {t['regras_linhas_corretas']}/"
        f"{t['itens_esperados']} | a mais {t['regras_a_mais']} | faltando {t['regras_faltando']} | "
        f"regras decidem sozinhas {t['regras_decidem']} (erradas {t['regras_decidem_errado']}) | "
        f"peças para a IA {t['pecas_para_ia']} | itens com peça visível {t['itens_com_peca']}/{t['itens_esperados']}"
        + (f" | COM ERRO {t['com_erro']}" if t["com_erro"] else "")
    )

    if args.gravar:
        args.referencia.parent.mkdir(parents=True, exist_ok=True)
        if args.casos and args.referencia.exists():
            anterior = json.loads(args.referencia.read_text(encoding="utf-8"))["casos"]
            atual = {**anterior, **atual}
        args.referencia.write_text(json.dumps(
            {"versao": _versao(), "gravado_em": datetime.now().isoformat(timespec="seconds"), "casos": atual},
            ensure_ascii=False, indent=2,
        ) + "\n", encoding="utf-8")
        print(f"\nReferência gravada em {args.referencia}")
        return 0

    if not args.referencia.exists():
        print(f"\nAinda não há referência. Rode com --gravar para criar ({args.referencia}).")
        return 0
    dados = json.loads(args.referencia.read_text(encoding="utf-8"))
    referencia = dados["casos"]
    if args.casos:
        referencia = {n: m for n, m in referencia.items() if n in atual}
    diferencas = comparar_com_referencia(referencia, atual)
    print(f"\nComparação com a referência (versão {dados.get('versao')}, {dados.get('gravado_em')}):")
    for titulo, chave in (("PIOROU", "piorou"), ("melhorou", "melhorou")):
        for nome, mudancas in diferencas[chave].items():
            print(f"  {titulo:<8} {nome}: " + "; ".join(mudancas))
    for nome in diferencas["novos"]:
        print(f"  novo     {nome} (ainda não está na referência)")
    for nome in diferencas["sumiram"]:
        print(f"  sumiu    {nome} (está na referência mas o pacote não foi encontrado)")
    if not any(diferencas.values()):
        print("  nenhuma diferença")
    if diferencas["piorou"]:
        print(f"\n{len(diferencas['piorou'])} pedido(s) pioraram. A mudança não deve entrar assim.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
