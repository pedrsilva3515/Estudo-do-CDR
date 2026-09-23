r"""Mede o agente (fase 3) com um ou mais modelos do OpenRouter nos pacotes revisados.

Uso:
    $env:PYTHONPATH="fase3-parser"
    $env:OPENROUTER_API_KEY="..."   # ou a chave salva na janela Configurar IA
    python scripts/avaliar_agente.py "$env:USERPROFILE\Documents\LeitorPedidosCDR\Relatorios" `
        --modelos google/gemini-3.1-flash-lite --orcamento-usd 0.10 --rastros saida-agente

O caminho "regional" (regras, sem IA) entra como referência. Os fatos de cada
CDR (inclusive o render do CorelDRAW) são extraídos uma vez e reaproveitados
por todos os modelos.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import urllib.request

from zcfreader.agente import extrair_fatos, interpretar_com_agente
from zcfreader.camadas import interpretar_em_camadas
from zcfreader.pedido import interpretar_pedido
from zcfreader.avaliacao_caminhos import avaliar_caminhos, resultado_de_auditoria_regional
from zcfreader.configuracao import PREFIXO_LOCAL, URL_SERVIDOR_LOCAL_PADRAO, obter_chave
from zcfreader.experimento_agente import executar_arquitetura_regional


def precos_openrouter(modelos: list[str]) -> dict[str, tuple[float, float]]:
    """Preço público por token (entrada, saída), para estimar gasto se a resposta não o trouxer."""
    with urllib.request.urlopen("https://openrouter.ai/api/v1/models", timeout=30) as resposta:
        dados = json.load(resposta)["data"]
    precos = {}
    for modelo in dados:
        if modelo["id"] in modelos:
            preco = modelo.get("pricing") or {}
            precos[modelo["id"]] = (float(preco.get("prompt") or 0), float(preco.get("completion") or 0))
    return precos


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("pasta", type=Path)
    parser.add_argument("--modelos", nargs="*", default=[], help="IDs do OpenRouter (agente com um modelo só)")
    parser.add_argument("--camadas", nargs=2, metavar=("RAPIDO", "FORTE"),
                        help="também mede o fluxo em camadas com esses dois modelos")
    parser.add_argument("--casos", nargs="+", help="trechos do nome dos casos a incluir")
    parser.add_argument("--rastros", type=Path, help="pasta para gravar resultado e rastro de cada execução")
    parser.add_argument("--sem-corel", action="store_true", help="usa o preview embutido em vez do CorelDRAW")
    parser.add_argument("--orcamento-usd", type=float, default=0.30,
                        help="gasto total máximo desta execução; ao atingir, os pedidos seguintes não são enviados")
    parser.add_argument("--limite-pedido-usd", type=float, default=0.05, help="gasto máximo por pedido")
    parser.add_argument("--servidor-local", default=URL_SERVIDOR_LOCAL_PADRAO,
                        help="endereço do servidor compatível com a OpenAI para modelos 'local:<nome>'")
    args = parser.parse_args()

    chave = obter_chave("openrouter")
    todos = args.modelos + list(args.camadas or [])
    if not chave and any(not m.startswith(PREFIXO_LOCAL) for m in todos):
        parser.error("Chave do OpenRouter não encontrada (Configurar IA ou OPENROUTER_API_KEY).")
    if args.sem_corel:
        import zcfreader.visao_api as visao_api
        visao_api.renderizar_com_corel = lambda caminho, *a, **k: None
    if args.rastros:
        args.rastros.mkdir(parents=True, exist_ok=True)
    todos_modelos = [m for m in dict.fromkeys(todos) if not m.startswith(PREFIXO_LOCAL)]
    if not todos:
        parser.error("Informe --modelos e/ou --camadas.")
    precos = precos_openrouter(todos_modelos)
    desconhecidos = [m for m in todos_modelos if m not in precos]
    if desconhecidos:
        parser.error(f"Modelos não encontrados no OpenRouter: {', '.join(desconhecidos)}")

    fatos_por_arquivo: dict[str, dict] = {}
    custos: dict[str, float] = {}

    def fatos(cdr: Path) -> dict:
        if cdr.name not in fatos_por_arquivo:
            fatos_por_arquivo[cdr.name] = extrair_fatos(cdr)
        return fatos_por_arquivo[cdr.name]

    def executar_modelo(cdr: Path, modelo: str, limite: float | None) -> dict:
        """Roteia para o OpenRouter ou para o servidor local, conforme o prefixo do modelo."""
        if modelo.startswith(PREFIXO_LOCAL):
            return interpretar_com_agente(
                cdr, None, modelo[len(PREFIXO_LOCAL):], fatos=fatos(cdr),
                base_url=args.servidor_local, usar_ferramentas=False,
            )
        return interpretar_com_agente(
            cdr, chave, modelo, fatos=fatos(cdr), custo_maximo_usd=limite, preco_por_token=precos[modelo],
        )

    def caminho_agente(modelo: str):
        def executar(cdr: Path, _pacote) -> dict:
            gasto = sum(custos.values())
            if gasto >= args.orcamento_usd and not modelo.startswith(PREFIXO_LOCAL):
                raise RuntimeError(f"orçamento de US$ {args.orcamento_usd:.2f} atingido (gasto US$ {gasto:.4f})")
            try:
                resultado = executar_modelo(
                    cdr, modelo, min(args.limite_pedido_usd, args.orcamento_usd - gasto),
                )
            except Exception as erro:
                print(f"  ! {modelo} em {cdr.name}: {type(erro).__name__}: {erro}", flush=True)
                raise
            rastro = resultado.get("rastro_agente", {})
            custos[modelo] = custos.get(modelo, 0.0) + float(rastro.get("custo_usd") or 0)
            print(
                f"  {modelo:<32} {cdr.name[:45]:<45} {len(resultado['itens'])} itens, "
                f"{rastro.get('chamadas')} chamadas, {len(rastro.get('correcoes', []))} correções, "
                f"{rastro.get('duracao_s')} s, {rastro.get('tokens', {}).get('entrada', 0)} tokens de entrada, "
                f"US$ {rastro.get('custo_usd', 0):.4f}", flush=True,
            )
            if args.rastros:
                nome = re.sub(r"[^\w.-]+", "_", f"{Path(cdr.name).stem}__{modelo}")
                (args.rastros / f"{nome}.json").write_text(
                    json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8",
                )
            return resultado
        return executar

    def caminho_camadas(cdr: Path, _pacote) -> dict:
        gasto = sum(custos.values())
        if gasto >= args.orcamento_usd:
            raise RuntimeError(f"orçamento de US$ {args.orcamento_usd:.2f} atingido (gasto US$ {gasto:.4f})")

        def agente(caminho, chave_agente, modelo, fatos=None, custo_maximo_usd=None, base_url=None, usar_ferramentas=True):
            if base_url:  # já veio roteado para o servidor local
                return interpretar_com_agente(
                    caminho, chave_agente, modelo, fatos=fatos, base_url=base_url, usar_ferramentas=usar_ferramentas,
                )
            return interpretar_com_agente(
                caminho, chave_agente, modelo, fatos=fatos, custo_maximo_usd=custo_maximo_usd,
                preco_por_token=precos[modelo],
            )

        resultado = interpretar_em_camadas(
            cdr, chave, interpretar_pedido(cdr), modelo_rapido=args.camadas[0], modelo_forte=args.camadas[1],
            custo_maximo_usd=min(args.limite_pedido_usd, args.orcamento_usd - gasto),
            executar_agente=agente, fatos=fatos(cdr), url_servidor_local=args.servidor_local,
        )
        p = resultado["processamento"]
        custos["camadas"] = custos.get("camadas", 0.0) + p["custo_usd"]
        motivos = next((c.get("motivos_para_escalar") for c in p["camadas"] if c["camada"] == "modelo_rapido"), None)
        print(f"  {'camadas':<32} {cdr.name[:45]:<45} camada {p['camada_final']}, {len(resultado['itens'])} itens, "
              f"{p['duracao_s']} s, US$ {p['custo_usd']:.4f}" + (f", escalou: {motivos}" if motivos else ""), flush=True)
        if args.rastros:
            nome = re.sub(r"[^\w.-]+", "_", f"{Path(cdr.name).stem}__camadas")
            (args.rastros / f"{nome}.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return resultado

    caminhos = {"regional": lambda cdr, _p: resultado_de_auditoria_regional(executar_arquitetura_regional(cdr))}
    caminhos.update({modelo: caminho_agente(modelo) for modelo in args.modelos})
    if args.camadas:
        caminhos["camadas"] = caminho_camadas
    resultado = avaliar_caminhos(args.pasta, caminhos, somente=args.casos)

    print()
    largura = max(len(c["arquivo"]) for c in resultado["casos"])
    for caso in resultado["casos"]:
        celulas = []
        for nome in caminhos:
            m = caso["metricas"][nome]
            celulas.append("ERRO".rjust(16) if "erro" in m else
                           (("OK " if m["pedido_correto"] else "   ") + f"{m['linhas_corretas']}/{m['esperados']} +{m['a_mais']} -{m['faltando']}").rjust(16))
        print(f"{caso['arquivo']:<{largura}}  " + "  ".join(celulas))
    print("\n(linhas corretas/esperadas  +itens a mais  -itens faltando)\n")
    for nome, t in resultado["totais"].items():
        print(
            f"{nome:>32}: pedidos corretos {t['pedidos_corretos']}/{t['casos']}"
            f" | linhas {t['linhas_corretas']}/{t['esperados']} | a mais {t['a_mais']} | faltando {t['faltando']}"
            f" | material {t['material_ok']}/{t['material_avaliado']}"
            + (f" | faltas no pedido percebidas {t['faltas_detectadas']}/{t['faltas_esperadas']} (chutes {t['chutes']})"
               if t.get("faltas_esperadas") else "")
            + (f" | FALHAS {t['falhas']}" if t["falhas"] else "")
            + (f" | custo US$ {custos[nome]:.2f}" if nome in custos else "")
        )
    print(f"\nGasto total: US$ {sum(custos.values()):.4f}")
    if args.rastros:
        (args.rastros / "resumo.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
