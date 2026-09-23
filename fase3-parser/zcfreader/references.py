"""Localiza instancias que referenciam imagens de ``Bitmaps.dat``.

Os descritores aparecem em ``pageN.dat`` para objetos comuns e tambem podem
aparecer em ``dataN.dat`` (observado em objetos dentro de PowerClip). O layout
confirmado pelos casos controlados e por um arquivo real e::

    uint16  tipo                  observado = 2
    uint16  bits_por_pixel        24 (RGB) ou 32 (CMYK)
    uint32  largura
    uint32  altura
    uint32  indice_logico         ordem interna; sem semantica completa ainda
    uint32  identificador_bitmap  liga ao prefixo do registro UI em Bitmaps.dat
    ...     sentinelas/campos ainda nao interpretados

A deteccao valida simultaneamente identificador, dimensoes, bpp e sentinelas
estruturais para evitar tratar coincidencias binárias como referencias.
"""
from __future__ import annotations

from dataclasses import dataclass
import math
import struct
from typing import TYPE_CHECKING

from .bitmaps import ArquivoBitmaps, RegistroBitmap

if TYPE_CHECKING:
    from .structure import ObjetoEstrutural


@dataclass(frozen=True)
class MatrizAfim:
    a: float
    b: float
    tx: float
    c: float
    d: float
    ty: float

    @property
    def escala_x(self) -> float:
        return math.hypot(self.a, self.c)

    @property
    def escala_y(self) -> float:
        return math.hypot(self.b, self.d)

    @property
    def rotacao_graus(self) -> float:
        """Rotacao do eixo X, em graus, para matrizes sem cisalhamento."""
        return math.degrees(math.atan2(self.c, self.a))

    @property
    def determinante(self) -> float:
        return self.a * self.d - self.b * self.c

    @property
    def espelhada(self) -> bool:
        return self.determinante < 0


@dataclass(frozen=True)
class InstanciaBitmap:
    membro: str
    offset: int
    indice_logico: int
    identificador_bitmap: int
    registro: RegistroBitmap
    numero_nos: int
    matriz_local: MatrizAfim | None = None
    objeto: "ObjetoEstrutural | None" = None

    @property
    def matriz_final(self) -> MatrizAfim | None:
        """Matriz absoluta confirmada pelo indice de root.dat, quando disponivel."""
        return self.objeto.matriz if self.objeto is not None else None

    @property
    def dpi_efetivo_x(self) -> float | None:
        matriz = self.matriz_final
        if matriz is None or matriz.escala_x == 0:
            return None
        return self.registro.imagem.resolucao_x_dpi / matriz.escala_x

    @property
    def dpi_efetivo_y(self) -> float | None:
        matriz = self.matriz_final
        if matriz is None or matriz.escala_y == 0:
            return None
        return self.registro.imagem.resolucao_y_dpi / matriz.escala_y

    @property
    def dpi_efetivo_local_x(self) -> float | None:
        """DPI apos a matriz local, sem transformacoes de grupos/PowerClip."""
        if self.matriz_local is None or self.matriz_local.escala_x == 0:
            return None
        return self.registro.imagem.resolucao_x_dpi / self.matriz_local.escala_x

    @property
    def dpi_efetivo_local_y(self) -> float | None:
        """DPI apos a matriz local, sem transformacoes de grupos/PowerClip."""
        if self.matriz_local is None or self.matriz_local.escala_y == 0:
            return None
        return self.registro.imagem.resolucao_y_dpi / self.matriz_local.escala_y

    @property
    def largura_local_mm(self) -> float | None:
        imagem = self.registro.imagem
        if self.matriz_local is None or imagem.resolucao_x_dpi <= 0:
            return None
        return imagem.largura / imagem.resolucao_x_dpi * 25.4 * self.matriz_local.escala_x

    @property
    def altura_local_mm(self) -> float | None:
        imagem = self.registro.imagem
        if self.matriz_local is None or imagem.resolucao_y_dpi <= 0:
            return None
        return imagem.altura / imagem.resolucao_y_dpi * 25.4 * self.matriz_local.escala_y

    @property
    def largura_efetiva_mm(self) -> float | None:
        imagem = self.registro.imagem
        matriz = self.matriz_final
        if matriz is None or imagem.resolucao_x_dpi <= 0:
            return None
        return imagem.largura / imagem.resolucao_x_dpi * 25.4 * matriz.escala_x

    @property
    def altura_efetiva_mm(self) -> float | None:
        imagem = self.registro.imagem
        matriz = self.matriz_final
        if matriz is None or imagem.resolucao_y_dpi <= 0:
            return None
        return imagem.altura / imagem.resolucao_y_dpi * 25.4 * matriz.escala_y


def parse_instancias_bitmap(
    data: bytes, membro: str, bitmaps: ArquivoBitmaps
) -> list[InstanciaBitmap]:
    """Encontra descritores de instancia em um membro binario do ZCF."""
    por_id = {registro.identificador: registro for registro in bitmaps}
    encontradas: list[InstanciaBitmap] = []

    # O menor descritor confirmado usa 44 bytes ate a ultima sentinela que
    # verificamos. A varredura byte a byte e intencional: chunks podem comecar
    # em offsets nao alinhados em 4 bytes.
    for offset in range(0, max(0, len(data) - 43)):
        tipo, bpp = struct.unpack_from("<HH", data, offset)
        if tipo != 2:
            continue
        largura, altura, indice_logico, identificador = struct.unpack_from(
            "<IIII", data, offset + 4
        )
        registro = por_id.get(identificador)
        if registro is None:
            continue
        imagem = registro.imagem
        if (largura, altura, bpp) != (
            imagem.largura,
            imagem.altura,
            imagem.bits_por_pixel,
        ):
            continue
        if data[offset + 20:offset + 24] != b"\x00" * 4:
            continue
        if data[offset + 28:offset + 32] != b"\xff" * 4:
            continue
        # Em +32 os casos controlados trazem 8 bytes zerados, mas um pedido real
        # ("adesivo recortado - mateus ms 2309", bitmap dentro de PowerClip
        # elíptico) traz dois uint32 = 2. Tipo, identificador, dimensões, bpp e as
        # sentinelas acima já identificam o descritor; aceitam-se valores pequenos.
        campo_32 = struct.unpack_from("<II", data, offset + 32)
        if any(valor > 0xFFFF for valor in campo_32):
            continue

        numero_nos = struct.unpack_from("<I", data, offset + 40)[0]
        matriz_offset = offset + 144 + 9 * numero_nos
        matriz = None
        if matriz_offset + 48 <= len(data):
            valores = struct.unpack_from("<6d", data, matriz_offset)
            if all(math.isfinite(v) for v in valores):
                candidata = MatrizAfim(*valores)
                if candidata.escala_x > 0 and candidata.escala_y > 0:
                    matriz = candidata

        encontradas.append(
            InstanciaBitmap(
                membro=membro,
                offset=offset,
                indice_logico=indice_logico,
                identificador_bitmap=identificador,
                registro=registro,
                numero_nos=numero_nos,
                matriz_local=matriz,
            )
        )
    return encontradas
