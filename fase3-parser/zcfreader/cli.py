"""Ferramenta de linha de comando do zcfreader.

Uso:
    python -m zcfreader.cli listar arquivo.cdr
    python -m zcfreader.cli extrair arquivo.cdr --saida pasta/
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .container import abrir_cdr


def _listar(caminho: Path) -> int:
    with abrir_cdr(caminho) as doc:
        print(f"{caminho}")
        print(f"  arquivos de dados: {', '.join(doc.arquivos_de_dados) or '(nenhum)'}")
        bitmaps = doc.bitmaps()
        if bitmaps is None:
            print("  bitmaps: nenhum (documento sem content/data/Bitmaps.dat)")
        else:
            print(f"  bitmaps: {len(bitmaps)} imagem(ns) unica(s)")
            for r in bitmaps:
                img = r.imagem
                mascara = f", com mascara de transparencia {r.mascara.largura}x{r.mascara.altura}" if r.mascara else ""
                print(
                    f"    [{r.indice}] {img.largura}x{img.altura} px, {img.espaco_de_cor} "
                    f"({img.bits_por_pixel} bpp), {img.resolucao_x_dpi:.0f}x{img.resolucao_y_dpi:.0f} dpi"
                    f"{mascara}"
                )

        itens = doc.pagina(1)
        if itens is not None:
            print(f"  page1.dat: {len(itens)} nome(s) encontrado(s) (layers e/ou objetos)")
            for item in itens:
                cor = ""
                if item.estilo and "fill" in item.estilo:
                    cor = f", cor: {item.estilo['fill'].get('primaryColor', '')}"
                print(f"    {item.nome!r}{cor}")
            estilos = doc.estilos_da_pagina(1) or []
            if len(estilos) != sum(1 for i in itens if i.estilo is not None):
                print(
                    f"  aviso: {len(estilos)} bloco(s) de estilo no total, mas so "
                    f"{sum(1 for i in itens if i.estilo is not None)} pareado(s) com um nome "
                    f"— documento tem objetos sem nome, use estilos_da_pagina() para ve-los todos"
                )
    return 0


def _extrair(caminho: Path, saida: Path) -> int:
    saida.mkdir(parents=True, exist_ok=True)
    with abrir_cdr(caminho) as doc:
        bitmaps = doc.bitmaps()
        if bitmaps is None or len(bitmaps) == 0:
            print("Nenhum bitmap para extrair.")
            return 0
        base = caminho.stem
        for r in bitmaps:
            destino = saida / f"{base}_bitmap{r.indice:02d}.png"
            r.salvar_png(destino)
            print(f"gravado: {destino}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="zcfreader", description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="comando", required=True)

    p_listar = sub.add_parser("listar", help="lista os bitmaps de um .cdr")
    p_listar.add_argument("arquivo", type=Path)

    p_extrair = sub.add_parser("extrair", help="extrai os bitmaps de um .cdr como PNG")
    p_extrair.add_argument("arquivo", type=Path)
    p_extrair.add_argument("--saida", type=Path, default=Path("."))

    args = ap.parse_args(argv)
    if args.comando == "listar":
        return _listar(args.arquivo)
    if args.comando == "extrair":
        return _extrair(args.arquivo, args.saida)
    ap.error("comando desconhecido")
    return 2


if __name__ == "__main__":
    sys.exit(main())
