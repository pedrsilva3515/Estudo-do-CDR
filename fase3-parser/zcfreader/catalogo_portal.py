"""Materiais e acabamentos com os nomes do Portal Flow da gráfica.

Catálogo levantado dos nomes das imagens exportadas de 839 pedidos concluídos
(set/2026), no padrão "P0873 - Cliente - <Material> - X<qtd> - com <Acabamento> - LxA".
Frequência das imagens por material entre parênteses, para os padrões da casa.

Quando o pedido diz o material ("adesivo fosco"), a conversão é do texto
(origem "arquivo"). Quando diz só o genérico ("adesivo", "lona"), usa o material
mais comum da gráfica e marca como "padrao_grafica": é uma sugestão, não certeza.
"""
from __future__ import annotations

import re
import unicodedata

MATERIAIS = {
    "Adesivo Leitoso Interm.": 965,
    "Papel Outdoor": 436,
    "Lona Brilho 440g": 186,
    "Adesivo Fosco": 68,
    "Lona Fosca": 64,
    "Material do Cliente Lona": 62,
    "Adesivo Transparente": 54,
    "Adesivo Fosco Blackout": 48,
    "Adesivo Perfurado": 45,
    "Material do Cliente Adesivo": 41,
    "Adesivo Blackout": 39,
    "Impressão a Laser Couchê 250g 12x18": 38,
    "PS 2 mm": 36,
    "Material do Cliente Prismático Branco": 19,
    "Impressão a Laser Couchê 150g A4": 18,
    "Impressão a Laser Couchê 250g A4": 17,
    "Material do Cliente Prismático Amarelo": 15,
    "PS 1 mm": 2,
}
ACABAMENTOS = ("Recorte", "Banner", "Ilhós", "Verniz", "Refilado", "Laminação", "Corte Especial",
               "Frente e Verso", "Somente Recorte")

# Padrões da casa quando o pedido só diz o genérico (fração entre os materiais da família).
PADRAO_ADESIVO = "Adesivo Leitoso Interm."   # ~78% dos adesivos exportados
PADRAO_LONA = "Lona Brilho 440g"              # ~74% das lonas exportadas


def _normal(texto) -> str:
    texto = "".join(c for c in unicodedata.normalize("NFKD", str(texto or "").casefold()) if not unicodedata.combining(c))
    return " " + " ".join(re.sub(r"[^\w]+", " ", texto).split()) + " "


def _tem(t: str, *palavras: str) -> bool:
    return any(f" {p}" in t for p in palavras)


def material_portal(material, acabamento=None) -> tuple[str | None, str]:
    """(nome no Portal Flow, origem) — origem "arquivo" ou "padrao_grafica"; (None, "") se não reconhece."""
    t = _normal(f"{material or ''} {acabamento or ''}")
    if t.strip() == "":
        return None, ""
    if _tem(t, "material do cliente"):
        if _tem(t, "prismatic"):
            return ("Material do Cliente Prismático Amarelo" if _tem(t, "amarel") else "Material do Cliente Prismático Branco"), "arquivo"
        if _tem(t, "lona", "banner"):
            return "Material do Cliente Lona", "arquivo"
        if _tem(t, "adesiv", "vinil"):
            return "Material do Cliente Adesivo", "arquivo"
    if _tem(t, "papel outdoor", "outdoor"):
        return "Papel Outdoor", "arquivo"
    if _tem(t, "couche"):
        gramatura = re.search(r" (150|250) ?g", t)
        formato = "A4" if _tem(t, "a4") else "12x18" if re.search(r" 12 ?x ?18", t) else None
        if gramatura and formato and f"Impressão a Laser Couchê {gramatura.group(1)}g {formato}" in MATERIAIS:
            return f"Impressão a Laser Couchê {gramatura.group(1)}g {formato}", "arquivo"
        return None, ""
    if re.search(r" ps( |$)", t):
        espessura = re.search(r" ([12]) ?mm", t)
        return (f"PS {espessura.group(1)} mm", "arquivo") if espessura else ("PS 2 mm", "padrao_grafica")
    if _tem(t, "lona", "banner"):
        if _tem(t, "fosc"):
            return "Lona Fosca", "arquivo"
        return PADRAO_LONA, ("arquivo" if _tem(t, "brilh", "440") else "padrao_grafica")
    if _tem(t, "adesiv", "vinil", "ads"):
        if _tem(t, "blackout", "black out"):
            return ("Adesivo Fosco Blackout" if _tem(t, "fosc") else "Adesivo Blackout"), "arquivo"
        if _tem(t, "perfurad"):
            return "Adesivo Perfurado", "arquivo"
        if _tem(t, "transparent", "trasnparent"):
            return "Adesivo Transparente", "arquivo"
        if _tem(t, "fosc"):
            return "Adesivo Fosco", "arquivo"
        if _tem(t, "leitos"):
            return PADRAO_ADESIVO, "arquivo"
        if _tem(t, "super cola", "brilh", "jatead", "refletiv", "prismatic"):
            return None, ""  # o pedido diz um tipo que o catálogo não tem: o operador decide
        return PADRAO_ADESIVO, "padrao_grafica"
    return None, ""


def acabamentos_portal(material, acabamento) -> list[str]:
    """Acabamentos com os nomes do Portal Flow, na ordem em que aparecem nas exportações."""
    t = _normal(f"{material or ''} {acabamento or ''}")
    lista = []
    if _tem(t, "banner"):
        lista.append("Banner")
    if _tem(t, "somente recorte"):
        lista.append("Somente Recorte")
    elif _tem(t, "corte especial"):
        lista.append("Corte Especial")
    elif _tem(t, "recort", "com rec") and not _tem(t, "sem rec"):
        lista.append("Recorte")
    if _tem(t, "refilad"):
        lista.append("Refilado")
    if _tem(t, "ilho", "ilhos"):
        lista.append("Ilhós")
    if _tem(t, "verniz"):
        lista.append("Verniz")
    if _tem(t, "laminac"):
        lista.append("Laminação")
    if _tem(t, "frente e verso"):
        lista.append("Frente e Verso")
    return lista
