"""Ponte entre a macro do CorelDRAW e a análise.

A macro chama:
    python -m zcfreader.ponte_corel <arquivo.cdr> <saida.txt> <regras|ia>

e lê o resultado em texto simples (Windows-1252, separado por TAB), que o VBA
lê sem bibliotecas extras. Uma linha por registro:

    INFO      camada   duracao_s   custo_usd
    ITEM      n  quantidade  largura_cm  altura_cm  material  acabamento  esquerda  direita  base  topo  situacao
    PERGUNTA  texto
    ERRO      mensagem

As coordenadas (cm) são as do arquivo, com origem no centro da página; a macro
converte para as do CorelDRAW. O resultado completo também é gravado em JSON ao
lado (<saida>.json), para a correção pelo Corel usar depois.

Modos:
- regras: sem IA e sem custo. Se as regras resolvem, é a resposta delas; se não,
  mostra os produtos prováveis das regras, marcados "a confirmar".
- ia: o mesmo fluxo em camadas do aplicativo (regras, depois a IA configurada).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from time import perf_counter


def _caixa_do_item(item: dict, candidatos: dict) -> dict | None:
    if item.get("caixa_cm"):
        return item["caixa_cm"]
    caixas = [candidatos[i]["caixa_cm"] for i in item.get("candidatos") or [] if i in candidatos]
    caixas += [
        {chave: valor / 10 for chave, valor in componente["caixa_mm"].items()}
        for componente in item.get("componentes") or [] if componente.get("caixa_mm")
    ]
    if not caixas:
        return None
    return {
        "esquerda": min(c["esquerda"] for c in caixas), "direita": max(c["direita"] for c in caixas),
        "base": min(c["base"] for c in caixas), "topo": max(c["topo"] for c in caixas),
    }


def _analisar_regras(caminho: Path, fatos: dict) -> dict:
    from .camadas import regras_resolvem, resultado_das_regras

    auditoria = fatos["auditoria_regional"]
    if regras_resolvem(auditoria):
        resultado = resultado_das_regras(auditoria)
        for item in resultado["itens"]:
            item["situacao"] = "regras"
        return {"itens": resultado["itens"], "perguntas_operador": [], "processamento": {"fluxo": "macro_corel", "camada_final": "regras"}}
    itens = []
    for regra in auditoria.get("itens") or []:
        if regra.get("papel") not in {"produto_confirmado", "produto_plausivel"}:
            continue
        itens.append({
            "indice": len(itens) + 1,
            "quantidade": {"valor": int(regra.get("quantidade_pedido") or regra.get("quantidade_desenhada") or 1)},
            "dimensoes": {"largura_mm": regra["largura_cm"] * 10, "altura_mm": regra["altura_cm"] * 10},
            "material": {"valor": regra.get("material")},
            "acabamento": {"valor": regra.get("acabamento")},
            "candidatos": [regra["candidato_id"]],
            "situacao": "a confirmar",
        })
    return {"itens": itens, "perguntas_operador": [], "processamento": {"fluxo": "macro_corel", "camada_final": "regras (a confirmar)"}}


def _analisar_ia(caminho: Path, fatos: dict) -> dict:
    from .camadas import interpretar_em_camadas
    from .configuracao import carregar_configuracao, obter_chave
    from .pedido import interpretar_pedido

    configuracao = carregar_configuracao()
    return interpretar_em_camadas(
        caminho, obter_chave("openrouter"), interpretar_pedido(caminho), fatos=fatos,
        modelo_rapido=configuracao["modelo_rapido"], modelo_forte=configuracao["modelo_forte"],
        custo_maximo_usd=configuracao["limite_pedido_usd"], url_servidor_local=configuracao["url_servidor_local"],
    )


def _campo(valor) -> str:
    texto = "" if valor is None else str(valor)
    return " ".join(texto.replace("\t", " ").split())


def _numero(valor) -> str:
    return f"{float(valor):.3f}"


def linhas_de_saida(resultado: dict, candidatos: dict, duracao_s: float) -> list[str]:
    processamento = resultado.get("processamento") or {}
    linhas = ["\t".join(["INFO", _campo(processamento.get("camada_final")), f"{duracao_s:.1f}",
                         f"{float(processamento.get('custo_usd') or 0):.4f}"])]
    for n, item in enumerate(resultado.get("itens") or [], 1):
        dimensoes = item.get("dimensoes") or {}
        caixa = _caixa_do_item(item, candidatos)
        coordenadas = [_numero(caixa[c]) for c in ("esquerda", "direita", "base", "topo")] if caixa else ["", "", "", ""]
        linhas.append("\t".join([
            "ITEM", str(n), _campo((item.get("quantidade") or {}).get("valor")),
            _numero((dimensoes.get("largura_mm") or 0) / 10), _numero((dimensoes.get("altura_mm") or 0) / 10),
            _campo((item.get("material") or {}).get("valor")), _campo((item.get("acabamento") or {}).get("valor")),
            *coordenadas, _campo(item.get("situacao") or ""),
        ]))
    for pergunta in resultado.get("perguntas_operador") or []:
        linhas.append("\t".join(["PERGUNTA", _campo(pergunta.get("pergunta") if isinstance(pergunta, dict) else pergunta)]))
    return linhas


_ORIGENS_VALIDAS = {"arquivo", "padrao_grafica", "faltou_no_pedido"}


def _numero_ou_none(texto: str) -> float | None:
    try:
        return float(texto.replace(",", "."))
    except (AttributeError, ValueError):
        return None


def resultado_corrigido(original: dict, linhas: list[str]) -> tuple[dict, str]:
    """Monta o resultado correto a partir do arquivo de correção escrito pela macro.

    Linhas (TAB):
        OBS   texto
        ITEM  n_original  quantidade  largura_cm  altura_cm  material  acabamento
              origem_quantidade  origem_material  origem_acabamento  peca  esquerda  direita  base  topo
              motivo  objetos
    ``n_original`` 0 = item novo; ``peca`` "corel" = peça escolhida selecionando no CorelDRAW.
    """
    from copy import deepcopy

    from .origem_campos import definir_origens

    originais = original.get("itens") or []
    itens, observacao = [], ""
    for linha in linhas:
        campos = linha.rstrip("\r\n").split("\t")
        if campos[0] == "OBS" and len(campos) > 1:
            observacao = campos[1].strip()
        if campos[0] != "ITEM" or len(campos) < 17:
            continue
        indice_original = int(campos[1] or 0)
        base = deepcopy(originais[indice_original - 1]) if 0 < indice_original <= len(originais) else {}
        item = base
        quantidade = int(float(campos[2] or 0) or 1)
        largura, altura = _numero_ou_none(campos[3]) or 0.0, _numero_ou_none(campos[4]) or 0.0
        antes_dim = base.get("dimensoes") or {}

        if (base.get("quantidade") or {}).get("valor") != quantidade:
            item["quantidade"] = {"valor": quantidade, "unidade": "unidade", "fonte": "correcao_operador", "confianca": 1.0}
        for campo, valor in (("material", campos[5]), ("acabamento", campos[6])):
            valor = valor.strip() or None
            if (base.get(campo) or {}).get("valor") != valor:
                item[campo] = {"valor": valor, "fonte": "correcao_operador", "confianca": 1.0}

        if campos[10] == "corel" or not antes_dim:
            item["dimensoes"] = {
                "largura_mm": round(largura * 10, 3), "altura_mm": round(altura * 10, 3),
                "tipo": "peca_indicada_pelo_operador", "fonte": "correcao_operador", "confianca": 1.0,
            }
        caixa = [_numero_ou_none(c) for c in campos[11:15]]
        if all(v is not None for v in caixa):
            item["caixa_cm"] = dict(zip(("esquerda", "direita", "base", "topo"), caixa))
        if campos[10] == "corel":
            item["peca_correta"] = {
                "origem": "selecao_corel", "largura_cm": largura, "altura_cm": altura,
                "objetos_corel": [o for o in campos[16].split(";") if o],
            }
            if base:
                item["peca_correta"]["antes"] = {
                    "ids": list(base.get("candidatos") or []),
                    "largura_cm": round((antes_dim.get("largura_mm") or 0) / 10, 3),
                    "altura_cm": round((antes_dim.get("altura_mm") or 0) / 10, 3),
                }
        if campos[15].strip():
            item["observacao_operador"] = campos[15].strip()
        origens = {
            campo: codigo for campo, codigo in zip(("quantidade", "material", "acabamento"), campos[7:10])
            if codigo in _ORIGENS_VALIDAS
        }
        itens.append(definir_origens(item, origens))
    correto = {k: v for k, v in original.items() if k != "itens"}
    correto["itens"] = itens
    return correto, observacao


def salvar_correcao(caminho: Path, arquivo_correcao: Path) -> Path:
    from .configuracao import carregar_configuracao
    from .relatorios import classificar_diferencas, gerar_pacote_diagnostico

    linhas = arquivo_correcao.read_text(encoding="cp1252").splitlines()
    original_json = next((l.split("\t", 1)[1] for l in linhas if l.startswith("ORIGINAL\t")), None)
    if not original_json or not Path(original_json).exists():
        raise FileNotFoundError("Resultado da análise não encontrado; analise o arquivo de novo antes de salvar.")
    dados = json.loads(Path(original_json).read_text(encoding="utf-8"))
    if Path(dados["arquivo"]).resolve() != Path(caminho).resolve():
        raise ValueError("A análise guardada é de outro arquivo; analise este arquivo de novo antes de salvar.")
    original = dados["resultado"]
    correto, observacao = resultado_corrigido(original, linhas)
    situacao = "corrigido" if classificar_diferencas(original, correto) else "confirmado"
    configuracao = carregar_configuracao()
    return gerar_pacote_diagnostico(
        Path(caminho), original, correto, situacao=situacao, observacao_operador=observacao,
        incluir_cdr=bool(configuracao.get("incluir_cdr_diagnostico", True)),
    )


def main(argumentos: list[str]) -> int:
    caminho, saida, modo = Path(argumentos[0]), Path(argumentos[1]), (argumentos[2] if len(argumentos) > 2 else "regras")
    if modo == "salvar":
        # Aqui "saida" é o arquivo de correção escrito pela macro; a resposta vai para <correcao>.ok
        try:
            linhas = ["\t".join(["OK", str(salvar_correcao(caminho, saida))])]
        except Exception as erro:
            linhas = ["\t".join(["ERRO", _campo(f"{type(erro).__name__}: {erro}")])]
        Path(str(saida) + ".ok").write_text("\r\n".join(linhas) + "\r\n", encoding="cp1252", errors="replace", newline="")
        return 0
    inicio = perf_counter()
    try:
        # O CorelDRAW aberto nunca é usado pela análise: o desenho vem do próprio arquivo.
        import zcfreader.visao_api as visao_api
        visao_api.renderizar_com_corel = lambda *a, **k: None
        from .agente import extrair_fatos

        fatos = extrair_fatos(caminho)
        resultado = _analisar_ia(caminho, fatos) if modo == "ia" else _analisar_regras(caminho, fatos)
        linhas = linhas_de_saida(resultado, fatos.get("candidatos") or {}, perf_counter() - inicio)
        Path(str(saida) + ".json").write_text(
            json.dumps({"arquivo": str(caminho), "modo": modo, "resultado": resultado}, ensure_ascii=False,
                       indent=2, default=str),
            encoding="utf-8",
        )
    except Exception as erro:  # a macro mostra a mensagem ao operador
        linhas = ["\t".join(["ERRO", _campo(f"{type(erro).__name__}: {erro}")])]
    saida.write_text("\r\n".join(linhas) + "\r\n", encoding="cp1252", errors="replace", newline="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
