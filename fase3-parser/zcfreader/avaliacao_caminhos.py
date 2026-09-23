"""Compara caminhos de interpretação contra as revisões do operador.

Diferente de ``avaliacao.comparar_resultados`` (igualdade exata de assinatura),
aqui os itens são pareados com tolerância de medida e orientação, e itens a mais
e faltando são contados separadamente — o erro mais caro para a produção é um
item inventado ou esquecido, não uma diferença de 1 mm.
"""
from __future__ import annotations

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unicodedata
from zipfile import ZipFile

from .origem_campos import origem

TOLERANCIA_ABSOLUTA_CM = 1.5
TOLERANCIA_RELATIVA = 0.03


def _texto(valor) -> str:
    texto = "".join(
        c for c in unicodedata.normalize("NFKD", str(valor or "").casefold())
        if not unicodedata.combining(c)
    )
    return " ".join(texto.replace("ilhoses", "ilhos").split())


def _material(valor) -> str:
    texto = _texto(valor)
    # Na gráfica, "vinil" é o adesivo vinílico: "vinil transparente" = "adesivo transparente".
    texto = " ".join("adesivo" if palavra == "vinil" else palavra for palavra in texto.split())
    return texto.replace("adesivo adesivo", "adesivo")


def materiais_compativeis(obtido, esperado) -> bool:
    a, b = _material(obtido), _material(esperado)
    if a == b:
        return True
    if {a, b} <= {"banner", "lona"}:
        return True
    # Material genérico no gabarito aceita subtipo mais específico, e vice-versa.
    return bool(a and b) and (a.startswith(b + " ") or b.startswith(a + " "))


def _medidas_cm(item: dict) -> tuple[float, float]:
    dim = item.get("dimensoes") or {}
    return float(dim.get("largura_mm") or 0) / 10, float(dim.get("altura_mm") or 0) / 10


def _quantidade(item: dict) -> int:
    return int((item.get("quantidade") or {}).get("valor") or 0)


def _valor(item: dict, campo: str):
    return (item.get(campo) or {}).get("valor")


def _erro_medida(a: tuple[float, float], b: tuple[float, float]) -> float | None:
    """Erro em cm no melhor alinhamento de orientação, ou None se fora da tolerância."""
    melhor = None
    for w, h in (a, a[::-1]):
        dw, dh = abs(w - b[0]), abs(h - b[1])
        limite_w = max(TOLERANCIA_ABSOLUTA_CM, TOLERANCIA_RELATIVA * b[0])
        limite_h = max(TOLERANCIA_ABSOLUTA_CM, TOLERANCIA_RELATIVA * b[1])
        if dw <= limite_w and dh <= limite_h:
            melhor = min(melhor, dw + dh) if melhor is not None else dw + dh
    return melhor


def consolidar_linhas(itens: list[dict]) -> list[dict]:
    """Soma linhas de mesma medida e material: "5 x 1 un" e "1 x 5 un" são o mesmo pedido."""
    consolidados: list[dict] = []
    for item in itens:
        destino = next((
            c for c in consolidados
            if _erro_medida(_medidas_cm(item), _medidas_cm(c)) is not None
            and _material(_valor(item, "material")) == _material(_valor(c, "material"))
            and _texto(_valor(item, "acabamento")) == _texto(_valor(c, "acabamento"))
        ), None)
        if destino is None:
            copia = deepcopy(item)
            copia["quantidade"] = {**(item.get("quantidade") or {}), "valor": _quantidade(item)}
            consolidados.append(copia)
        else:
            destino["quantidade"]["valor"] += _quantidade(item)
    return consolidados


def comparar_tolerante(obtido: dict, esperado: dict) -> dict:
    itens_obtidos = consolidar_linhas(obtido.get("itens") or [])
    itens_esperados = consolidar_linhas(esperado.get("itens") or [])
    pares = []
    for i, item_obtido in enumerate(itens_obtidos):
        for j, item_esperado in enumerate(itens_esperados):
            erro = _erro_medida(_medidas_cm(item_obtido), _medidas_cm(item_esperado))
            if erro is None:
                continue
            # Desempate por quantidade e material quando há medidas iguais.
            pares.append((
                erro, int(_quantidade(item_obtido) != _quantidade(item_esperado)),
                int(not materiais_compativeis(_valor(item_obtido, "material"), _valor(item_esperado, "material"))),
                i, j,
            ))
    usados_o, usados_e, casados = set(), set(), []
    for _, _, _, i, j in sorted(pares, key=lambda p: (p[1], p[2], p[0])):
        if i in usados_o or j in usados_e:
            continue
        usados_o.add(i)
        usados_e.add(j)
        casados.append((itens_obtidos[i], itens_esperados[j]))

    def faltou(item: dict, campo: str) -> bool:
        return origem(item, campo) == "faltou_no_pedido"

    # Campo que faltou no pedido não é cobrado: o certo é o sistema perceber a falta.
    qtd_ok = sum(faltou(e, "quantidade") or _quantidade(o) == _quantidade(e) for o, e in casados)
    com_material = [(o, e) for o, e in casados if _valor(e, "material") and not faltou(e, "material")]
    material_ok = sum(materiais_compativeis(_valor(o, "material"), _valor(e, "material")) for o, e in com_material)
    com_acabamento = [(o, e) for o, e in casados if _valor(e, "acabamento") and not faltou(e, "acabamento")]
    acabamento_ok = sum(_texto(_valor(o, "acabamento")) == _texto(_valor(e, "acabamento")) for o, e in com_acabamento)
    linhas_corretas = sum(
        (faltou(e, "quantidade") or _quantidade(o) == _quantidade(e))
        and (not _valor(e, "material") or faltou(e, "material")
             or materiais_compativeis(_valor(o, "material"), _valor(e, "material")))
        for o, e in casados
    )
    perguntou = bool(obtido.get("perguntas") or obtido.get("perguntas_operador"))
    faltas_esperadas = faltas_detectadas = chutes = 0
    for o, e in casados:
        for campo in ("quantidade", "material", "acabamento"):
            if not faltou(e, campo):
                continue
            faltas_esperadas += 1
            vazio = campo != "quantidade" and not _valor(o, campo)
            if vazio or perguntou:
                faltas_detectadas += 1
            else:
                chutes += 1
    total_obtido = sum(_quantidade(i) for i in itens_obtidos)
    total_esperado = sum(_quantidade(i) for i in itens_esperados)
    return {
        "esperados": len(itens_esperados), "obtidos": len(itens_obtidos),
        "pareados": len(casados),
        "a_mais": len(itens_obtidos) - len(casados),
        "faltando": len(itens_esperados) - len(casados),
        "quantidade_ok": qtd_ok,
        "material_ok": material_ok, "material_avaliado": len(com_material),
        "acabamento_ok": acabamento_ok, "acabamento_avaliado": len(com_acabamento),
        "linhas_corretas": linhas_corretas,
        "pedido_correto": linhas_corretas == len(itens_esperados) == len(itens_obtidos),
        "total_unidades_ok": total_obtido == total_esperado,
        "perguntas": len(obtido.get("perguntas") or obtido.get("perguntas_operador") or []),
        "faltas_esperadas": faltas_esperadas, "faltas_detectadas": faltas_detectadas, "chutes": chutes,
    }


def resultado_de_auditoria_regional(auditoria: dict) -> dict:
    """Converte os produtos da auditoria regional para o formato de itens do pedido."""
    itens = []
    for item in auditoria.get("itens", []):
        if item.get("papel") not in {"produto_confirmado", "produto_plausivel"}:
            continue
        quantidade = item.get("quantidade_pedido") or item.get("quantidade_desenhada") or 1
        itens.append({
            "indice": len(itens) + 1,
            "quantidade": {"valor": int(quantidade)},
            "dimensoes": {"largura_mm": item["largura_cm"] * 10, "altura_mm": item["altura_cm"] * 10},
            "material": {"valor": item.get("material")},
            "acabamento": {"valor": item.get("acabamento")},
        })
    return {"itens": itens, "total_unidades": sum(i["quantidade"]["valor"] for i in itens)}


def carregar_casos(pasta: Path) -> list[dict]:
    """Uma revisão por CDR (a mais recente), com o CDR incluído no pacote."""
    revisoes = {}
    for zip_path in sorted(Path(pasta).glob("*.zip")):
        with ZipFile(zip_path) as pacote:
            nomes = pacote.namelist()
            if "diagnostico.json" not in nomes or "resultado-correto.json" not in nomes:
                continue
            cdr = next((n for n in nomes if n.startswith("arquivo-original/") and n.casefold().endswith(".cdr")), None)
            if not cdr:
                continue
            diagnostico = json.loads(pacote.read("diagnostico.json"))
            revisoes[diagnostico["arquivo"]["sha256"]] = {
                "zip": zip_path, "membro_cdr": cdr, "nome": diagnostico["arquivo"]["nome"],
            }
    return list(revisoes.values())


def avaliar_caminhos(pasta: Path, caminhos: dict, somente: list[str] | None = None) -> dict:
    """``caminhos`` mapeia nome -> função(caminho_cdr, pacote) que devolve um resultado.

    ``somente`` restringe aos casos cujo nome contém algum dos trechos informados.
    """
    casos = []
    for caso in carregar_casos(pasta):
        if somente and not any(t.casefold() in caso["nome"].casefold() for t in somente):
            continue
        with ZipFile(caso["zip"]) as pacote, tempfile.TemporaryDirectory(prefix="cdr-aval-") as tmp:
            cdr = Path(tmp) / Path(caso["membro_cdr"]).name
            cdr.write_bytes(pacote.read(caso["membro_cdr"]))
            esperado = json.loads(pacote.read("resultado-correto.json"))
            metricas = {}
            for nome, funcao in caminhos.items():
                try:
                    metricas[nome] = comparar_tolerante(funcao(cdr, pacote), deepcopy(esperado))
                except Exception as erro:  # um caminho quebrado não deve esconder os demais
                    metricas[nome] = {"erro": f"{type(erro).__name__}: {erro}"}
        casos.append({"arquivo": caso["nome"], "metricas": metricas})
    totais = {}
    for nome in caminhos:
        validos = [c["metricas"][nome] for c in casos if "erro" not in c["metricas"][nome]]
        totais[nome] = {
            "casos": len(validos),
            "falhas": len(casos) - len(validos),
            "pedidos_corretos": sum(m["pedido_correto"] for m in validos),
            **{chave: sum(m[chave] for m in validos) for chave in (
                "esperados", "obtidos", "pareados", "a_mais", "faltando", "quantidade_ok", "linhas_corretas", "perguntas",
                "faltas_esperadas", "faltas_detectadas", "chutes",
                "material_ok", "material_avaliado", "acabamento_ok", "acabamento_avaliado",
            )},
        }
    return {"casos": casos, "totais": totais}
