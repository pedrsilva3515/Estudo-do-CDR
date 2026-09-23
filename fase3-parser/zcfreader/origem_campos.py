"""De onde veio cada informação de um item corrigido pelo operador.

Separa três situações que uma correção sozinha não distingue:

- ``arquivo``: a informação estava no pedido; se o sistema errou, é erro dele;
- ``padrao_grafica``: não estava no pedido, mas a gráfica tem um padrão; o
  sistema pode aprender (candidata a regra da casa);
- ``faltou_no_pedido``: só o cliente sabe; o comportamento certo do sistema é
  deixar vazio ou perguntar, e não adivinhar.
"""
from __future__ import annotations

ORIGENS = {
    "arquivo": "Estava no arquivo",
    "padrao_grafica": "Padrão da gráfica",
    "faltou_no_pedido": "Faltou no pedido — perguntar ao cliente",
}
CAMPOS = ("quantidade", "medida", "material", "acabamento")
MARCAS = {"padrao_grafica": " (padrão)", "faltou_no_pedido": " (faltou)"}


def origem(item: dict, campo: str) -> str:
    valor = (item.get("origem_campos") or {}).get(campo)
    return valor if valor in ORIGENS else "arquivo"


def campos_com_origem(item: dict, tipo: str) -> list[str]:
    return [campo for campo in CAMPOS if origem(item, campo) == tipo]


def definir_origens(item: dict, origens: dict[str, str]) -> dict:
    """Grava só o que difere do padrão, para não poluir os relatórios."""
    especiais = {campo: tipo for campo, tipo in origens.items() if campo in CAMPOS and tipo in ORIGENS and tipo != "arquivo"}
    novo = dict(item)
    if especiais:
        novo["origem_campos"] = especiais
    else:
        novo.pop("origem_campos", None)
    return novo


def marca(item: dict, campo: str) -> str:
    return MARCAS.get(origem(item, campo), "")
