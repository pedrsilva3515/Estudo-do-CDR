#!/usr/bin/env python3
"""Motor de diferencas binarias para arquivos .cdr no formato ZCF (Fase 2).

Compara dois arquivos .cdr (base vs. variante), extrai cada membro interno do
contêiner ZIP e reporta com precisao:

- membros que existem so no base ou so na variante;
- membros identicos;
- membros alterados, com as regioes de bytes que mudaram (offset, tamanho e
  hexdump lado a lado) quando os tamanhos sao iguais, ou prefixo/sufixo comum
  e o "miolo" divergente quando os tamanhos diferem.

Uso:
    python zcf_diff.py base.cdr variante.cdr [-o relatorio.md]
    python zcf_diff.py --all pasta_dos_casos [-o pasta_de_relatorios]

No modo --all, os manifestos caso_*.json da pasta sao lidos e cada caso com
"arquivo_base" preenchido e comparado contra sua base, gerando um relatorio
Markdown por caso.
"""

from __future__ import annotations

import argparse
import json
import sys
import zipfile
from pathlib import Path

# Diferencas separadas por menos de MERGE_GAP bytes iguais sao agrupadas na
# mesma regiao, para nao fragmentar o relatorio em milhares de micro-diffs.
MERGE_GAP = 32
# Bytes de contexto mostrados antes/depois de cada regiao no hexdump.
CONTEXTO = 16
# Limite de bytes hexdumpados por regiao (regioes maiores sao resumidas).
MAX_DUMP = 96
# Limite de regioes detalhadas por membro.
MAX_REGIOES = 40


def ler_membros(caminho: Path) -> dict[str, bytes]:
    """Extrai todos os membros do contêiner ZCF para a memoria."""
    with zipfile.ZipFile(caminho) as z:
        return {info.filename: z.read(info.filename) for info in z.infolist()}


def regioes_diferentes(a: bytes, b: bytes) -> list[tuple[int, int]]:
    """Regioes (offset, tamanho) onde a != b, para buffers do MESMO tamanho.

    Diferencas proximas (gap < MERGE_GAP) sao fundidas numa regiao so.
    """
    regioes: list[tuple[int, int]] = []
    inicio = None
    ultimo_diff = None
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            if inicio is None:
                inicio = i
            elif i - ultimo_diff > MERGE_GAP:
                regioes.append((inicio, ultimo_diff - inicio + 1))
                inicio = i
            ultimo_diff = i
    if inicio is not None:
        regioes.append((inicio, ultimo_diff - inicio + 1))
    return regioes


def prefixo_sufixo_comum(a: bytes, b: bytes) -> tuple[int, int]:
    """Tamanho do prefixo e do sufixo comuns entre dois buffers."""
    n = min(len(a), len(b))
    p = 0
    while p < n and a[p] == b[p]:
        p += 1
    s = 0
    while s < n - p and a[len(a) - 1 - s] == b[len(b) - 1 - s]:
        s += 1
    return p, s


def hexdump(dados: bytes, offset_base: int = 0) -> str:
    linhas = []
    for i in range(0, len(dados), 16):
        parte = dados[i : i + 16]
        hexs = " ".join(f"{c:02x}" for c in parte)
        asc = "".join(chr(c) if 32 <= c < 127 else "." for c in parte)
        linhas.append(f"  {offset_base + i:10d}  {hexs:<47}  {asc}")
    return "\n".join(linhas)


def dump_regiao(rotulo: str, dados: bytes, ini: int, tam: int) -> list[str]:
    """Hexdump de uma regiao com contexto, truncado em MAX_DUMP bytes."""
    ctx_ini = max(0, ini - CONTEXTO)
    ctx_fim = min(len(dados), ini + tam + CONTEXTO)
    truncado = ""
    if ctx_fim - ctx_ini > MAX_DUMP:
        ctx_fim = ctx_ini + MAX_DUMP
        truncado = f"  ... (regiao truncada; tamanho real {tam} bytes)"
    out = [f"{rotulo}:", hexdump(dados[ctx_ini:ctx_fim], ctx_ini)]
    if truncado:
        out.append(truncado)
    return out


def comparar_membro(nome: str, a: bytes, b: bytes) -> list[str]:
    """Relatorio Markdown das diferencas de um membro presente nos dois lados."""
    out = [f"### `{nome}` — ALTERADO ({len(a)} -> {len(b)} bytes)", ""]

    if len(a) == len(b):
        regioes = regioes_diferentes(a, b)
        out.append(f"Mesmo tamanho; {len(regioes)} regiao(oes) alterada(s):")
        out.append("")
        for n, (ini, tam) in enumerate(regioes[:MAX_REGIOES], 1):
            out.append(f"**Regiao {n}: offset {ini}, {tam} byte(s)**")
            out.append("```")
            out.extend(dump_regiao("base", a, ini, tam))
            out.extend(dump_regiao("variante", b, ini, tam))
            out.append("```")
            out.append("")
        if len(regioes) > MAX_REGIOES:
            out.append(f"... e mais {len(regioes) - MAX_REGIOES} regioes omitidas.")
            out.append("")
    else:
        p, s = prefixo_sufixo_comum(a, b)
        miolo_a = len(a) - p - s
        miolo_b = len(b) - p - s
        out.append(
            f"Tamanhos diferentes (delta {len(b) - len(a):+d}). "
            f"Prefixo comum: {p} bytes; sufixo comum: {s} bytes."
        )
        out.append(
            f"Miolo divergente: base [{p}..{len(a) - s}) = {miolo_a} bytes, "
            f"variante [{p}..{len(b) - s}) = {miolo_b} bytes."
        )
        out.append("")
        out.append("```")
        out.extend(dump_regiao("base (inicio do miolo)", a, p, min(miolo_a, MAX_DUMP)))
        out.extend(dump_regiao("variante (inicio do miolo)", b, p, min(miolo_b, MAX_DUMP)))
        out.append("```")
        out.append("")
    return out


def comparar_cdr(base: Path, variante: Path) -> str:
    """Compara dois .cdr ZCF e devolve um relatorio Markdown completo."""
    ma = ler_membros(base)
    mb = ler_membros(variante)

    so_base = sorted(set(ma) - set(mb))
    so_variante = sorted(set(mb) - set(ma))
    comuns = sorted(set(ma) & set(mb))
    identicos = [n for n in comuns if ma[n] == mb[n]]
    alterados = [n for n in comuns if ma[n] != mb[n]]

    out = [
        f"# Diff ZCF: `{base.name}` vs `{variante.name}`",
        "",
        "## Resumo",
        "",
        "| Situacao | Membros |",
        "|---|---|",
        f"| So no base | {', '.join(f'`{n}`' for n in so_base) or '—'} |",
        f"| So na variante | {', '.join(f'`{n}`' for n in so_variante) or '—'} |",
        f"| Identicos | {', '.join(f'`{n}`' for n in identicos) or '—'} |",
        f"| Alterados | {', '.join(f'`{n}`' for n in alterados) or '—'} |",
        "",
    ]

    for nome in so_variante:
        out.append(f"### `{nome}` — NOVO na variante ({len(mb[nome])} bytes)")
        out.append("```")
        out.append(hexdump(mb[nome][:64]))
        out.append("```")
        out.append("")
    for nome in so_base:
        out.append(f"### `{nome}` — REMOVIDO na variante (tinha {len(ma[nome])} bytes)")
        out.append("")
    for nome in alterados:
        out.extend(comparar_membro(nome, ma[nome], mb[nome]))

    return "\n".join(out)


def modo_all(pasta: Path, saida: Path) -> None:
    saida.mkdir(parents=True, exist_ok=True)
    manifestos = sorted(pasta.glob("caso_*.json"))
    if not manifestos:
        sys.exit(f"Nenhum manifesto caso_*.json encontrado em {pasta}")
    for mf in manifestos:
        info = json.loads(mf.read_text(encoding="utf-8", errors="replace"))
        arq_base = info.get("arquivo_base", "")
        if not arq_base:
            continue  # o proprio caso base nao tem par de comparacao
        base = pasta / arq_base
        variante = pasta / info["arquivo"]
        if not base.exists() or not variante.exists():
            print(f"AVISO: par ausente para {info['caso']}, pulando", file=sys.stderr)
            continue
        rel = comparar_cdr(base, variante)
        destino = saida / f"diff_{info['caso']}.md"
        destino.write_text(rel + "\n", encoding="utf-8")
        print(f"gerado: {destino}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("arquivos", nargs="*", help="base.cdr variante.cdr")
    ap.add_argument("--all", metavar="PASTA", help="compara todos os pares descritos nos manifestos da pasta")
    ap.add_argument("-o", "--saida", help="arquivo (modo par) ou pasta (modo --all) de saida")
    args = ap.parse_args()

    if args.all:
        modo_all(Path(args.all), Path(args.saida or "relatorios"))
    elif len(args.arquivos) == 2:
        rel = comparar_cdr(Path(args.arquivos[0]), Path(args.arquivos[1]))
        if args.saida:
            Path(args.saida).write_text(rel + "\n", encoding="utf-8")
            print(f"gerado: {args.saida}")
        else:
            print(rel)
    else:
        ap.error("informe base.cdr e variante.cdr, ou use --all PASTA")


if __name__ == "__main__":
    main()
