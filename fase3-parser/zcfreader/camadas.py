"""Interpretação em camadas: regras → modelo rápido → modelo forte → operador.

Cada camada só é acionada quando a anterior não resolve com segurança:

1. Regras regionais: aceitas sem IA apenas quando todas as peças visíveis são
   produtos confirmados (ou estruturas auxiliares) com quantidade escrita.
2. Modelo rápido e barato (agente com validador).
3. Modelo forte, quando o rápido faz perguntas, termina com erros de validação,
   não encontra itens ou contradiz um produto confirmado pelas regras.
4. O que continuar ambíguo vira pergunta para o operador.
"""
from __future__ import annotations

from copy import deepcopy
from pathlib import Path
from time import perf_counter

from .agente import extrair_fatos, interpretar_com_agente
from .configuracao import (
    LIMITE_PEDIDO_PADRAO_USD,
    MODELO_FORTE_PADRAO,
    MODELO_RAPIDO_PADRAO,
    PREFIXO_LOCAL,
    URL_SERVIDOR_LOCAL_PADRAO,
)


def regras_resolvem(auditoria: dict) -> bool:
    itens = auditoria.get("itens") or []
    produtos = [i for i in itens if i.get("papel") == "produto_confirmado"]
    return bool(produtos) and all(
        i.get("estado") == "estrutura_auxiliar"
        or (i.get("papel") == "produto_confirmado" and i.get("estado") == "confirmado_por_evidencia"
            and i.get("quantidade_pedido"))
        for i in itens
    ) and not auditoria.get("conflitos_fontes")


def _mesma_medida(item: dict, largura_cm: float, altura_cm: float, tolerancia_cm: float = 1.0) -> bool:
    dim = item.get("dimensoes") or {}
    w, h = float(dim.get("largura_mm") or 0) / 10, float(dim.get("altura_mm") or 0) / 10
    return min(abs(w - largura_cm) + abs(h - altura_cm), abs(w - altura_cm) + abs(h - largura_cm)) <= tolerancia_cm


def motivos_para_escalar(resultado: dict, auditoria: dict, fatos: dict | None = None) -> list[str]:
    motivos = []
    if not resultado.get("itens"):
        motivos.append("nenhum item encontrado")
    if resultado.get("perguntas"):
        motivos.append(f"{len(resultado['perguntas'])} pergunta(s) em aberto")
    erros = (resultado.get("rastro_agente") or {}).get("erros_restantes") or []
    if erros:
        motivos.append(f"{len(erros)} erro(s) de validação não corrigido(s)")
    candidatos = (fatos or {}).get("candidatos") or {}
    for item in resultado.get("itens") or []:
        # Pedir mais unidades que as peças desenhadas é comum (a arte se repete); pedir
        # menos (ex.: "9 impressões" com 12 cartões na folha) sugere que o produto é
        # outro nível da montagem, como a folha inteira.
        desenhadas = sum(int(candidatos.get(i, {}).get("quantidade_geometrica") or 1) for i in item.get("candidatos") or [])
        quantidade = (item.get("quantidade") or {}).get("valor") or 0
        if quantidade and quantidade < desenhadas:
            motivos.append(f"quantidade {quantidade} menor que as {desenhadas} peças desenhadas")
    for regra in auditoria.get("itens") or []:
        if regra.get("papel") != "produto_confirmado" or not regra.get("quantidade_pedido"):
            continue
        confirmado = any(
            _mesma_medida(item, regra["largura_cm"], regra["altura_cm"])
            and (item.get("quantidade") or {}).get("valor") == regra["quantidade_pedido"]
            for item in resultado.get("itens") or []
        )
        if not confirmado:
            motivos.append(
                f"contradiz a regra confirmada {regra['candidato_id']} "
                f"({regra['quantidade_pedido']} un de {regra['largura_cm']:g} x {regra['altura_cm']:g} cm)"
            )
    return motivos


def resultado_das_regras(auditoria: dict) -> dict:
    itens = []
    for regra in auditoria.get("itens") or []:
        if regra.get("papel") != "produto_confirmado":
            continue
        evidencia = next((e.get("texto") for e in regra.get("evidencias") or [] if e.get("texto")), None)
        itens.append({
            "indice": len(itens) + 1,
            "quantidade": {"valor": int(regra["quantidade_pedido"]), "fonte": "regras_regionais", "confianca": 0.95},
            "dimensoes": {
                "largura_mm": round(regra["largura_cm"] * 10, 2), "altura_mm": round(regra["altura_cm"] * 10, 2),
                "fonte": "geometria_cdr", "confianca": 0.98,
            },
            "material": {"valor": regra.get("material"), "fonte": "regras_regionais", "confianca": 0.9, "texto_origem": evidencia},
            "acabamento": {"valor": regra.get("acabamento"), "fonte": "regras_regionais", "confianca": 0.9},
            "candidatos": [regra["candidato_id"]],
        })
    return {"itens": itens, "perguntas": []}


def _resumo_itens(resultado: dict) -> list[str]:
    return [
        f"{(i.get('quantidade') or {}).get('valor')} x {(i.get('dimensoes') or {}).get('largura_mm', 0) / 10:g}"
        f" x {(i.get('dimensoes') or {}).get('altura_mm', 0) / 10:g} cm {(i.get('material') or {}).get('valor') or ''}".strip()
        for i in resultado.get("itens") or []
    ]


def _com_confianca(itens: list[dict], confianca: float) -> list[dict]:
    for item in itens:
        for campo in ("quantidade", "material", "acabamento"):
            item.setdefault(campo, {}).setdefault("confianca", confianca)
        item.setdefault("dimensoes", {}).setdefault("confianca", 0.98)
        item.setdefault("componentes", [])
    return itens


def interpretar_em_camadas(
    caminho: Path,
    chave: str | None,
    resultado_estrutural: dict,
    modelo_rapido: str = MODELO_RAPIDO_PADRAO,
    modelo_forte: str | None = MODELO_FORTE_PADRAO,
    custo_maximo_usd: float = LIMITE_PEDIDO_PADRAO_USD,
    executar_agente=interpretar_com_agente,
    fatos: dict | None = None,
    url_servidor_local: str = URL_SERVIDOR_LOCAL_PADRAO,
) -> dict:
    """Devolve o resultado estrutural com os itens da camada que resolveu o pedido."""
    inicio = perf_counter()
    fatos = fatos or extrair_fatos(Path(caminho))
    auditoria = fatos["auditoria_regional"]
    resultado = deepcopy(resultado_estrutural)
    resultado["itens_estruturais"] = resultado.get("itens", [])
    resultado.setdefault("alertas", [])
    processamento = {"fluxo": "camadas", "camadas": [], "custo_usd": 0.0, "modelos": []}

    def finalizar(escolhido: dict, camada: str, confianca: float) -> dict:
        resultado["itens"] = _com_confianca(deepcopy(escolhido.get("itens") or []), confianca)
        for indice, item in enumerate(resultado["itens"], 1):
            item["indice"] = indice
        resultado["total_unidades"] = sum((i.get("quantidade") or {}).get("valor") or 0 for i in resultado["itens"])
        resultado["perguntas_operador"] = escolhido.get("perguntas") or []
        for pergunta in resultado["perguntas_operador"]:
            resultado["alertas"].append({
                "codigo": "PERGUNTA_AO_OPERADOR", "severidade": "revisao", "mensagem": pergunta.get("pergunta", ""),
            })
        resultado["pendencias"] = [
            campo for campo in ("material", "acabamento")
            if any(not (i.get(campo) or {}).get("valor") for i in resultado["itens"])
        ]
        if resultado["perguntas_operador"]:
            resultado["pendencias"].append("perguntas")
        processamento["camada_final"] = camada
        processamento["duracao_s"] = round(perf_counter() - inicio, 1)
        processamento["custo_usd"] = round(processamento["custo_usd"], 5)
        resultado["processamento"] = processamento
        resultado["analise_regional_experimental"] = auditoria
        return resultado

    # 1. Regras
    if regras_resolvem(auditoria):
        processamento["camadas"].append({"camada": "regras", "aceita": True})
        return finalizar(resultado_das_regras(auditoria), "regras", 0.95)
    processamento["camadas"].append({"camada": "regras", "aceita": False})
    if not chave and not str(modelo_rapido).startswith(PREFIXO_LOCAL):
        resultado["alertas"].append({
            "codigo": "AGENTE_SEM_CHAVE", "severidade": "revisao",
            "mensagem": "As regras não resolveram o pedido e não há chave do OpenRouter; mantida a leitura estrutural.",
        })
        return finalizar(resultado_estrutural, "estrutural", 0.7)

    # 2. Modelo rápido
    def rodar(modelo: str, limite: float) -> dict:
        if modelo.startswith(PREFIXO_LOCAL):
            # Modelo no servidor local: sem chave, sem custo e sem ferramentas.
            saida = executar_agente(
                Path(caminho), None, modelo[len(PREFIXO_LOCAL):], fatos=fatos, custo_maximo_usd=None,
                base_url=url_servidor_local, usar_ferramentas=False,
            )
        else:
            saida = executar_agente(Path(caminho), chave, modelo, fatos=fatos, custo_maximo_usd=limite)
        rastro = saida.get("rastro_agente") or {}
        processamento["custo_usd"] += float(rastro.get("custo_usd") or 0)
        processamento["modelos"].append(modelo)
        return saida

    try:
        rapido = rodar(modelo_rapido, custo_maximo_usd)
    except Exception as erro:
        processamento["camadas"].append({"camada": "modelo_rapido", "modelo": modelo_rapido, "erro": str(erro)})
        rapido = None
        motivos = [f"falha do modelo rápido: {erro}"]
    else:
        motivos = motivos_para_escalar(rapido, auditoria, fatos)
        processamento["camadas"].append({
            "camada": "modelo_rapido", "modelo": modelo_rapido, "motivos_para_escalar": motivos,
            "itens": _resumo_itens(rapido),
        })
    if rapido is not None and not motivos:
        return finalizar(rapido, "modelo_rapido", 0.85)
    if not modelo_forte:
        if rapido is None:
            raise RuntimeError(processamento["camadas"][-1]["erro"])
        return finalizar(rapido, "modelo_rapido", 0.7)

    # 3. Modelo forte
    restante = max(custo_maximo_usd - processamento["custo_usd"], 0.0)
    try:
        forte = rodar(modelo_forte, restante)
    except Exception as erro:
        processamento["camadas"].append({"camada": "modelo_forte", "modelo": modelo_forte, "erro": str(erro)})
        if rapido is None:
            raise
        resultado["alertas"].append({
            "codigo": "MODELO_FORTE_FALHOU", "severidade": "revisao",
            "mensagem": f"O modelo de reforço falhou ({erro}); resultado do modelo rápido mantido para revisão.",
        })
        return finalizar(rapido, "modelo_rapido", 0.7)
    motivos_forte = motivos_para_escalar(forte, auditoria, fatos)
    processamento["camadas"].append({
        "camada": "modelo_forte", "modelo": modelo_forte, "motivos_restantes": motivos_forte,
        "itens": _resumo_itens(forte),
    })
    if rapido is not None and sorted(_resumo_itens(rapido)) != sorted(_resumo_itens(forte)):
        resultado["alertas"].append({
            "codigo": "MODELOS_DIVERGEM", "severidade": "revisao",
            "mensagem": "Os modelos rápido e forte chegaram a listas diferentes; confira os itens.",
        })
    for motivo in motivos_forte:
        if motivo.startswith("contradiz"):
            resultado["alertas"].append({"codigo": "AGENTE_CONTRADIZ_REGRA", "severidade": "revisao", "mensagem": motivo})
    return finalizar(forte, "modelo_forte", 0.8)
