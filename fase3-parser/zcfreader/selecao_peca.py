"""Escolha da peça correta na página, usada na janela de correção.

O operador clica na peça que deveria ter sido reconhecida. Como o catálogo já
conhece todas as peças do CDR, o clique vira uma informação precisa (ID e
medida exata), e não apenas um print. Clicar de novo no mesmo ponto alterna
entre as peças sobrepostas, da menor para a maior. Arrastar desenha uma região
quando a peça certa não existe no catálogo: as peças do arquivo que couberem na
região são unidas e a medida vem delas, exata; só sem nenhuma peça dentro vale a
medida aproximada do retângulo desenhado.
"""
from __future__ import annotations

from io import BytesIO

TOLERANCIA_CLIQUE_PX = 6
ARRASTO_MINIMO_PX = 8


def cm_do_px(fatos: dict, tamanho: tuple[int, int], x_px: float, y_px: float) -> tuple[float, float]:
    lim = fatos["limites_cm"]
    return (
        lim["esquerda"] + x_px / tamanho[0] * (lim["direita"] - lim["esquerda"]),
        lim["topo"] - y_px / tamanho[1] * (lim["topo"] - lim["base"]),
    )


def px_do_cm(fatos: dict, tamanho: tuple[int, int], caixa_cm: dict) -> tuple[float, float, float, float]:
    lim = fatos["limites_cm"]
    largura = (lim["direita"] - lim["esquerda"]) or 1
    altura = (lim["topo"] - lim["base"]) or 1
    return (
        (caixa_cm["esquerda"] - lim["esquerda"]) / largura * tamanho[0],
        (lim["topo"] - caixa_cm["topo"]) / altura * tamanho[1],
        (caixa_cm["direita"] - lim["esquerda"]) / largura * tamanho[0],
        (lim["topo"] - caixa_cm["base"]) / altura * tamanho[1],
    )


def candidatos_no_ponto(fatos: dict, x_cm: float, y_cm: float, folga_cm: float = 0.0) -> list[str]:
    """IDs das peças que contêm o ponto, da menor para a maior área."""
    encontrados = []
    for candidato_id, candidato in fatos.get("candidatos", {}).items():
        caixa = candidato.get("caixa_cm")
        if not caixa:
            continue
        if (caixa["esquerda"] - folga_cm <= x_cm <= caixa["direita"] + folga_cm
                and caixa["base"] - folga_cm <= y_cm <= caixa["topo"] + folga_cm):
            area = (caixa["direita"] - caixa["esquerda"]) * (caixa["topo"] - caixa["base"])
            encontrados.append((area, candidato_id))
    return [candidato_id for _, candidato_id in sorted(encontrados)]


def selecao_de_candidato(fatos: dict, candidato_id: str) -> dict:
    candidato = fatos["candidatos"][candidato_id]
    return {
        "origem": "peca_do_catalogo", "id": candidato_id,
        "largura_cm": round(float(candidato["largura_cm"]), 3),
        "altura_cm": round(float(candidato["altura_cm"]), 3),
        "ocorrencias_desenhadas": int(candidato.get("quantidade_geometrica") or 1),
        "caixa_cm": dict(candidato["caixa_cm"]),
    }


def pecas_na_regiao(fatos: dict, caixa_cm: dict, folga_cm: float = 0.3) -> list[str]:
    """Peças inteiramente dentro da região, sem as que estão dentro de outra da lista."""
    dentro = []
    for candidato_id, candidato in fatos.get("candidatos", {}).items():
        c = candidato.get("caixa_cm")
        if c and (c["esquerda"] >= caixa_cm["esquerda"] - folga_cm and c["direita"] <= caixa_cm["direita"] + folga_cm
                  and c["base"] >= caixa_cm["base"] - folga_cm and c["topo"] <= caixa_cm["topo"] + folga_cm):
            dentro.append(candidato_id)

    def contida(a: str, b: str) -> bool:
        ca, cb = fatos["candidatos"][a]["caixa_cm"], fatos["candidatos"][b]["caixa_cm"]
        return (a != b and ca["esquerda"] >= cb["esquerda"] - 0.01 and ca["direita"] <= cb["direita"] + 0.01
                and ca["base"] >= cb["base"] - 0.01 and ca["topo"] <= cb["topo"] + 0.01)

    externas = [a for a in dentro if not any(contida(a, b) for b in dentro)]
    # Duas peças com a mesma caixa (ex.: arte e contorno) contam uma vez só.
    unicas, caixas_vistas = [], set()
    for candidato_id in sorted(externas):
        c = fatos["candidatos"][candidato_id]["caixa_cm"]
        assinatura = tuple(round(c[k], 2) for k in ("esquerda", "direita", "base", "topo"))
        if assinatura not in caixas_vistas:
            caixas_vistas.add(assinatura)
            unicas.append(candidato_id)
    return unicas


def selecao_de_uniao(fatos: dict, ids: list[str]) -> dict:
    """Uma peça formada pela união exata de peças do arquivo."""
    if len(ids) == 1:
        return selecao_de_candidato(fatos, ids[0])
    caixas = [fatos["candidatos"][i]["caixa_cm"] for i in ids]
    caixa = {
        "esquerda": min(c["esquerda"] for c in caixas), "direita": max(c["direita"] for c in caixas),
        "base": min(c["base"] for c in caixas), "topo": max(c["topo"] for c in caixas),
    }
    return {
        "origem": "uniao_de_pecas", "id": "+".join(ids), "ids": list(ids),
        "largura_cm": round(caixa["direita"] - caixa["esquerda"], 3),
        "altura_cm": round(caixa["topo"] - caixa["base"], 3),
        "ocorrencias_desenhadas": 1, "caixa_cm": caixa,
    }


def selecao_de_regiao(fatos: dict, tamanho: tuple[int, int], x0: float, y0: float, x1: float, y1: float) -> dict:
    """Região desenhada pelo operador, convertida para centímetros do CDR."""
    esquerda, topo = cm_do_px(fatos, tamanho, min(x0, x1), min(y0, y1))
    direita, base = cm_do_px(fatos, tamanho, max(x0, x1), max(y0, y1))
    return {
        "origem": "regiao_desenhada", "id": None,
        "largura_cm": round(direita - esquerda, 2), "altura_cm": round(topo - base, 2),
        "ocorrencias_desenhadas": 1,
        "caixa_cm": {"esquerda": esquerda, "direita": direita, "base": base, "topo": topo},
    }


def aplicar_selecao_ao_item(item: dict, selecao: dict) -> dict:
    """Troca a peça do item pela escolhida, preservando quantidade, material e acabamento."""
    novo = dict(item)
    novo["dimensoes"] = {
        "largura_mm": selecao["largura_cm"] * 10, "altura_mm": selecao["altura_cm"] * 10,
        "tipo": "peca_indicada_pelo_operador", "fonte": "correcao_operador", "confianca": 1.0,
    }
    novo["candidatos"] = list(selecao.get("ids") or ([selecao["id"]] if selecao.get("id") else []))
    novo["caixa_cm"] = dict(selecao["caixa_cm"])
    novo["peca_correta"] = {
        chave: selecao[chave] for chave in ("origem", "id", "largura_cm", "altura_cm", "ocorrencias_desenhadas")
    }
    if item.get("candidatos") or item.get("dimensoes"):
        dim = item.get("dimensoes") or {}
        novo["peca_correta"]["antes"] = {
            "ids": list(item.get("candidatos") or []),
            "largura_cm": round((dim.get("largura_mm") or 0) / 10, 3),
            "altura_cm": round((dim.get("altura_mm") or 0) / 10, 3),
        }
    return novo


def abrir_janela_selecao(pai, fatos: dict, ao_escolher, pode_substituir: bool) -> None:
    """Janela com a página inteira; ``ao_escolher(selecao, substituir)`` recebe a escolha."""
    import tkinter as tk
    from tkinter import ttk

    from PIL import Image, ImageTk

    with Image.open(BytesIO(fatos["imagem"])) as original:
        original.load()
        pagina = original.convert("RGB")
    largura_tela = pai.winfo_screenwidth()
    altura_tela = pai.winfo_screenheight()
    escala = min((largura_tela - 80) / pagina.size[0], (altura_tela - 260) / pagina.size[1], 1.0)
    exibida = pagina.resize((max(1, round(pagina.size[0] * escala)), max(1, round(pagina.size[1] * escala))))
    tamanho = exibida.size

    janela = tk.Toplevel(pai)
    janela.title("Escolher a peça certa")
    janela.transient(pai)
    janela.grab_set()
    corpo = ttk.Frame(janela, padding=14)
    corpo.pack(fill="both", expand=True)
    ttk.Label(
        corpo,
        text=(
            "Clique na peça que deveria ter sido reconhecida; clique de novo no mesmo lugar para alternar entre "
            "peças sobrepostas. Para uma peça formada por várias partes, arraste em volta delas: a medida vem "
            "das peças do arquivo que ficarem dentro, sem precisar acertar a borda."
        ),
        style="Subtitulo.TLabel", wraplength=max(420, tamanho[0]), justify="left",
    ).pack(anchor="w", pady=(0, 8))
    tela = tk.Canvas(corpo, width=tamanho[0], height=tamanho[1], highlightthickness=1, highlightbackground="#cbd5e1")
    tela.pack()
    foto = ImageTk.PhotoImage(exibida)
    tela.create_image(0, 0, image=foto, anchor="nw")
    tela.imagem = foto  # mantém a referência viva enquanto a janela existir
    var_info = tk.StringVar(value="Nenhuma peça escolhida.")
    ttk.Label(corpo, textvariable=var_info, style="Subtitulo.TLabel", font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(8, 8))

    estado = {"selecao": None, "ultimo_ponto": None, "opcoes": [], "posicao": 0, "inicio": None, "marcas": [], "retangulo": None}

    def limpar_marcas() -> None:
        for marca in estado["marcas"]:
            tela.delete(marca)
        estado["marcas"] = []

    def destacar(selecao: dict) -> None:
        limpar_marcas()
        x0, y0, x1, y1 = px_do_cm(fatos, tamanho, selecao["caixa_cm"])
        estado["marcas"].append(tela.create_rectangle(x0, y0, x1, y1, outline="#e11d48", width=3))
        rotulo = f"{selecao['id'] or 'região'} — {selecao['largura_cm']:g} × {selecao['altura_cm']:g} cm"
        fundo = tela.create_rectangle(x0, max(0, y0 - 22), x0 + 9 * len(rotulo), max(22, y0), fill="#e11d48", outline="")
        estado["marcas"] += [fundo, tela.create_text(x0 + 4, max(11, y0 - 11), text=rotulo, anchor="w", fill="white")]
        estado["selecao"] = selecao
        botao_usar.configure(state="normal" if pode_substituir else "disabled")
        botao_adicionar.configure(state="normal")

    def pressionar(evento) -> None:
        estado["inicio"] = (evento.x, evento.y)

    def arrastar(evento) -> None:
        inicio = estado["inicio"]
        if inicio is None:
            return
        if estado["retangulo"] is None:
            estado["retangulo"] = tela.create_rectangle(*inicio, evento.x, evento.y, outline="#2563eb", dash=(4, 2), width=2)
        else:
            tela.coords(estado["retangulo"], *inicio, evento.x, evento.y)

    def soltar(evento) -> None:
        inicio = estado["inicio"] or (evento.x, evento.y)
        if abs(evento.x - inicio[0]) >= ARRASTO_MINIMO_PX and abs(evento.y - inicio[1]) >= ARRASTO_MINIMO_PX:
            regiao = selecao_de_regiao(fatos, tamanho, inicio[0], inicio[1], evento.x, evento.y)
            pecas = pecas_na_regiao(fatos, regiao["caixa_cm"])
            if pecas:
                selecao = selecao_de_uniao(fatos, pecas)
                destacar(selecao)
                var_info.set(
                    f"{len(pecas)} peça(s) do arquivo dentro da região ({', '.join(pecas[:6])}{'…' if len(pecas) > 6 else ''}): "
                    f"{selecao['largura_cm']:g} × {selecao['altura_cm']:g} cm, medida exata do arquivo."
                )
            else:
                destacar(regiao)
                var_info.set(
                    f"Nenhuma peça do arquivo cabe inteira na região: {regiao['largura_cm']:g} × {regiao['altura_cm']:g} cm "
                    "(medida aproximada; confira no formulário)."
                )
            if estado["retangulo"] is not None:
                tela.delete(estado["retangulo"])
                estado["retangulo"] = None
            estado["ultimo_ponto"] = None
            return
        mesmo_ponto = estado["ultimo_ponto"] is not None and all(
            abs(a - b) <= TOLERANCIA_CLIQUE_PX for a, b in zip(estado["ultimo_ponto"], (evento.x, evento.y))
        )
        if mesmo_ponto and estado["opcoes"]:
            estado["posicao"] = (estado["posicao"] + 1) % len(estado["opcoes"])
        else:
            x_cm, y_cm = cm_do_px(fatos, tamanho, evento.x, evento.y)
            estado["opcoes"] = candidatos_no_ponto(fatos, x_cm, y_cm)
            estado["posicao"] = 0
            estado["ultimo_ponto"] = (evento.x, evento.y)
        if not estado["opcoes"]:
            limpar_marcas()
            estado["selecao"] = None
            var_info.set("Nenhuma peça do arquivo neste ponto. Arraste para desenhar a região.")
            return
        selecao = selecao_de_candidato(fatos, estado["opcoes"][estado["posicao"]])
        destacar(selecao)
        total = len(estado["opcoes"])
        var_info.set(
            f"{selecao['id']}: {selecao['largura_cm']:g} × {selecao['altura_cm']:g} cm"
            + (f", {selecao['ocorrencias_desenhadas']} ocorrências desenhadas" if selecao["ocorrencias_desenhadas"] > 1 else "")
            + (f"  •  peça {estado['posicao'] + 1} de {total} neste ponto (clique de novo para alternar)" if total > 1 else "")
        )

    def escolher(substituir: bool) -> None:
        if estado["selecao"] is None:
            return
        selecao = estado["selecao"]
        janela.destroy()
        ao_escolher(selecao, substituir)

    tela.bind("<ButtonPress-1>", pressionar)
    tela.bind("<B1-Motion>", arrastar)
    tela.bind("<ButtonRelease-1>", soltar)
    botoes = ttk.Frame(corpo)
    botoes.pack(fill="x")
    ttk.Button(botoes, text="Cancelar", command=janela.destroy).pack(side="right")
    botao_adicionar = ttk.Button(botoes, text="Adicionar como novo item", state="disabled", command=lambda: escolher(False))
    botao_adicionar.pack(side="right", padx=6)
    botao_usar = ttk.Button(
        botoes, text="Usar para o item selecionado", style="Primary.TButton", state="disabled",
        command=lambda: escolher(True),
    )
    botao_usar.pack(side="right")
