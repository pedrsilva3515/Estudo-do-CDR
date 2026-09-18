"""Harness de regressão baseado nos pacotes revisados pelo operador."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import tempfile
from zipfile import ZipFile

from .pedido import interpretar_pedido


def assinatura_item(item: dict) -> tuple:
    dim = item.get("dimensoes") or {}
    material = str((item.get("material") or {}).get("valor") or "").casefold().strip()
    acabamento = str((item.get("acabamento") or {}).get("valor") or "").casefold().strip()
    return (
        int((item.get("quantidade") or {}).get("valor") or 0),
        round(float(dim.get("largura_mm") or 0), 1), round(float(dim.get("altura_mm") or 0), 1),
        material, acabamento,
    )


def comparar_resultados(obtido: dict, esperado: dict) -> dict:
    antes = Counter(assinatura_item(item) for item in obtido.get("itens", []))
    depois = Counter(assinatura_item(item) for item in esperado.get("itens", []))
    comuns = sum((antes & depois).values())
    total = max(sum(depois.values()), 1)
    campos = {"quantidade": 0, "dimensoes": 0, "material": 0, "acabamento": 0}
    # Métricas por assinatura de campo, independentes da ordem da tabela.
    indices = {"quantidade": (0,), "dimensoes": (1, 2), "material": (3,), "acabamento": (4,)}
    for campo, posicoes in indices.items():
        a = Counter(tuple(chave[p] for p in posicoes) for chave, n in antes.items() for _ in range(n))
        b = Counter(tuple(chave[p] for p in posicoes) for chave, n in depois.items() for _ in range(n))
        campos[campo] = sum((a & b).values()) / total
    return {
        "exato": antes == depois,
        "itens_corretos": comuns, "itens_esperados": sum(depois.values()),
        "acuracia_itens": comuns / total,
        "numero_itens_correto": sum(antes.values()) == sum(depois.values()),
        "total_unidades_correto": obtido.get("total_unidades") == esperado.get("total_unidades"),
        "acuracia_campos": campos,
    }


def avaliar_pasta_relatorios(pasta: Path) -> dict:
    """Executa o parser nos CDRs incluídos, mantendo apenas a revisão mais nova de cada arquivo."""
    revisoes = {}
    for zip_path in sorted(Path(pasta).glob("*.zip")):
        with ZipFile(zip_path) as pacote:
            if "diagnostico.json" not in pacote.namelist() or "resultado-correto.json" not in pacote.namelist():
                continue
            diagnostico = json.loads(pacote.read("diagnostico.json"))
            cdr = next((n for n in pacote.namelist() if n.startswith("arquivo-original/") and n.casefold().endswith(".cdr")), None)
            if cdr:
                revisoes[diagnostico["arquivo"]["sha256"]] = (zip_path, cdr, diagnostico)
    casos = []
    for zip_path, membro_cdr, diagnostico in revisoes.values():
        with ZipFile(zip_path) as pacote, tempfile.TemporaryDirectory(prefix="cdr-regressao-") as pasta_tmp:
            caminho = Path(pasta_tmp) / Path(membro_cdr).name
            caminho.write_bytes(pacote.read(membro_cdr))
            esperado = json.loads(pacote.read("resultado-correto.json"))
            obtido = interpretar_pedido(caminho)
        casos.append({
            "arquivo": diagnostico["arquivo"]["nome"],
            "metricas": comparar_resultados(obtido, esperado),
        })
    return {
        "casos": casos, "total_casos": len(casos),
        "casos_exatos": sum(c["metricas"]["exato"] for c in casos),
        "totais_corretos": sum(c["metricas"]["total_unidades_correto"] for c in casos),
    }
