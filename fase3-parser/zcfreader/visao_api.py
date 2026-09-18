"""Leitura visual e reconciliação de hipóteses do pedido (fluxo 0.7)."""
from __future__ import annotations

import base64
from copy import deepcopy
import json
from pathlib import Path

from .container import abrir_cdr
from .ocr import executar_ocr
from .render_corel import renderizar_com_corel


def extrair_preview(caminho: Path) -> tuple[bytes, str] | None:
    with abrir_cdr(caminho) as doc:
        nomes = doc.namelist()
        preferencias = ("previews/thumbnail.png", "previews/page1.png", "metadata/thumbnails/thumbnail.png", "metadata/thumbnails/page1.png")
        membro = next((nome for nome in preferencias if nome in nomes), None)
        if membro is None:
            membro = next((nome for nome in nomes if nome.casefold().endswith(".png") and "preview" in nome.casefold()), None)
        return (doc.read(membro), "image/png") if membro else None


def extrair_imagem_analise(caminho: Path) -> tuple[bytes, str, str] | None:
    """Prefere render nítido do Corel; mantém operação independente como fallback."""
    render = renderizar_com_corel(caminho)
    if render:
        return render, "image/png", "coreldraw_alta_resolucao"
    preview = extrair_preview(caminho)
    return (*preview, "preview_embutido") if preview else None


def _schema_resposta() -> dict:
    """Contrato completo: a visão pode contestar, criar ou remover itens."""
    item = {
        "type": "object", "additionalProperties": False,
        "properties": {
            "indice": {"type": "integer"}, "quantidade": {"type": ["integer", "null"]},
            "largura_cm": {"type": ["number", "null"]}, "altura_cm": {"type": ["number", "null"]},
            "material": {"type": ["string", "null"]}, "acabamento": {"type": ["string", "null"]},
            "evidencia": {"type": ["string", "null"]},
            "confianca": {"type": "number", "minimum": 0, "maximum": 1},
        },
        "required": ["indice", "quantidade", "largura_cm", "altura_cm", "material", "acabamento", "evidencia", "confianca"],
    }
    instrucao = {
        "type": "object", "additionalProperties": False,
        "properties": {
            "texto": {"type": "string"}, "quantidade": {"type": ["integer", "null"]},
            "largura_cm": {"type": ["number", "null"]}, "altura_cm": {"type": ["number", "null"]},
        },
        "required": ["texto", "quantidade", "largura_cm", "altura_cm"],
    }
    return {
        "type": "object", "additionalProperties": False,
        "properties": {
            "estrutura_confere": {"type": "string", "enum": ["sim", "nao", "incerto"]},
            "documento_misto": {"type": "boolean"},
            "instrucoes_visuais": {"type": "array", "items": instrucao},
            "itens": {"type": "array", "items": item},
            "observacoes": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["estrutura_confere", "documento_misto", "instrucoes_visuais", "itens", "observacoes"],
    }


def prompt_analise_visual(resultado_estrutural: dict) -> str:
    evidencias = json.dumps(resultado_estrutural, ensure_ascii=False, separators=(",", ":"))
    return (
        "Interprete a página inteira como um pedido de produção gráfica. ANTES de olhar o JSON, faça um "
        "inventário visual em instrucoes_visuais de TODAS as legendas no padrão 'N UN', 'N UND' ou "
        "'N UNI DE CADA', copiando o texto e os números, e percorrendo "
        "a imagem de cima para baixo e da esquerda para a direita. Cada legenda pode representar um item "
        "ausente do JSON, especialmente quando foi convertida em curvas. Nunca devolva quantidade null se "
        "uma quantidade UN estiver legível na imagem ou nas evidências. Leia instruções visíveis, inclusive "
        "texto convertido em curvas ou rotacionado. Associe quantidade, dimensão, material e acabamento "
        "somente à arte próxima. Detecte grades e repetições. Diferencie texto da própria arte (telefone, "
        "preço, nome) de instrução de produção. Nome do arquivo e JSON são hipóteses, não verdade. Pode criar, "
        "remover ou reagrupar itens. Separe materiais em documentos mistos. Dimensões escritas têm prioridade; "
        "a geometria pode incluir bordas ou objetos auxiliares. Retorne a lista COMPLETA. Use estrutura_confere "
        "'nao' quando a lista estrutural precisar ser substituída, 'sim' quando tiver os mesmos itens, ou "
        "'incerto'. Não invente informação ilegível: use null. Em evidencia, cite brevemente o texto ou padrão "
        "visual que sustenta o item. Evidências estruturais: " + evidencias
    )


def prompt_mapa_visual(nome_arquivo: str, ocr_visual: list[dict]) -> str:
    """Primeira leitura deliberadamente independente, para evitar ancoragem."""
    ocr = json.dumps(ocr_visual, ensure_ascii=False, separators=(",", ":"))
    return (
        "Faça uma primeira leitura independente deste pedido de gráfica. Você NÃO recebeu candidatos nem "
        "geometria do CDR. Conte apenas produtos/peças imprimíveis; linhas, colchetes, molduras e textos são "
        "instruções ou auxiliares, não produtos. Percorra a página de cima para baixo e da esquerda para a "
        "direita. Associe cabeçalhos de material e legendas de quantidade às peças abaixo. 'N DE CADA' aplica "
        "N unidades a cada peça distinta dentro da região indicada. Não estime dimensões pela aparência: use "
        "null quando elas não estiverem escritas. Retorne um item para cada produto distinto e descreva sua "
        "posição em evidencia. Como não há estrutura para conferir, use estrutura_confere='incerto'. "
        f"Nome do arquivo (somente contexto): {nome_arquivo}. OCR com posições: {ocr}"
    )


def analisar_com_openai(caminho: Path, resultado_estrutural: dict | None, chave: str, modelo: str, mapa_inicial: dict | None = None) -> dict:
    from openai import OpenAI
    preview = extrair_imagem_analise(caminho)
    if preview is None:
        raise RuntimeError("O CDR não contém um preview PNG utilizável pela análise visual.")
    bytes_imagem, mime, _origem = preview
    ocr_visual = executar_ocr(bytes_imagem)
    if resultado_estrutural is None:
        prompt = prompt_mapa_visual(caminho.name, ocr_visual)
        fase = "mapa_visual_inicial"
    else:
        evidencias = deepcopy(resultado_estrutural)
        evidencias["ocr_visual"] = ocr_visual
        if mapa_inicial is not None:
            evidencias["mapa_visual_inicial"] = mapa_inicial
        prompt = prompt_analise_visual(evidencias)
        fase = "adjudicacao"
    url_imagem = f"data:{mime};base64,{base64.b64encode(bytes_imagem).decode('ascii')}"
    resposta = OpenAI(api_key=chave).responses.create(
        model=modelo, store=False,
        input=[{"role": "user", "content": [
            {"type": "input_text", "text": prompt},
            {"type": "input_image", "image_url": url_imagem, "detail": "high"},
        ]}],
        text={"format": {"type": "json_schema", "name": "pedido_cdr_v07", "strict": True, "schema": _schema_resposta()}},
        max_output_tokens=2600,
    )
    resultado = normalizar_mapa_visual(json.loads(resposta.output_text))
    resultado["_imagem_origem"] = _origem
    resultado["_ocr_visual"] = ocr_visual
    resultado["_fase"] = fase
    return resultado


def precisa_adjudicacao(resultado_estrutural: dict, mapa_visual: dict) -> bool:
    """Detecta divergência objetiva antes de gastar uma segunda chamada de IA."""
    propostas = mapa_visual.get("itens") or []
    itens = resultado_estrutural.get("itens") or []
    if propostas and len(propostas) != len(itens):
        return True
    for estrutural, visual in zip(itens, propostas):
        qtd_visual = visual.get("quantidade")
        qtd_estrutural = estrutural.get("quantidade", {}).get("valor")
        if qtd_visual and qtd_estrutural and qtd_visual != qtd_estrutural:
            return True
    return False


def normalizar_mapa_visual(mapa: dict) -> dict:
    """Converte contagem de desenhos em unidades quando a legenda é explícita."""
    from .pedido import parse_material, parse_quantidade

    normalizados = []
    for item in mapa.get("itens") or []:
        evidencia = str(item.get("evidencia") or "")
        instrucao = parse_quantidade(evidencia)
        atual = item.get("quantidade")
        if instrucao and "de cada" in evidencia.casefold() and isinstance(atual, int) and 1 < atual <= 20 and atual != instrucao[0]:
            for numero in range(atual):
                copia = deepcopy(item)
                copia["quantidade"] = instrucao[0]
                copia["evidencia"] = f"{evidencia} — peça {numero + 1} de {atual}"
                normalizados.append(copia)
        else:
            copia = deepcopy(item)
            if instrucao:
                copia["quantidade"] = instrucao[0]
            normalizados.append(copia)
    for item in normalizados:
        material = parse_material(str(item.get("material") or ""))
        if material:
            item["material"] = material["material"]
            if not item.get("acabamento") and material.get("acabamento"):
                item["acabamento"] = material["acabamento"]
    for indice, item in enumerate(normalizados, 1):
        item["indice"] = indice
    mapa["itens"] = normalizados
    return mapa


def _item_visual(proposta: dict, indice: int, fonte: str) -> dict:
    confianca = float(proposta.get("confianca") or 0)
    largura, altura = proposta.get("largura_cm"), proposta.get("altura_cm")
    return {
        "indice": indice,
        "quantidade": {"valor": proposta.get("quantidade"), "unidade": "unidade", "fonte": fonte, "confianca": confianca},
        "dimensoes": {"largura_mm": largura * 10 if largura is not None else None, "altura_mm": altura * 10 if altura is not None else None, "tipo": "leitura_visual", "fonte": fonte, "confianca": confianca},
        "componentes": [],
        "material": {"valor": proposta.get("material"), "fonte": fonte, "confianca": confianca},
        "acabamento": {"valor": proposta.get("acabamento"), "fonte": fonte, "confianca": confianca},
        "evidencia_visual": proposta.get("evidencia"),
    }


def _proposta_completa(proposta: dict) -> bool:
    return (
        isinstance(proposta.get("quantidade"), int) and proposta["quantidade"] > 0
        and isinstance(proposta.get("largura_cm"), (int, float)) and proposta["largura_cm"] > 0
        and isinstance(proposta.get("altura_cm"), (int, float)) and proposta["altura_cm"] > 0
    )


def reconciliar_analise_visual(resultado: dict, visual: dict, fonte: str = "visao_api") -> dict:
    """Substitui a estrutura somente quando a visão declara conflito com proposta completa."""
    propostas = list(visual.get("itens") or []) if isinstance(visual.get("itens"), list) else []
    # O inventário visual é deliberadamente redundante: modelos pequenos podem
    # transcrever corretamente uma legenda e ainda omiti-la da lista final.
    chaves = {(p.get("quantidade"), p.get("largura_cm"), p.get("altura_cm")) for p in propostas}
    for instrucao in visual.get("instrucoes_visuais") or []:
        chave = (instrucao.get("quantidade"), instrucao.get("largura_cm"), instrucao.get("altura_cm"))
        if all(chave) and chave not in chaves:
            propostas.append({
                "indice": len(propostas) + 1, **{k: instrucao.get(k) for k in ("quantidade", "largura_cm", "altura_cm")},
                "material": None, "acabamento": None, "evidencia": instrucao.get("texto"), "confianca": 0.8,
            })
            chaves.add(chave)
    from .pedido import parse_dimensoes, parse_quantidade
    for leitura in visual.get("_ocr_visual") or []:
        quantidade = parse_quantidade(leitura.get("texto", ""))
        dimensoes = parse_dimensoes(leitura.get("texto", ""))
        if not quantidade or not dimensoes:
            continue
        chave = (quantidade[0], dimensoes["largura_mm"] / 10, dimensoes["altura_mm"] / 10)
        if chave in chaves:
            continue
        propostas.append({
            "indice": len(propostas) + 1, "quantidade": chave[0], "largura_cm": chave[1], "altura_cm": chave[2],
            "material": None, "acabamento": None, "evidencia": leitura["texto"],
            "confianca": min(0.95, float(leitura.get("confianca") or 0.8)),
        })
        chaves.add(chave)
    estado = visual.get("estrutura_confere", "incerto")
    substituir = bool(
        visual.get("_fase") != "mapa_visual_inicial"
        and
        estado == "nao" and propostas
        and all(_proposta_completa(p) and float(p.get("confianca") or 0) >= 0.65 for p in propostas)
    )
    if substituir:
        resultado["itens_estruturais_descartados"] = deepcopy(resultado.get("itens", []))
        resultado["itens"] = [_item_visual(p, i, fonte) for i, p in enumerate(propostas, 1)]
        resultado.setdefault("alertas", []).append({
            "codigo": "ESTRUTURA_RECONSTRUIDA_PELA_VISAO", "severidade": "revisao",
            "mensagem": "A leitura visual encontrou outra composição; confirme os itens reconstruídos.",
        })
    else:
        por_indice = {p.get("indice"): p for p in propostas}
        for item in resultado.get("itens", []):
            proposta = por_indice.get(item.get("indice"))
            if not proposta:
                continue
            item["analise_visual"] = proposta
            confianca = float(proposta.get("confianca") or 0)
            for campo in ("material", "acabamento"):
                valor, atual = proposta.get(campo), item.get(campo, {}).get("valor")
                if valor and atual is None:
                    item[campo] = {"valor": valor, "fonte": fonte, "confianca": confianca}
                elif valor and atual and valor.casefold() != str(atual).casefold():
                    resultado.setdefault("alertas", []).append({"codigo": f"DIVERGENCIA_VISAO_{campo.upper()}", "severidade": "revisao", "mensagem": f"Item {item['indice']}: análise indica '{atual}', visão sugere '{valor}'."})
            quantidade, atual_qtd = proposta.get("quantidade"), item.get("quantidade", {}).get("valor")
            if quantidade and atual_qtd and quantidade != atual_qtd:
                resultado.setdefault("alertas", []).append({"codigo": "DIVERGENCIA_VISAO_QUANTIDADE", "severidade": "revisao", "mensagem": f"Item {item['indice']}: análise indica {atual_qtd}, visão sugere {quantidade}."})

    resultado["total_unidades"] = sum(i.get("quantidade", {}).get("valor") or 0 for i in resultado.get("itens", []))
    resultado["analise_visual"] = {"fonte": "openai_api" if fonte == "visao_api" else fonte, "imagem_origem": visual.get("_imagem_origem", "preview_embutido"), "ocr_linhas": len(visual.get("_ocr_visual") or []), "estrutura_confere": estado, "documento_misto": bool(visual.get("documento_misto")), "observacoes": visual.get("observacoes", [])}
    resultado["pendencias"] = [campo for campo in ("quantidade", "dimensoes", "material", "acabamento") if any(
        (not item.get(campo, {}).get("valor")) if campo != "dimensoes" else (not item.get("dimensoes", {}).get("largura_mm") or not item.get("dimensoes", {}).get("altura_mm"))
        for item in resultado.get("itens", []))]
    return resultado


mesclar_analise_visual = reconciliar_analise_visual
