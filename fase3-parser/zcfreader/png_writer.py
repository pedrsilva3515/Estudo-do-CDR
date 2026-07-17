"""Escritor de PNG minimo, sem dependencias externas (so `zlib`/`struct` da
biblioteca padrao). Suficiente para gravar as imagens extraidas do
Bitmaps.dat sem depender de Pillow ou de outra lib de imagem.
"""
from __future__ import annotations

import struct
import zlib

_COLOR_TYPE_POR_CANAIS = {1: 0, 3: 2, 4: 6}  # grayscale, RGB, RGBA


def _chunk(tipo: bytes, dados: bytes) -> bytes:
    return (
        struct.pack(">I", len(dados))
        + tipo
        + dados
        + struct.pack(">I", zlib.crc32(tipo + dados))
    )


def write_png(path, largura: int, altura: int, pixels: bytes, canais: int) -> None:
    """Grava um PNG de 8 bits por canal a partir de pixels *top-down*
    (primeira linha do array = topo da imagem), sem padding entre linhas.

    `canais` deve ser 1 (grayscale), 3 (RGB) ou 4 (RGBA).
    """
    if canais not in _COLOR_TYPE_POR_CANAIS:
        raise ValueError(f"canais deve ser 1, 3 ou 4, recebido {canais}")

    linha_bytes = largura * canais
    esperado = linha_bytes * altura
    if len(pixels) != esperado:
        raise ValueError(
            f"tamanho de pixels incompativel: esperado {esperado} bytes "
            f"({largura}x{altura}x{canais}), recebido {len(pixels)}"
        )

    # PNG exige um byte de filtro (0 = "sem filtro") no inicio de cada linha.
    cru = bytearray((linha_bytes + 1) * altura)
    for y in range(altura):
        origem = y * linha_bytes
        destino = y * (linha_bytes + 1)
        cru[destino] = 0
        cru[destino + 1:destino + 1 + linha_bytes] = pixels[origem:origem + linha_bytes]

    ihdr = struct.pack(">IIBBBBB", largura, altura, 8, _COLOR_TYPE_POR_CANAIS[canais], 0, 0, 0)
    idat = zlib.compress(bytes(cru), level=6)

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(_chunk(b"IHDR", ihdr))
        f.write(_chunk(b"IDAT", idat))
        f.write(_chunk(b"IEND", b""))
