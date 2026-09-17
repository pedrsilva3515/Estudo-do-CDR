"""Análise visual opcional por API, sem substituir evidências estruturais."""
from __future__ import annotations

import base64
import json
from pathlib import Path

from .container import abrir_cdr


def extrair_preview(caminho: Path) -> tuple[bytes, str] | None:
    with abrir_cdr(caminho) as doc:
        nomes = doc.namelist()
        preferencias = (
            "previews/thumbnail.png", "previews/page1.png",
            "metadata/thumbnails/thumbnail.png", "metadata/thumbnails/page1.png",
        )
        membro = next((nome for nome in preferencias if nome in nomes), None)
        if membro is None:
            membro = next((nome for nome in nomes if nome.casefold().endswith(".png") and "preview" in nome.casefold()), None)
        if membro is None:
            return None
        return doc.read(membro), "image/png"


def _schema_resposta() -> dict:
    item = {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "indice": {"type": "integer"},
            "quantidade": {"type": ["integer", "null"]},
            "material": {"type": ["string", "null"]},
            "acabamento": {"type": ["string", "null"]},
            "observacao": {"type": ["string", "null"]},
            "confianca": {"type": "number", "minimum": 0, "maximum": 1},
        },
        "required": ["indice", "quantidade", "material", "acabamento", "observacao", "confianca"],
    }
    return {
        "type": "object",
        "additionalProperties": False,
        "properties": {
            "itens": {"type": "array", "items": item},
            "observacoes": {"type": "array", "items": {"type": "string"}},
        },
        "required": ["itens", "observacoes"],
    }


def analisar_com_openai(caminho: Path, resultado_estrutural: dict, chave: str, modelo: str) -> dict:
    """Envia preview + evidências e recebe uma leitura visual estruturada."""
    from openai import OpenAI

    preview = extrair_preview(caminho)
    if preview is None:
        raise RuntimeError("O CDR não contém um preview PNG utilizável pela análise visual.")
    bytes_imagem, mime = preview
    url_imagem = f"data:{mime};base64,{base64.b64encode(bytes_imagem).decode('ascii')}"
    evidencias = json.dumps(resultado_estrutural, ensure_ascii=False, separators=(",", ":"))
    prompt = (
        "Interprete este pedido de gráfica em português. Use a imagem para ler textos, inclusive os "
        "convertidos em curvas, e associe quantidade, material e acabamento a cada item já detectado. "
        "A geometria e as dimensões do JSON são evidências mais fortes e não devem ser recalculadas pela "
        "imagem. Não invente campos ilegíveis; use null. JSON estrutural: " + evidencias
    )
    cliente = OpenAI(api_key=chave)
    resposta = cliente.responses.create(
        model=modelo,
        store=False,
        input=[{
            "role": "user",
            "content": [
                {"type": "input_text", "text": prompt},
                {"type": "input_image", "image_url": url_imagem, "detail": "high"},
            ],
        }],
        text={"format": {"type": "json_schema", "name": "pedido_cdr", "strict": True, "schema": _schema_resposta()}},
        max_output_tokens=1800,
    )
    return json.loads(resposta.output_text)


def mesclar_analise_visual(resultado: dict, visual: dict) -> dict:
    """Preenche lacunas e registra divergências sem ocultar a fonte original."""
    por_indice = {item.get("indice"): item for item in visual.get("itens", [])}
    for item in resultado.get("itens", []):
        proposta = por_indice.get(item.get("indice"))
        if not proposta:
            continue
        item["analise_visual_api"] = proposta
        for campo in ("material", "acabamento"):
            valor = proposta.get(campo)
            atual = item.get(campo, {}).get("valor")
            if valor and atual is None:
                item[campo] = {
                    "valor": valor, "fonte": "visao_api", "confianca": proposta.get("confianca", 0.5),
                }
            elif valor and atual and valor.casefold() != str(atual).casefold():
                resultado.setdefault("alertas", []).append({
                    "codigo": f"DIVERGENCIA_API_{campo.upper()}", "severidade": "revisao",
                    "mensagem": f"Item {item['indice']}: estrutura/nome indica '{atual}', API sugere '{valor}'.",
                })
        quantidade = proposta.get("quantidade")
        atual_qtd = item.get("quantidade", {}).get("valor")
        if quantidade and atual_qtd and quantidade != atual_qtd:
            resultado.setdefault("alertas", []).append({
                "codigo": "DIVERGENCIA_API_QUANTIDADE", "severidade": "revisao",
                "mensagem": f"Item {item['indice']}: análise atual indica {atual_qtd}, API sugere {quantidade}.",
            })
    resultado["analise_visual"] = {
        "fonte": "openai_api", "observacoes": visual.get("observacoes", []),
    }
    resultado["pendencias"] = [
        campo for campo in resultado.get("pendencias", [])
        if any(item.get(campo, {}).get("valor") is None for item in resultado.get("itens", []))
    ]
    return resultado
