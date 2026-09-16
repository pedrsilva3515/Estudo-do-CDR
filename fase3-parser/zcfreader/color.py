"""Leitura do contexto de cor em ``color/color.xml``."""
from __future__ import annotations

from dataclasses import dataclass
import xml.etree.ElementTree as ET


@dataclass(frozen=True)
class ContextoCorDocumento:
    modelo: str | None
    intento_renderizacao: str | None
    possui_objetos_rgb: bool | None
    possui_objetos_cmyk: bool | None
    possui_objetos_cinza: bool | None


def _booleano(root: ET.Element, nome: str) -> bool | None:
    texto = root.findtext(nome)
    if texto is None:
        return None
    return texto.strip().casefold() == "true"


def parse_contexto_cor(data: bytes) -> ContextoCorDocumento:
    root = ET.fromstring(data)
    contexto = root.find("ColorContext")
    return ContextoCorDocumento(
        modelo=contexto.findtext("ColorModel") if contexto is not None else None,
        intento_renderizacao=(contexto.findtext("RenderingIntent") if contexto is not None else None),
        possui_objetos_rgb=_booleano(root, "HasRgbObjects"),
        possui_objetos_cmyk=_booleano(root, "HasCmykObjects"),
        possui_objetos_cinza=_booleano(root, "HasGrayscaleObjects"),
    )
