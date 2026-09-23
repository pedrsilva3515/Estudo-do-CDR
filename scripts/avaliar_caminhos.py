"""Mede cada caminho de interpretação nos pacotes revisados pelo operador.

Uso:
    $env:PYTHONPATH="fase3-parser"
    python scripts/avaliar_caminhos.py "$env:USERPROFILE\\Documents\\LeitorPedidosCDR\\Relatorios"

Caminhos:
    app_na_epoca        resultado-original.json gravado no pacote (versão usada na revisão)
    estrutural          interpretar_pedido() atual, sem IA
    estrutural_ia_salva estrutural atual + reconciliação com a resposta de IA salva no pacote
    regional            produtos da arquitetura regional experimental (sem IA)
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from zcfreader.avaliacao_caminhos import avaliar_caminhos, resultado_de_auditoria_regional
from zcfreader.experimento_agente import executar_arquitetura_regional
from zcfreader.pedido import interpretar_pedido
from zcfreader.visao_api import reconciliar_analise_visual

CAMINHOS = {
    "app_na_epoca": lambda cdr, pacote: json.loads(pacote.read("resultado-original.json")),
    "estrutural": lambda cdr, pacote: interpretar_pedido(cdr),
    "estrutural_ia_salva": lambda cdr, pacote: reconciliar_analise_visual(
        interpretar_pedido(cdr), json.loads(pacote.read("analise-visual.json")), fonte="modelo_local",
    ),
    "regional": lambda cdr, pacote: resultado_de_auditoria_regional(executar_arquitetura_regional(cdr)),
}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pasta", type=Path)
    parser.add_argument("--caminhos", nargs="+", choices=list(CAMINHOS), default=list(CAMINHOS))
    parser.add_argument("--saida", type=Path, help="grava o JSON completo")
    parser.add_argument("--sem-corel", action="store_true", help="usa o preview embutido em vez de abrir o CorelDRAW")
    args = parser.parse_args()
    if args.sem_corel:
        import zcfreader.visao_api as visao_api
        visao_api.renderizar_com_corel = lambda caminho, *a, **k: None
    resultado = avaliar_caminhos(args.pasta, {nome: CAMINHOS[nome] for nome in args.caminhos})
    if args.saida:
        args.saida.write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    largura = max(len(c["arquivo"]) for c in resultado["casos"])
    print(f"{'arquivo':<{largura}}  " + "  ".join(f"{n:>22}" for n in args.caminhos))
    for caso in resultado["casos"]:
        celulas = []
        for nome in args.caminhos:
            m = caso["metricas"][nome]
            if "erro" in m:
                celulas.append(f"{'ERRO':>22}")
                continue
            marca = "OK" if m["pedido_correto"] else "  "
            celulas.append(f"{marca} {m['linhas_corretas']}/{m['esperados']} +{m['a_mais']} -{m['faltando']}".rjust(22))
        print(f"{caso['arquivo']:<{largura}}  " + "  ".join(celulas))
    print("\n(linhas corretas/esperadas  +itens a mais  -itens faltando)\n")
    for nome, t in resultado["totais"].items():
        print(
            f"{nome:>20}: pedidos corretos {t['pedidos_corretos']}/{t['casos']}"
            f" | linhas {t['linhas_corretas']}/{t['esperados']}"
            f" | a mais {t['a_mais']} | faltando {t['faltando']}"
            f" | material {t['material_ok']}/{t['material_avaliado']}"
            + (f" | faltas no pedido percebidas {t['faltas_detectadas']}/{t['faltas_esperadas']} (chutes {t['chutes']})"
               if t.get("faltas_esperadas") else "")
            f" | acabamento {t['acabamento_ok']}/{t['acabamento_avaliado']}"
            + (f" | FALHAS {t['falhas']}" if t["falhas"] else "")
        )


if __name__ == "__main__":
    main()
