"""Ferramenta de linha de comando do zcfreader.

Uso:
    python -m zcfreader.cli listar arquivo.cdr
    python -m zcfreader.cli extrair arquivo.cdr --saida pasta/
"""
from __future__ import annotations

import argparse
from collections import Counter
import sys
from pathlib import Path

from .container import abrir_cdr


def _listar(caminho: Path) -> int:
    with abrir_cdr(caminho) as doc:
        print(f"{caminho}")
        metadados = doc.metadados()
        if metadados is not None:
            largura = metadados.largura_pagina_mm
            altura = metadados.altura_pagina_mm
            tamanho = (
                f"{largura:g} x {altura:g} mm"
                if largura is not None and altura is not None
                else "desconhecido"
            )
            nome = f" ({metadados.nome_tamanho_pagina})" if metadados.nome_tamanho_pagina else ""
            print(
                f"  documento: {metadados.paginas or '?'} pagina(s), "
                f"{metadados.layers or '?'} layer(s)"
            )
            print(f"  pagina: {tamanho}{nome}, orientacao {metadados.orientacao or 'desconhecida'}")
            if metadados.contagem_objetos:
                print(f"  objetos: {metadados.contagem_objetos.get('Total', '?')} no total")
            if metadados.fontes_usadas:
                print(f"  fontes usadas: {', '.join(metadados.fontes_usadas)}")
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
            instancias = doc.instancias_bitmaps(bitmaps)
            print(f"  instancias de bitmap: {len(instancias)} objeto(s)")
            for instancia in instancias:
                dpi_local = ""
                if instancia.dpi_efetivo_x is not None:
                    dpi_local = (
                        f", DPI efetivo {instancia.dpi_efetivo_x:.0f}x"
                        f"{instancia.dpi_efetivo_y:.0f}, tamanho "
                        f"{instancia.largura_efetiva_mm:.1f}x"
                        f"{instancia.altura_efetiva_mm:.1f} mm"
                    )
                print(
                    f"    {instancia.membro}@{instancia.offset}: "
                    f"imagem [{instancia.registro.indice}] "
                    f"(id {instancia.identificador_bitmap}){dpi_local}"
                )

        objetos = [obj for obj in doc.estrutura() if obj.tipo == "obj"]
        if objetos:
            contagens = Counter(obj.tipo_objeto or "desconhecido" for obj in objetos)
            resumo = ", ".join(
                f"{tipo}={quantidade}" for tipo, quantidade in sorted(contagens.items())
            )
            com_caixa = sum(obj.caixa is not None for obj in objetos)
            com_matriz = sum(obj.matriz is not None for obj in objetos)
            print(
                f"  geometria: {len(objetos)} objeto(s) ({resumo}); "
                f"bbox={com_caixa}, matriz={com_matriz}"
            )
            curvas = [obj for obj in objetos if obj.tipo_objeto == "curva"]
            curvas_lidas = [obj for obj in curvas if obj.geometria_curva is not None]
            if curvas:
                total_pontos = sum(obj.geometria_curva.numero_pontos for obj in curvas_lidas)
                print(
                    f"  curvas: {len(curvas_lidas)}/{len(curvas)} decodificada(s), "
                    f"{total_pontos} ponto(s) compactos"
                )
            fluxos_texto = doc.textos()
            objetos_texto = [obj for obj in objetos if obj.tipo_objeto == "texto"]
            if fluxos_texto or objetos_texto:
                print(
                    f"  textos: {len(fluxos_texto)} fluxo(s), "
                    f"{len(objetos_texto)} objeto(s)"
                )
                for indice, fluxo in enumerate(fluxos_texto):
                    print(f"    fluxo [{indice}]: {fluxo.texto!r}")
                for objeto in objetos_texto:
                    estilos = ", ".join(
                        f"{estilo.fonte or '?'} "
                        f"{estilo.tamanho_pt:.2f} pt"
                        if estilo.tamanho_pt is not None
                        else f"{estilo.fonte or '?'} tamanho desconhecido"
                        for estilo in objeto.estilos_texto
                    )
                    print(
                        f"    objeto {objeto.tipo_texto or 'texto'}, "
                        f"pagina {objeto.pagina or '?'}: {estilos or 'sem estilo decodificado'}"
                    )

        paginas = doc.paginas_estruturais()
        for pagina in paginas:
            origem = "personalizado" if pagina.tamanho_personalizado else "padrao"
            print(
                f"  pagina {pagina.indice}: {pagina.largura_mm:g}x"
                f"{pagina.altura_mm:g} mm ({origem}), sangria {pagina.sangria_mm:g} mm"
            )
        ocorrencias = doc.conferencia_limites()
        if ocorrencias:
            print(f"  alerta: {len(ocorrencias)} objeto(s) excedem os limites da pagina")
            for ocorrencia in ocorrencias:
                lados = []
                for nome, valor in (
                    ("esquerda", ocorrencia.excede_esquerda_mm),
                    ("direita", ocorrencia.excede_direita_mm),
                    ("topo", ocorrencia.excede_topo_mm),
                    ("base", ocorrencia.excede_base_mm),
                ):
                    if valor > 0:
                        lados.append(f"{nome}={valor:.1f} mm")
                print(
                    f"    pagina {ocorrencia.pagina.indice}, "
                    f"{ocorrencia.objeto.tipo_objeto}: {', '.join(lados)} "
                    f"({'alem da sangria' if ocorrencia.ultrapassa_sangria else 'dentro da sangria'})"
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
