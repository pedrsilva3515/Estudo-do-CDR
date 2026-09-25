"""Provas de regressão: cada pedido revisado pelo operador vira uma prova.

Antes de aceitar uma mudança na análise, todos os pacotes revisados são
refeitos pelos caminhos sem IA (gratuitos e sempre iguais) e comparados com a
referência gravada. Qualquer pedido que piorar aparece na hora.

O que se mede em cada pedido:
- regras: o resultado das regras regionais, comparado com o resultado correto;
- regras_decidem: se as regras respondem sozinhas (o fluxo em camadas nem chama
  a IA) e, nesse caso, se acertam; decidir sozinho e errar é o pior erro;
- pecas: quantas peças a IA recebe e quantos itens corretos têm uma peça com a
  medida certa entre elas (se a peça não aparece, a IA não tem como acertar).
"""
from __future__ import annotations

import json
import tempfile
from copy import deepcopy
from pathlib import Path
from zipfile import ZipFile

from .avaliacao_caminhos import carregar_casos, comparar_tolerante, resultado_de_auditoria_regional
from .camadas import regras_resolvem, resultado_das_regras

TOLERANCIA_PECA_CM = 1.5

# Métrica -> True quando maior é melhor.
METRICAS = {
    "regras_pedido_correto": True,
    "regras_linhas_corretas": True,
    "regras_a_mais": False,
    "regras_faltando": False,
    "regras_material_ok": True,
    "regras_acabamento_ok": True,
    "regras_decidem_errado": False,
    "itens_com_peca": True,
}


def _itens_com_peca(candidatos: list[dict], esperado: dict) -> int:
    visiveis = [c for c in candidatos if c.get("visivel_inicialmente", True)]
    cobertos = 0
    for item in esperado.get("itens") or []:
        dim = item.get("dimensoes") or {}
        w, h = (dim.get("largura_mm") or 0) / 10, (dim.get("altura_mm") or 0) / 10
        if any(
            min(abs(c["largura_cm"] - w) + abs(c["altura_cm"] - h), abs(c["largura_cm"] - h) + abs(c["altura_cm"] - w))
            <= TOLERANCIA_PECA_CM
            for c in visiveis
        ):
            cobertos += 1
    return cobertos


def medir_caso(cdr: Path, esperado: dict) -> dict:
    """Mede um pedido pelos caminhos sem IA."""
    from .experimento_agente import executar_arquitetura_regional, extrair_candidatos_agente

    auditoria = executar_arquitetura_regional(cdr)
    regras = comparar_tolerante(resultado_de_auditoria_regional(auditoria), deepcopy(esperado))
    decidem = regras_resolvem(auditoria)
    decidem_errado = decidem and not comparar_tolerante(resultado_das_regras(auditoria), deepcopy(esperado))["pedido_correto"]
    candidatos = extrair_candidatos_agente(cdr)["candidatos"]
    return {
        "itens_esperados": len(esperado.get("itens") or []),
        "regras_pedido_correto": int(regras["pedido_correto"]),
        "regras_linhas_corretas": regras["linhas_corretas"],
        "regras_a_mais": regras["a_mais"],
        "regras_faltando": regras["faltando"],
        "regras_material_ok": regras["material_ok"],
        "regras_acabamento_ok": regras["acabamento_ok"],
        "regras_decidem": int(decidem),
        "regras_decidem_errado": int(decidem_errado),
        "pecas_para_ia": sum(1 for c in candidatos if c.get("visivel_inicialmente", True)),
        "itens_com_peca": _itens_com_peca(candidatos, esperado),
    }


def medir_pasta(pasta: Path, somente: list[str] | None = None, progresso=None) -> dict:
    """Mede todos os pacotes revisados da pasta (um por CDR, a revisão mais recente)."""
    casos = {}
    for caso in carregar_casos(pasta):
        if somente and not any(t.casefold() in caso["nome"].casefold() for t in somente):
            continue
        with ZipFile(caso["zip"]) as pacote, tempfile.TemporaryDirectory(prefix="cdr-prova-") as tmp:
            cdr = Path(tmp) / Path(caso["membro_cdr"]).name
            cdr.write_bytes(pacote.read(caso["membro_cdr"]))
            esperado = json.loads(pacote.read("resultado-correto.json"))
            try:
                medidas = medir_caso(cdr, esperado)
            except Exception as erro:  # um pedido quebrado é uma piora, não deve parar as outras provas
                medidas = {"erro": f"{type(erro).__name__}: {erro}"}
        casos[caso["nome"]] = {"pacote": Path(caso["zip"]).name, **medidas}
        if progresso:
            progresso(caso["nome"], casos[caso["nome"]])
    return casos


def comparar_com_referencia(referencia: dict, atual: dict) -> dict:
    """Separa os pedidos em piorou / melhorou / novo / sumiu, métrica a métrica."""
    pioras, melhoras, novos = {}, {}, []
    for nome, medidas in atual.items():
        antes = referencia.get(nome)
        if antes is None:
            novos.append(nome)
            continue
        if "erro" in medidas and "erro" not in antes:
            pioras[nome] = [f"passou a dar erro: {medidas['erro']}"]
            continue
        if "erro" in antes and "erro" not in medidas:
            melhoras[nome] = ["deixou de dar erro"]
            continue
        if "erro" in medidas:
            continue
        for metrica, maior_melhor in METRICAS.items():
            a, d = antes.get(metrica), medidas.get(metrica)
            if a is None or d is None or a == d:
                continue
            texto = f"{metrica}: {a} -> {d}"
            ((melhoras if (d > a) == maior_melhor else pioras).setdefault(nome, [])).append(texto)
    sumiram = [nome for nome in referencia if nome not in atual]
    return {"piorou": pioras, "melhorou": melhoras, "novos": novos, "sumiram": sumiram}


def totais(casos: dict) -> dict:
    validos = [m for m in casos.values() if "erro" not in m]
    chaves = ["itens_esperados", "regras_pedido_correto", "regras_linhas_corretas", "regras_a_mais", "regras_faltando",
              "regras_decidem", "regras_decidem_errado", "pecas_para_ia", "itens_com_peca"]
    return {"pedidos": len(casos), "com_erro": len(casos) - len(validos), **{c: sum(m[c] for m in validos) for c in chaves}}
