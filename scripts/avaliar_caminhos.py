"""Mede cada caminho de interpretação nos pacotes revisados pelo operador.

Uso:
    $env:PYTHONPATH="fase3-parser"
    python scripts/avaliar_caminhos.py "$env:USERPROFILE\\Documents\\LeitorPedidosCDR\\Relatorios"

Caminhos:
    app_na_epoca        resultado-original.json gravado no pacote (versão usada na revisão)
    estrutural          interpretar_pedido() atual, sem IA
    estrutural_ia_salva estrutural atual + reconciliação com a resposta de IA salva no pacote
    regional            produtos da arquitetura regional experimental (sem IA)
    macro               o que a macro do CorelDRAW mostra no botão sem IA (ponte_corel, modo regras)

Respostas certas ajustadas depois da revisão ficam em <pasta>/gabarito/<caso_id>.json.
Use --saida para guardar uma rodada e --comparar <rodada anterior> para ver quais
pedidos melhoraram ou pioraram. A leitura dos CDR fica em cache (<pasta>/_cache_leitura):
a primeira rodada lê tudo, as seguintes só o que mudou; --sem-cache lê do zero.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from zcfreader.avaliacao_caminhos import avaliar_caminhos, resultado_de_auditoria_regional
from zcfreader.experimento_agente import executar_arquitetura_regional
from zcfreader.pedido import interpretar_pedido
from zcfreader.visao_api import reconciliar_analise_visual

def _macro(cdr: Path, pacote) -> dict:
    from zcfreader import ponte_corel
    from zcfreader.agente import extrair_fatos

    fatos = extrair_fatos(cdr)
    resultado = ponte_corel._analisar_regras(cdr, fatos)
    ponte_corel.separar_ocorrencias(resultado, fatos.get("candidatos") or {}, fatos.get("auditoria_regional"))
    return ponte_corel.aplicar_catalogo(resultado)


CAMINHOS = {
    "app_na_epoca": lambda cdr, pacote: json.loads(pacote.read("resultado-original.json")),
    "estrutural": lambda cdr, pacote: interpretar_pedido(cdr),
    "estrutural_ia_salva": lambda cdr, pacote: reconciliar_analise_visual(
        interpretar_pedido(cdr), json.loads(pacote.read("analise-visual.json")), fonte="modelo_local",
    ),
    "regional": lambda cdr, pacote: resultado_de_auditoria_regional(executar_arquitetura_regional(cdr)),
    "macro": _macro,
}


def _comparar_rodadas(anterior: dict, atual: dict) -> None:
    """Lista os pedidos que mudaram de certo para errado (e vice-versa) entre duas rodadas."""
    antes = {c.get("caso_id") or c["arquivo"]: c for c in anterior["casos"]}
    for nome in atual["totais"]:
        pioraram, melhoraram = [], []
        for caso in atual["casos"]:
            velho = (antes.get(caso.get("caso_id") or caso["arquivo"]) or {}).get("metricas", {}).get(nome)
            novo = caso["metricas"][nome]
            if not velho or "erro" in velho or "erro" in novo:
                continue
            if velho["pedido_correto"] and not novo["pedido_correto"]:
                pioraram.append(caso["arquivo"])
            elif novo["pedido_correto"] and not velho["pedido_correto"]:
                melhoraram.append(caso["arquivo"])
        print(f"\n{nome}: melhoraram {len(melhoraram)} | PIORARAM {len(pioraram)}")
        for arquivo in melhoraram:
            print(f"   + {arquivo}")
        for arquivo in pioraram:
            print(f"   - {arquivo}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pasta", type=Path)
    parser.add_argument("--caminhos", nargs="+", choices=list(CAMINHOS), default=list(CAMINHOS))
    parser.add_argument("--saida", type=Path, help="grava o JSON completo")
    parser.add_argument("--sem-corel", action="store_true", help="usa o preview embutido em vez de abrir o CorelDRAW")
    parser.add_argument("--comparar", type=Path, help="JSON de uma rodada anterior (--saida) para comparar")
    parser.add_argument("--somente", nargs="+", help="só os pedidos cujo nome contém algum destes trechos")
    parser.add_argument("--cache", type=Path,
                        help="pasta do cache da leitura dos CDR (padrão: <pasta>/_cache_leitura)")
    parser.add_argument("--sem-cache", action="store_true", help="lê todos os CDR do zero")
    args = parser.parse_args()
    if not args.sem_cache:
        # Peças, desenho da página e OCR só são refeitos quando o arquivo ou o código que os produz muda.
        from zcfreader.cache_leitura import ativar

        ativar(args.cache or args.pasta / "_cache_leitura")
    if args.sem_corel:
        import zcfreader.visao_api as visao_api
        visao_api.renderizar_com_corel = lambda caminho, *a, **k: None
    if "macro" in args.caminhos:
        # A macro nunca usa o CorelDRAW aberto: o desenho vem do próprio arquivo.
        import zcfreader.visao_api as visao_api
        visao_api.renderizar_com_corel = lambda caminho, *a, **k: None
    resultado = avaliar_caminhos(args.pasta, {nome: CAMINHOS[nome] for nome in args.caminhos}, args.somente)
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
            f" | acabamento {t['acabamento_ok']}/{t['acabamento_avaliado']}"
            + (f" | faltas no pedido percebidas {t['faltas_detectadas']}/{t['faltas_esperadas']} (chutes {t['chutes']})"
               if t.get("faltas_esperadas") else "")
            + (f" | FALHAS {t['falhas']}" if t["falhas"] else "")
        )

    if args.comparar:
        _comparar_rodadas(json.loads(args.comparar.read_text(encoding="utf-8")), resultado)


if __name__ == "__main__":
    main()
