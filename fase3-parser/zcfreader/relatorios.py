"""Pacotes de feedback auditáveis para melhorar a interpretação de pedidos."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
from zipfile import ZIP_DEFLATED, ZipFile

from .visao_api import extrair_preview


VERSAO_APLICACAO = "0.7.0"


def pasta_relatorios() -> Path:
    documentos = Path(os.environ.get("USERPROFILE") or Path.home()) / "Documents"
    return documentos / "LeitorPedidosCDR" / "Relatorios"


def _json_bytes(valor: object) -> bytes:
    return (json.dumps(valor, ensure_ascii=False, indent=2) + "\n").encode("utf-8")


def hash_arquivo(caminho: Path) -> str:
    resumo = hashlib.sha256()
    with caminho.open("rb") as arquivo:
        for bloco in iter(lambda: arquivo.read(1024 * 1024), b""):
            resumo.update(bloco)
    return resumo.hexdigest()


def normalizar_resultado_corrigido(resultado: dict) -> dict:
    corrigido = deepcopy(resultado)
    itens = corrigido.get("itens", [])
    for indice, item in enumerate(itens, 1):
        item["indice"] = indice
    corrigido["total_unidades"] = sum(
        int(item.get("quantidade", {}).get("valor") or 0) for item in itens
    )
    pendencias = []
    for campo in ("material", "acabamento"):
        if any(not item.get(campo, {}).get("valor") for item in itens):
            pendencias.append(campo)
    corrigido["pendencias"] = pendencias
    return corrigido


def classificar_diferencas(original: dict, correto: dict) -> list[str]:
    categorias: list[str] = []
    antes = original.get("itens", [])
    depois = correto.get("itens", [])
    if len(antes) != len(depois):
        categorias.append("agrupamento_de_itens")
    for a, b in zip(antes, depois):
        if a.get("quantidade", {}).get("valor") != b.get("quantidade", {}).get("valor"):
            categorias.append("quantidade")
        da, db = a.get("dimensoes", {}), b.get("dimensoes", {})
        if (da.get("largura_mm"), da.get("altura_mm")) != (db.get("largura_mm"), db.get("altura_mm")):
            categorias.append("dimensoes")
        if a.get("material", {}).get("valor") != b.get("material", {}).get("valor"):
            categorias.append("material")
        if a.get("acabamento", {}).get("valor") != b.get("acabamento", {}).get("valor"):
            categorias.append("acabamento")
    return list(dict.fromkeys(categorias))


def _resumo_texto(original: dict, correto: dict, diagnostico: dict) -> str:
    linhas = [
        "RELATÓRIO DE REVISÃO — LEITOR DE PEDIDOS CDR",
        "",
        f"Caso: {diagnostico['caso_id']}",
        f"Arquivo: {diagnostico['arquivo']['nome']}",
        f"Situação: {diagnostico['situacao']}",
        f"Aplicação: v{diagnostico['versao_aplicacao']}",
        f"Processamento: {diagnostico.get('processamento') or 'estrutural'}",
        f"Tempo: {diagnostico.get('duracao_segundos', 0):.1f} s",
        f"Categorias alteradas: {', '.join(diagnostico['categorias']) or 'nenhuma'}",
        f"Observação do operador: {diagnostico.get('observacao_operador') or 'nenhuma'}",
        "",
        "RESULTADO CORRETO",
    ]
    for item in correto.get("itens", []):
        dimensoes = item.get("dimensoes", {})
        linhas.append(
            f"- Item {item.get('indice')}: {item.get('quantidade', {}).get('valor')} un; "
            f"{(dimensoes.get('largura_mm') or 0) / 10:g} x "
            f"{(dimensoes.get('altura_mm') or 0) / 10:g} cm; "
            f"material={item.get('material', {}).get('valor') or 'confirmar'}; "
            f"acabamento={item.get('acabamento', {}).get('valor') or 'confirmar'}"
        )
    linhas.extend([
        "",
        f"Total anterior: {original.get('total_unidades', 0)}",
        f"Total correto: {correto.get('total_unidades', 0)}",
        "",
        "Anexe este ZIP na conversa para investigação. O CDR só estará incluído se essa opção foi marcada.",
    ])
    return "\n".join(linhas) + "\n"


def gerar_pacote_diagnostico(
    caminho_cdr: Path,
    resultado_original: dict,
    resultado_correto: dict,
    resultado_estrutural: dict | None = None,
    analise_visual: dict | None = None,
    duracao_segundos: float = 0,
    situacao: str = "confirmado",
    observacao_operador: str = "",
    incluir_cdr: bool = False,
) -> Path:
    """Grava ZIP de diagnóstico e uma entrada no histórico local."""
    caminho_cdr = Path(caminho_cdr)
    correto = normalizar_resultado_corrigido(resultado_correto)
    sha256 = hash_arquivo(caminho_cdr)
    agora = datetime.now().astimezone()
    caso_id = f"{agora:%Y%m%d-%H%M%S}-{sha256[:12]}"
    seguro = re.sub(r"[^\w.-]+", "-", caminho_cdr.stem, flags=re.UNICODE).strip("-_")[:60] or "pedido"
    pasta = pasta_relatorios()
    pasta.mkdir(parents=True, exist_ok=True)
    destino = pasta / f"{caso_id}-{seguro}.zip"
    processamento = resultado_original.get("processamento", {})
    diagnostico = {
        "schema_version": "1.0",
        "caso_id": caso_id,
        "gerado_em": agora.isoformat(),
        "versao_aplicacao": VERSAO_APLICACAO,
        "situacao": situacao,
        "categorias": classificar_diferencas(resultado_original, correto),
        "observacao_operador": observacao_operador.strip(),
        "duracao_segundos": round(float(duracao_segundos or 0), 3),
        "processamento": processamento,
        "arquivo": {
            "nome": caminho_cdr.name,
            "tamanho_bytes": caminho_cdr.stat().st_size,
            "sha256": sha256,
            "cdr_incluido": bool(incluir_cdr),
        },
    }
    with ZipFile(destino, "w", compression=ZIP_DEFLATED) as pacote:
        pacote.writestr("resultado-original.json", _json_bytes(resultado_original))
        pacote.writestr("resultado-correto.json", _json_bytes(correto))
        pacote.writestr("diagnostico.json", _json_bytes(diagnostico))
        pacote.writestr("resumo.txt", _resumo_texto(resultado_original, correto, diagnostico).encode("utf-8"))
        if resultado_estrutural is not None:
            pacote.writestr("resultado-estrutural.json", _json_bytes(resultado_estrutural))
        if analise_visual is not None:
            pacote.writestr("analise-visual.json", _json_bytes(analise_visual))
        preview = extrair_preview(caminho_cdr)
        if preview is not None:
            pacote.writestr("preview.png", preview[0])
        if incluir_cdr:
            pacote.write(caminho_cdr, f"arquivo-original/{caminho_cdr.name}")

    entrada = {
        "caso_id": caso_id, "gerado_em": agora.isoformat(), "arquivo": caminho_cdr.name,
        "situacao": situacao, "categorias": diagnostico["categorias"], "pacote": str(destino),
    }
    with (pasta / "historico.jsonl").open("a", encoding="utf-8") as historico:
        historico.write(json.dumps(entrada, ensure_ascii=False) + "\n")
    return destino
