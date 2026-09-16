"""Leitura de conteúdo e estilos de texto em documentos ZCF.

O conteúdo textual agregado fica em ``META-INF/textinfo.xml``. Os atributos
por objeto ficam em um ou mais JSONs dentro do bloco ``txsm`` apontado por
``root.dat``. As duas fontes são mantidas separadas porque a correspondência
por ordem entre ``TextStream`` e objetos ainda precisa de casos adicionais.
"""
from __future__ import annotations

from dataclasses import dataclass
import json
import re
import xml.etree.ElementTree as ET
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .structure import ObjetoEstrutural


class FormatoTextoInvalido(ValueError):
    """Levantado quando ``textinfo.xml`` não é XML válido."""


@dataclass(frozen=True)
class TrechoTexto:
    texto: str
    idioma: int | None = None
    quebra: str | None = None


@dataclass(frozen=True)
class FluxoTexto:
    trechos: tuple[TrechoTexto, ...]

    @property
    def texto(self) -> str:
        """Texto legível, separando trechos marcados como parágrafo."""
        partes: list[str] = []
        for indice, trecho in enumerate(self.trechos):
            if indice and self.trechos[indice - 1].quebra == "para":
                partes.append("\n")
            partes.append(trecho.texto)
        return "".join(partes)


@dataclass(frozen=True)
class EstiloTexto:
    fonte: str | None
    tamanho_unidades: int | None
    italico: bool | None
    sublinhado: bool | None
    tachado: bool | None
    peso_codigo: int | None
    bruto: dict

    @property
    def tamanho_pt(self) -> float | None:
        if self.tamanho_unidades is None:
            return None
        return self.tamanho_unidades / 10_000.0 * 72.0 / 25.4


@dataclass(frozen=True)
class TextoEstruturado:
    objeto: "ObjetoEstrutural"
    fluxo: FluxoTexto


def _nome_local(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _inteiro_opcional(valor) -> int | None:
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _booleano_codigo(valor) -> bool | None:
    numero = _inteiro_opcional(valor)
    return None if numero is None else numero != 0


def parse_textinfo(data: bytes) -> tuple[FluxoTexto, ...]:
    """Extrai os ``TextStream`` e seus ``TextRun`` do resumo XML."""
    try:
        raiz = ET.fromstring(data)
    except ET.ParseError as exc:
        raise FormatoTextoInvalido(f"textinfo.xml inválido: {exc}") from exc

    fluxos: list[FluxoTexto] = []
    for elemento in raiz.iter():
        if _nome_local(elemento.tag) != "TextStream":
            continue
        trechos = []
        for filho in elemento:
            if _nome_local(filho.tag) != "TextRun":
                continue
            trechos.append(
                TrechoTexto(
                    texto="".join(filho.itertext()),
                    idioma=_inteiro_opcional(filho.attrib.get("lang")),
                    quebra=filho.attrib.get("break"),
                )
            )
        fluxos.append(FluxoTexto(tuple(trechos)))
    return tuple(fluxos)


_JSON_CARACTERE = re.compile(rb'\{\s*"character"\s*:')


def parse_estilos_texto(data: bytes) -> tuple[EstiloTexto, ...]:
    """Extrai estilos completos de caractere de um bloco ``txsm``.

    Texto de parágrafo pode trazer um JSON por parágrafo. Pequenos registros
    ``{"character": {}}`` são ignorados porque não descrevem uma fonte.
    """
    estilos: list[EstiloTexto] = []
    decoder = json.JSONDecoder()
    for match in _JSON_CARACTERE.finditer(data):
        try:
            texto = data[match.start():].decode("utf-8", errors="surrogateescape")
            bruto, _ = decoder.raw_decode(texto)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        caractere = bruto.get("character")
        if not isinstance(caractere, dict):
            continue
        latino = caractere.get("latin")
        if not isinstance(latino, dict) or not latino.get("font"):
            continue
        estilos.append(
            EstiloTexto(
                fonte=latino.get("font"),
                tamanho_unidades=_inteiro_opcional(latino.get("size")),
                italico=_booleano_codigo(latino.get("italic")),
                sublinhado=_booleano_codigo(latino.get("underline")),
                tachado=_booleano_codigo(latino.get("strikeout")),
                peso_codigo=_inteiro_opcional(latino.get("weight")),
                bruto=bruto,
            )
        )
    return tuple(estilos)
