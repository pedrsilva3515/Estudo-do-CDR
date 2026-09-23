"""Renderização própria da página a partir do CDR, sem o CorelDRAW.

Não busca fidelidade de impressão: o objetivo é uma imagem nítida o bastante
para o OCR ler instruções convertidas em curvas e para a IA ver a montagem.
Desenha curvas (retas e Bézier, com furos por par-ímpar), retângulos, elipses,
bitmaps e textos nativos, com preenchimento uniforme e contorno, e recorta o
conteúdo de PowerClip pela forma do recipiente. Degradês usam a cor inicial;
padrões e rotação de bitmaps são ignorados.

A área desenhada é a união das caixas dos objetos de primeiro nível, a mesma
usada por ``experimento_agente.extrair_candidatos_agente`` para mapear pixels
em centímetros.
"""
from __future__ import annotations

from io import BytesIO
import os
from pathlib import Path

from .container import abrir_cdr
from .page import parse_cor_objeto, parse_estilos
from .render import para_rgba

LADO_MAXIMO_PADRAO = 2400
PASSOS_BEZIER = 12
_FONTES = ("arial.ttf", "segoeui.ttf", "DejaVuSans.ttf")


def _rgb(cor_texto) -> tuple[int, int, int] | None:
    cor = parse_cor_objeto(cor_texto)
    if cor is None:
        return None
    if cor.modelo == "SPOT" and cor.cor_alternativa is not None:
        cor = cor.cor_alternativa
    c = cor.componentes
    if cor.modelo in {"CMYK", "CMYK255"} and len(c) == 4:
        escala = 100 if cor.modelo == "CMYK" else 255
        ciano, magenta, amarelo, preto = (min(max(v / escala, 0), 1) for v in c)
        return tuple(round(255 * (1 - v) * (1 - preto)) for v in (ciano, magenta, amarelo))
    if cor.modelo == "RGB255" and len(c) == 3:
        return tuple(min(max(v, 0), 255) for v in c)
    if cor.modelo == "GRAY255" and len(c) == 1:
        return (c[0],) * 3
    return (128, 128, 128)


def _estilo_do_objeto(objeto, estilos_por_membro: dict) -> dict:
    if objeto.membro is None or objeto.offset_dados is None or objeto.tamanho_dados is None:
        return {}
    fim = objeto.offset_dados + objeto.tamanho_dados
    return next(
        (estilo for offset, estilo in estilos_por_membro.get(objeto.membro, ()) if objeto.offset_dados <= offset < fim),
        {},
    )


def _preenchimento(estilo: dict) -> tuple[int, int, int, int] | None:
    preenchimento = estilo.get("fill") or {}
    if str(preenchimento.get("type", "0")) == "0":
        return None
    cor = _rgb(preenchimento.get("primaryColor")) or (128, 128, 128)
    transparencia = estilo.get("transparency") or {}
    try:
        opacidade = 1 - float(transparencia.get("uniformTransparency") or 0)
    except (TypeError, ValueError):
        opacidade = 1.0
    if opacidade <= 0.05:
        return None
    return (*cor, round(255 * opacidade))


def _contorno(objeto, estilo: dict, px_por_unidade: float) -> tuple[tuple[int, int, int, int], int] | None:
    contorno = objeto.contorno
    if contorno is None or not contorno.presente:
        return None
    cor = _rgb(contorno.cor) or (0, 0, 0)
    largura_px = max(1, round(contorno.largura_unidades * px_por_unidade))
    return (*cor, 255), min(largura_px, 40)


def _subcaminhos_px(objeto, para_px) -> list[list[tuple[float, float]]]:
    pontos = objeto.pontos_curva_absolutos
    if not pontos:
        return []
    caminhos: list[list[tuple[float, float]]] = []
    controles: list[tuple[float, float]] = []
    for x, y, flag in pontos:
        papel = flag & 0xC0
        ponto = para_px(x, y)
        if papel == 0x00:
            caminhos.append([ponto])
            controles = []
        elif not caminhos:
            continue
        elif papel == 0xC0:
            controles.append(ponto)
        elif papel == 0x80 and len(controles) >= 2:
            (x0, y0), (x1, y1), (x2, y2), (x3, y3) = caminhos[-1][-1], controles[-2], controles[-1], ponto
            for passo in range(1, PASSOS_BEZIER + 1):
                t = passo / PASSOS_BEZIER
                u = 1 - t
                caminhos[-1].append((
                    u * u * u * x0 + 3 * u * u * t * x1 + 3 * u * t * t * x2 + t * t * t * x3,
                    u * u * u * y0 + 3 * u * u * t * y1 + 3 * u * t * t * y2 + t * t * t * y3,
                ))
            controles = []
        else:
            caminhos[-1].append(ponto)
            controles = []
    return [c for c in caminhos if len(c) >= 2]


def _fonte(tamanho: int):
    from PIL import ImageFont

    raiz = Path(os.environ.get("WINDIR", r"C:\Windows")) / "Fonts"
    for nome in _FONTES:
        try:
            return ImageFont.truetype(str(raiz / nome), tamanho)
        except OSError:
            try:
                return ImageFont.truetype(nome, tamanho)
            except OSError:
                continue
    return ImageFont.load_default(size=tamanho)


def renderizar_pagina(caminho: Path, lado_maximo_px: int = LADO_MAXIMO_PADRAO) -> bytes | None:
    """PNG da montagem inteira, ou None quando o documento não tem objetos medíveis."""
    from PIL import Image, ImageChops, ImageDraw

    with abrir_cdr(Path(caminho)) as doc:
        estrutura = list(doc.estrutura())
        topo = [o.caixa for o in estrutura if o.caixa is not None and not o.ancestrais and o.tipo in {"obj", "grp"}]
        if not topo:
            return None
        esquerda = min(c.esquerda for c in topo)
        direita = max(c.direita for c in topo)
        base = min(c.base for c in topo)
        cima = max(c.topo for c in topo)
        largura_u, altura_u = max(direita - esquerda, 1), max(cima - base, 1)
        escala = lado_maximo_px / max(largura_u, altura_u)
        tamanho = (max(1, round(largura_u * escala)), max(1, round(altura_u * escala)))

        def para_px(x: float, y: float) -> tuple[float, float]:
            return (x - esquerda) * escala, (cima - y) * escala

        def caixa_px(caixa) -> tuple[float, float, float, float]:
            x0, y0 = para_px(caixa.esquerda, caixa.topo)
            x1, y1 = para_px(caixa.direita, caixa.base)
            return min(x0, x1), min(y0, y1), max(x0, x1), max(y0, y1)

        estilos_por_membro = {m: parse_estilos(doc.read(m)) for m in {o.membro for o in estrutura if o.membro}}
        # Cada consulta ao documento cria objetos novos: a chave é a posição no root.dat.
        def chave(objeto) -> tuple:
            return objeto.membro, objeto.offset_root

        textos = {chave(item.objeto): item.fluxo.texto for item in doc.textos_por_objeto() or ()}
        bitmaps = {chave(i.objeto): i.registro for i in doc.instancias_bitmaps() if i.objeto is not None}
        recipientes = doc.recipientes_powerclip(estrutura)
        mascaras: dict[tuple, object] = {}

        def mascara_do_recipiente(recipiente):
            """Forma do PowerClip em tons de cinza (255 = visível)."""
            if chave(recipiente) not in mascaras:
                mascara = Image.new("L", tamanho, 0)
                forma = ImageDraw.Draw(mascara)
                caminhos = _subcaminhos_px(recipiente, para_px) if recipiente.tipo_objeto == "curva" else []
                if caminhos:
                    binaria = Image.new("1", tamanho, 0)
                    for caminho_px in caminhos:
                        sub = Image.new("1", tamanho, 0)
                        ImageDraw.Draw(sub).polygon(caminho_px, fill=1)
                        binaria = ImageChops.logical_xor(binaria, sub)
                    mascara = binaria.convert("L")
                elif recipiente.tipo_objeto == "elipse":
                    forma.ellipse(caixa_px(recipiente.caixa), fill=255)
                else:
                    forma.rectangle(caixa_px(recipiente.caixa), fill=255)
                mascaras[chave(recipiente)] = mascara
            return mascaras[chave(recipiente)]

        pagina = Image.new("RGBA", tamanho, (255, 255, 255, 255))
        # root.dat lista primeiro o objeto da frente; desenha-se de trás para a frente.
        for objeto in reversed(estrutura):
            if objeto.tipo != "obj" or objeto.caixa is None:
                continue
            estilo = _estilo_do_objeto(objeto, estilos_por_membro)
            camada = Image.new("RGBA", tamanho, (0, 0, 0, 0))
            desenho = ImageDraw.Draw(camada)
            preenchimento = _preenchimento(estilo)
            contorno = _contorno(objeto, estilo, escala)
            x0, y0, x1, y1 = caixa_px(objeto.caixa)
            tipo = objeto.tipo_objeto

            if tipo == "bitmap" and chave(objeto) in bitmaps:
                try:
                    largura, altura, rgba = para_rgba(bitmaps[chave(objeto)])
                    # Os pixels do ZCF são gravados de baixo para cima; a matriz pode espelhar.
                    imagem = Image.frombytes("RGBA", (largura, altura), rgba)
                    matriz = objeto.matriz
                    if matriz is None or matriz.d >= 0:
                        imagem = imagem.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                    if matriz is not None and matriz.a < 0:
                        imagem = imagem.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                    destino = (max(1, round(x1 - x0)), max(1, round(y1 - y0)))
                    camada.alpha_composite(imagem.resize(destino), (round(x0), round(y0)))
                except (ValueError, OSError):
                    desenho.rectangle((x0, y0, x1, y1), fill=(200, 200, 200, 255))
            elif tipo == "curva":
                caminhos = _subcaminhos_px(objeto, para_px)
                if preenchimento and caminhos:
                    mascara = Image.new("1", tamanho, 0)
                    for caminho_px in caminhos:
                        sub = Image.new("1", tamanho, 0)
                        ImageDraw.Draw(sub).polygon(caminho_px, fill=1)
                        mascara = ImageChops.logical_xor(mascara, sub)
                    camada.paste(preenchimento, mask=mascara.convert("L"))
                if contorno:
                    for caminho_px in caminhos:
                        desenho.line(caminho_px, fill=contorno[0], width=contorno[1])
            elif tipo in {"retangulo", "elipse", "desconhecido"}:
                forma = desenho.ellipse if tipo == "elipse" else desenho.rectangle
                forma((x0, y0, x1, y1), fill=preenchimento,
                      outline=contorno[0] if contorno else None, width=contorno[1] if contorno else 0)
            elif tipo == "texto" and textos.get(chave(objeto)):
                linhas = [linha.strip() for linha in textos[chave(objeto)].splitlines() if linha.strip()]
                if not linhas:
                    continue
                altura_linha = max(4, (y1 - y0) / len(linhas))
                largura_caixa = max(4, x1 - x0)
                fonte = _fonte(max(8, int(altura_linha * 0.9)))
                cor_texto = preenchimento or (0, 0, 0, 255)
                maior = max(desenho.textlength(linha, font=fonte) for linha in linhas) or 1
                for n, linha in enumerate(linhas):
                    # Cada linha é esticada na proporção da linha mais longa, para que o
                    # texto ocupe a mesma extensão da caixa do CDR (a regra "N DE CADA"
                    # usa a largura da legenda lida pelo OCR).
                    esquerda_t, topo_t, direita_t, base_t = desenho.textbbox((0, 0), linha, font=fonte)
                    rotulo = Image.new("RGBA", (max(1, direita_t - esquerda_t), max(1, base_t - topo_t)), (0, 0, 0, 0))
                    ImageDraw.Draw(rotulo).text((-esquerda_t, -topo_t), linha, fill=cor_texto, font=fonte)
                    destino = (
                        max(1, round(largura_caixa * (direita_t - esquerda_t) / maior)),
                        max(1, round(altura_linha * 0.8)),
                    )
                    camada.alpha_composite(
                        rotulo.resize(destino), (round(x0), round(y0 + n * altura_linha + altura_linha * 0.1)),
                    )
            else:
                continue
            recipiente = recipientes.get(chave(objeto))
            if recipiente is not None:
                # Conteúdo de PowerClip: só aparece o que está dentro da máscara.
                alfa = ImageChops.multiply(camada.getchannel("A"), mascara_do_recipiente(recipiente))
                camada.putalpha(alfa)
            pagina.alpha_composite(camada)

    saida = BytesIO()
    pagina.convert("RGB").save(saida, format="PNG")
    return saida.getvalue()
