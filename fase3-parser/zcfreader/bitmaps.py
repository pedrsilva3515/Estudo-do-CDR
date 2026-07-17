"""Parser de content/data/Bitmaps.dat (arquivo interno do formato ZCF do
CorelDRAW moderno).

Estrutura confirmada por engenharia reversa incremental — ver
docs/descobertas-fase2.md e docs/descobertas-fase1b.md no repositorio do
projeto para o detalhamento completo, com nivel de confianca por achado.

Resumo da estrutura:

    Bitmaps.dat = cabecalho de 8 bytes + sequencia de registros "UI".

Cada registro UI representa uma IMAGEM UNICA armazenada no documento —
bitmaps duplicados (o mesmo bitmap usado varias vezes na pagina) sao
deduplicados: so existe um registro UI por imagem distinta, e as demais
instancias sao referencias a partir de page*.dat (que este modulo nao le).

Cada UI contem 1 ou 2 registros "RI" aninhados:
  - RI #1: a imagem em si — pixels descomprimidos, linhas de cima para
    baixo (top-down), 24 bits/pixel em BGR (RGB) ou 32 bits/pixel em
    C,M,Y,K (CMYK), confirmado visualmente comparando com as cores
    conhecidas dos casos de teste da Fase 1/1b.
  - RI #2 (se presente): mascara de transparencia em escala de cinza
    (8 bits/pixel), mesmas dimensoes da imagem principal. Deteccao de
    presenca e estrutural (sobra de bytes dentro do UI apos o RI #1), nao
    depende de nenhum campo de flag ainda nao confirmado.

Os dois niveis tem convencoes de tamanho DIFERENTES (confirmado
empiricamente comparando varios casos de teste — nao presuma que sao
iguais so por terem a mesma forma tag+tamanho):

  - UI: o campo de tamanho mede o comprimento do PAYLOAD quando o
    registro nao e o ultimo do seu escopo; quando E o ultimo, mede a
    distancia da TAG ate o fim do escopo (inclui o proprio cabecalho
    de 8 bytes na contagem). `_fim_do_registro` decide qual das duas
    regras vale, por aritmetica pura.
  - RI: o campo de tamanho SEMPRE mede a distancia da TAG ate o fim do
    registro (offset + tamanho, sem nenhum ajuste de cabeçalho), tanto
    para o ultimo RI de um UI quanto para um RI seguido de outro.

Entre o fim dos dados de pixel de uma imagem e a tag UI da imagem
seguinte (quando ha uma), existem 8 bytes extras (um contador + uma
flag, no mesmo formato dos 8 bytes que abrem o arquivo) que ficam
"dentro" do tamanho declarado pelo UI anterior mas fora do RI. O parser
ignora esses bytes explicitamente (nao tenta interpreta-los como um
registro RI) verificando a tag antes de tratar a sobra como mascara.
"""
from __future__ import annotations

import struct
from dataclasses import dataclass, field

UI_TAG = b"UI\x00\x00"
RI_TAG = b"RI"

_UI_HEADER_LEN = 8   # tag(4) + tamanho(4)
_UI_RI_OFF = 32      # offset do 1o RI, relativo ao inicio do UI

# Offsets dentro de um registro RI, relativos ao inicio da sua tag.
_RI_TAMANHO_OFF = 2
_RI_LARGURA_OFF = 22
_RI_ALTURA_OFF = 26
_RI_BPP_OFF = 34
_RI_STRIDE_OFF = 38
_RI_TAMANHO_DADOS_OFF = 42
_RI_RESX_OFF = 50
_RI_RESY_OFF = 54
_RI_HEADER_TOTAL = 78  # bytes da tag RI ate o inicio dos dados de pixel


class FormatoBitmapsInvalido(ValueError):
    """Levantado quando Bitmaps.dat nao segue a estrutura esperada."""


@dataclass
class ImagemBruta:
    """Uma imagem decodificada de um unico registro RI."""

    largura: int
    altura: int
    bits_por_pixel: int
    stride: int
    resolucao_x_dpi: float
    resolucao_y_dpi: float
    pixels: bytes  # bruto, top-down, layout conforme bits_por_pixel

    @property
    def espaco_de_cor(self) -> str:
        return {24: "RGB", 32: "CMYK", 8: "Gray"}.get(self.bits_por_pixel, "desconhecido")


@dataclass
class RegistroBitmap:
    """Um registro UI: uma imagem unica armazenada, com mascara opcional."""

    indice: int
    offset: int
    imagem: ImagemBruta
    mascara: ImagemBruta | None = None

    def salvar_png(self, caminho) -> None:
        """Grava a imagem (com transparencia, se houver mascara) como PNG."""
        from .png_writer import write_png
        from .render import para_rgba

        largura, altura, pixels = para_rgba(self)
        write_png(caminho, largura, altura, pixels, canais=4)


@dataclass
class ArquivoBitmaps:
    """Bitmaps.dat decodificado: sequencia de imagens unicas (deduplicadas)."""

    registros: list[RegistroBitmap] = field(default_factory=list)

    def __len__(self) -> int:
        return len(self.registros)

    def __iter__(self):
        return iter(self.registros)

    def __getitem__(self, i):
        return self.registros[i]


def _px_por_metro_para_dpi(valor: int) -> float:
    return valor * 0.0254 / 1000.0


def _fim_do_registro(offset: int, tamanho_campo: int, header_len: int, fim_do_escopo: int) -> int:
    """Aplica a regra de tamanho do formato (ver docstring do modulo) por
    aritmetica pura: compara a hipotese "registro nao-final" contra o fim
    do escopo conhecido, sem espiar bytes seguintes.
    """
    candidato = offset + header_len + tamanho_campo
    if candidato - fim_do_escopo == header_len:
        return fim_do_escopo  # registro final: tamanho contava ate o fim do escopo
    if candidato > fim_do_escopo:
        raise FormatoBitmapsInvalido(
            f"registro no offset {offset} declara tamanho {tamanho_campo}, "
            f"que ultrapassa o fim do escopo ({fim_do_escopo})"
        )
    return candidato  # registro nao-final: tamanho era so o payload


def _ler_ri(data: bytes, offset: int, fim_do_escopo: int) -> tuple[ImagemBruta, int]:
    """Decodifica um registro RI a partir de `offset`. Devolve a imagem e o
    offset absoluto de fim deste registro.

    Diferente do UI, o tamanho do RI sempre mede a distancia da tag ate o
    fim do registro (sem regra dupla final/nao-final) — ver docstring do
    modulo.
    """
    if data[offset:offset + 2] != RI_TAG:
        raise FormatoBitmapsInvalido(
            f"esperava tag 'RI' no offset {offset}, encontrado {data[offset:offset + 2]!r}"
        )
    tamanho_campo = struct.unpack_from("<I", data, offset + _RI_TAMANHO_OFF)[0]
    fim_registro = offset + tamanho_campo
    if fim_registro > fim_do_escopo:
        raise FormatoBitmapsInvalido(
            f"registro RI no offset {offset} declara tamanho {tamanho_campo}, "
            f"que ultrapassa o fim do escopo ({fim_do_escopo})"
        )

    largura = struct.unpack_from("<I", data, offset + _RI_LARGURA_OFF)[0]
    altura = struct.unpack_from("<I", data, offset + _RI_ALTURA_OFF)[0]
    bpp = struct.unpack_from("<I", data, offset + _RI_BPP_OFF)[0]
    stride = struct.unpack_from("<I", data, offset + _RI_STRIDE_OFF)[0]
    tamanho_dados = struct.unpack_from("<I", data, offset + _RI_TAMANHO_DADOS_OFF)[0]
    resx = struct.unpack_from("<I", data, offset + _RI_RESX_OFF)[0]
    resy = struct.unpack_from("<I", data, offset + _RI_RESY_OFF)[0]

    inicio_pixels = offset + _RI_HEADER_TOTAL
    pixels = data[inicio_pixels:inicio_pixels + tamanho_dados]
    if len(pixels) != tamanho_dados:
        raise FormatoBitmapsInvalido(
            f"registro RI no offset {offset} declara {tamanho_dados} bytes de pixel, "
            f"mas so {len(pixels)} estao disponiveis ate o fim do escopo"
        )

    imagem = ImagemBruta(
        largura=largura,
        altura=altura,
        bits_por_pixel=bpp,
        stride=stride,
        resolucao_x_dpi=_px_por_metro_para_dpi(resx),
        resolucao_y_dpi=_px_por_metro_para_dpi(resy),
        pixels=pixels,
    )
    return imagem, fim_registro


def parse_bitmaps(data: bytes) -> ArquivoBitmaps:
    """Decodifica o conteudo bruto de content/data/Bitmaps.dat."""
    if len(data) < 8:
        raise FormatoBitmapsInvalido("arquivo curto demais para ter o cabecalho de 8 bytes")

    registros: list[RegistroBitmap] = []
    offset = 8
    indice = 0
    while offset + _UI_HEADER_LEN <= len(data):
        tag = data[offset:offset + 4]
        if tag != UI_TAG:
            raise FormatoBitmapsInvalido(f"tag inesperada no offset {offset}: {tag!r}")
        tamanho_campo = struct.unpack_from("<I", data, offset + 4)[0]
        fim_registro = _fim_do_registro(offset, tamanho_campo, _UI_HEADER_LEN, len(data))

        ri_offset = offset + _UI_RI_OFF
        imagem, fim_ri1 = _ler_ri(data, ri_offset, fim_registro)

        # A sobra entre o fim do RI da imagem e o fim do escopo do UI so e
        # uma mascara se realmente comecar com a tag RI — caso contrario e
        # o "cabecalho" de 8 bytes da proxima imagem (ver docstring do
        # modulo), que nao pertence a este registro e deve ser ignorado.
        mascara = None
        if fim_ri1 + 2 <= fim_registro and data[fim_ri1:fim_ri1 + 2] == RI_TAG:
            mascara, _ = _ler_ri(data, fim_ri1, fim_registro)

        registros.append(
            RegistroBitmap(indice=indice, offset=offset, imagem=imagem, mascara=mascara)
        )
        indice += 1
        offset = fim_registro

    return ArquivoBitmaps(registros=registros)
