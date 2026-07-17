"""Converte ImagemBruta / RegistroBitmap (pixels no layout interno do ZCF)
para RGB/RGBA top-down prontos para gravar como PNG.

A conversao CMYK->RGB e ingenua (formula padrao sem gestao de cor / perfil
ICC): serve bem para preview e extracao de conteudo, mas as cores podem
divergir um pouco do que o CorelDRAW renderiza com o perfil de cor do
documento. Ver limitacoes em fase3-parser/README.md.
"""
from __future__ import annotations

from .bitmaps import ImagemBruta, RegistroBitmap


def _bgr_para_rgb_linha(linha: bytes) -> bytes:
    saida = bytearray(len(linha))
    saida[0::3] = linha[2::3]  # R <- B
    saida[1::3] = linha[1::3]  # G <- G
    saida[2::3] = linha[0::3]  # B <- R
    return bytes(saida)


def _cmyk_para_rgb_linha(linha: bytes, largura: int) -> bytes:
    saida = bytearray(largura * 3)
    for x in range(largura):
        i = x * 4
        c, m, y, k = linha[i], linha[i + 1], linha[i + 2], linha[i + 3]
        fator_k = 1 - k / 255
        saida[x * 3] = int(255 * (1 - c / 255) * fator_k)
        saida[x * 3 + 1] = int(255 * (1 - m / 255) * fator_k)
        saida[x * 3 + 2] = int(255 * (1 - y / 255) * fator_k)
    return bytes(saida)


def para_rgb(imagem: ImagemBruta) -> tuple[int, int, bytes]:
    """Devolve (largura, altura, pixels_rgb_topdown), sem canal alfa."""
    w, h, bpp = imagem.largura, imagem.altura, imagem.bits_por_pixel
    bytes_por_pixel = bpp // 8
    linhas = []
    for y in range(h):
        inicio = y * imagem.stride
        linha = imagem.pixels[inicio:inicio + w * bytes_por_pixel]
        if bpp == 24:
            linhas.append(_bgr_para_rgb_linha(linha))
        elif bpp == 32:
            linhas.append(_cmyk_para_rgb_linha(linha, w))
        else:
            raise ValueError(f"bits_por_pixel nao suportado para conversao para RGB: {bpp}")
    return w, h, b"".join(linhas)


def para_rgba(registro: RegistroBitmap) -> tuple[int, int, bytes]:
    """Devolve (largura, altura, pixels_rgba_topdown). Sem mascara, o canal
    alfa fica 255 (totalmente opaco) em todos os pixels."""
    largura, altura, rgb = para_rgb(registro.imagem)

    saida = bytearray(largura * altura * 4)
    saida[0::4] = rgb[0::3]
    saida[1::4] = rgb[1::3]
    saida[2::4] = rgb[2::3]

    if registro.mascara is None:
        saida[3::4] = bytes([255]) * (largura * altura)
        return largura, altura, bytes(saida)

    mascara = registro.mascara
    if mascara.largura != largura or mascara.altura != altura:
        raise ValueError(
            f"mascara ({mascara.largura}x{mascara.altura}) tem dimensoes "
            f"diferentes da imagem principal ({largura}x{altura})"
        )
    alfa = bytearray(largura * altura)
    for y in range(altura):
        inicio = y * mascara.stride
        alfa[y * largura:(y + 1) * largura] = mascara.pixels[inicio:inicio + largura]
    saida[3::4] = bytes(alfa)
    return largura, altura, bytes(saida)
