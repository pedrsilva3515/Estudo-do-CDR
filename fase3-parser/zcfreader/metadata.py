"""Leitura dos metadados XMP gravados em ``META-INF/metadata.xml``.

Ao contrario de ``page*.dat``, este membro e XML documentado pela propria
estrutura do arquivo e nao exige inferencia sobre chunks binarios. Ele traz
um resumo util para pre-flight: tamanho nominal da pagina, contagens de
paginas/layers/objetos, fontes usadas e informacoes da versao do CorelDRAW.

Os valores ``PageWidth`` e ``PageHeight`` usam 10.000 unidades por mm
(a mesma escala de 100.000 unidades por cm observada em ``page*.dat``).
Em documentos com paginas de tamanhos diferentes, o XML oferece apenas um
resumo de pagina; portanto estes campos nao devem ser tratados como a medida
individual de todas as paginas sem validacao adicional.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import xml.etree.ElementTree as ET


NS = {
    "cdr": "http://namespace.corel.com/cdr/metadata/1.0/",
    "cdrinfo": "http://namespace.corel.com/cdr/metadata/1.0/fileinfo/",
    "crl": "http://namespace.corel.com/zcf/metadata/1.0/",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
}


class FormatoMetadadosInvalido(ValueError):
    """Levantado quando o XML de metadados nao pode ser interpretado."""


def _texto(root: ET.Element, caminho: str) -> str | None:
    no = root.find(caminho, NS)
    if no is None or no.text is None:
        return None
    valor = no.text.strip()
    return valor or None


def _inteiro(root: ET.Element, caminho: str) -> int | None:
    valor = _texto(root, caminho)
    if valor is None:
        return None
    try:
        return int(valor)
    except ValueError as exc:
        raise FormatoMetadadosInvalido(
            f"valor inteiro invalido em {caminho}: {valor!r}"
        ) from exc


def _contagens_recurso(root: ET.Element, caminho: str) -> dict[str, int]:
    recurso = root.find(caminho, NS)
    if recurso is None:
        return {}
    resultado: dict[str, int] = {}
    for filho in recurso:
        nome = filho.tag.rsplit("}", 1)[-1]
        try:
            resultado[nome] = int((filho.text or "0").strip())
        except ValueError:
            continue
    return resultado


@dataclass(frozen=True)
class MetadadosDocumento:
    paginas: int | None = None
    layers: int | None = None
    largura_pagina_unidades: int | None = None
    altura_pagina_unidades: int | None = None
    nome_tamanho_pagina: str | None = None
    dimensoes_pagina_texto: str | None = None
    orientacao_codigo: int | None = None
    resolucao_x_dpi: int | None = None
    resolucao_y_dpi: int | None = None
    core_version: int | None = None
    app_version: int | None = None
    build_number: int | None = None
    fontes_usadas: tuple[str, ...] = ()
    fontes_incorporadas: bool | None = None
    contagem_objetos: dict[str, int] = field(default_factory=dict)
    contagem_efeitos: dict[str, int] = field(default_factory=dict)

    @property
    def largura_pagina_mm(self) -> float | None:
        if self.largura_pagina_unidades is None:
            return None
        return self.largura_pagina_unidades / 10_000.0

    @property
    def altura_pagina_mm(self) -> float | None:
        if self.altura_pagina_unidades is None:
            return None
        return self.altura_pagina_unidades / 10_000.0

    @property
    def orientacao(self) -> str | None:
        """Deriva retrato/paisagem pelas dimensoes, sem adivinhar o enum Corel."""
        largura = self.largura_pagina_unidades
        altura = self.altura_pagina_unidades
        if largura is None or altura is None:
            return None
        if largura == altura:
            return "quadrada"
        return "retrato" if altura > largura else "paisagem"


def parse_metadata(data: bytes) -> MetadadosDocumento:
    """Decodifica ``META-INF/metadata.xml`` a partir de seus bytes."""
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise FormatoMetadadosInvalido(f"XML de metadados invalido: {exc}") from exc

    fontes = tuple(
        (no.text or "").strip()
        for no in root.findall(".//cdrinfo:FontsUsed/rdf:Bag/rdf:li", NS)
        if (no.text or "").strip()
    )
    incorporadas_texto = _texto(root, ".//cdrinfo:FontsEmbedded")
    incorporadas = None
    if incorporadas_texto is not None:
        incorporadas = incorporadas_texto.casefold() == "true"

    return MetadadosDocumento(
        paginas=_inteiro(root, ".//cdrinfo:NumPages"),
        layers=_inteiro(root, ".//cdrinfo:NumLayers"),
        largura_pagina_unidades=_inteiro(root, ".//cdrinfo:PageWidth"),
        altura_pagina_unidades=_inteiro(root, ".//cdrinfo:PageHeight"),
        nome_tamanho_pagina=_texto(root, ".//cdrinfo:PageSizeName"),
        dimensoes_pagina_texto=_texto(root, ".//cdrinfo:PageDimensions"),
        orientacao_codigo=_inteiro(root, ".//cdrinfo:PageOrientation"),
        resolucao_x_dpi=_inteiro(root, ".//cdrinfo:ResolutionX"),
        resolucao_y_dpi=_inteiro(root, ".//cdrinfo:ResolutionY"),
        core_version=_inteiro(root, ".//cdr:CoreVersion"),
        app_version=_inteiro(root, ".//cdr:AppVersion"),
        build_number=_inteiro(root, ".//cdr:BuildNumber"),
        fontes_usadas=fontes,
        fontes_incorporadas=incorporadas,
        contagem_objetos=_contagens_recurso(root, ".//cdrinfo:Objects"),
        contagem_efeitos=_contagens_recurso(root, ".//cdrinfo:Effects"),
    )
