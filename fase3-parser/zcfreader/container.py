"""Abre um `.cdr` no formato ZCF (ZIP Container Format) e expoe seus
membros internos. O `.cdr` moderno do CorelDRAW e, na pratica, um ZIP
comum contendo `mimetype`, `content/root.dat`, `content/data/*.dat`,
XMLs de metadados e previews PNG — ver docs/evidencias-amostra-helo.md.
"""
from __future__ import annotations

import zipfile
from pathlib import Path

MIMETYPE_ESPERADO = b"application/x-vnd.corel.zcf.draw.document+zip"


class ZcfContainer:
    """Wrapper fino sobre o ZIP interno de um `.cdr` ZCF."""

    def __init__(self, caminho):
        self.caminho = Path(caminho)
        self._zip = zipfile.ZipFile(self.caminho)

    def close(self) -> None:
        self._zip.close()

    def __enter__(self) -> "ZcfContainer":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def read(self, membro: str) -> bytes:
        return self._zip.read(membro)

    def namelist(self) -> list[str]:
        return self._zip.namelist()

    def tem_membro(self, membro: str) -> bool:
        return membro in self._zip.namelist()

    @property
    def arquivos_de_dados(self) -> list[str]:
        """Nomes listados em content/dataFileList.dat (relativos a
        content/data/), na ordem em que aparecem no indice."""
        if not self.tem_membro("content/dataFileList.dat"):
            return []
        bruto = self.read("content/dataFileList.dat").decode("ascii", errors="replace")
        return [linha.strip() for linha in bruto.splitlines() if linha.strip()]

    def bitmaps(self):
        """Decodifica content/data/Bitmaps.dat, se presente no documento.
        Devolve None se o documento nao tiver nenhum bitmap."""
        if not self.tem_membro("content/data/Bitmaps.dat"):
            return None
        from .bitmaps import parse_bitmaps
        return parse_bitmaps(self.read("content/data/Bitmaps.dat"))

    def pagina(self, indice: int = 1):
        """Extrai nomes e estilos (fill/outline/transparency) de
        content/data/page{indice}.dat — ver zcfreader.page para o que e
        extraido e as limitacoes (nao ha parser de geometria ainda, e o
        pareamento nome->estilo so e confiavel se todo objeto tem nome).
        Devolve None se a pagina nao existir."""
        membro = f"content/data/page{indice}.dat"
        if not self.tem_membro(membro):
            return None
        from .page import parse_page
        return parse_page(self.read(membro))

    def estilos_da_pagina(self, indice: int = 1):
        """Devolve TODOS os blocos de estilo (fill/outline/transparency)
        de content/data/page{indice}.dat, com offset, sem depender de o
        objeto ter nome — mais confiavel que `.pagina()` em documentos
        reais, onde a maioria dos objetos nao e nomeada. Devolve None se
        a pagina nao existir."""
        membro = f"content/data/page{indice}.dat"
        if not self.tem_membro(membro):
            return None
        from .page import parse_estilos
        return parse_estilos(self.read(membro))


def abrir_cdr(caminho) -> ZcfContainer:
    """Abre um arquivo `.cdr` (ou `.zip` equivalente) para leitura."""
    return ZcfContainer(caminho)
