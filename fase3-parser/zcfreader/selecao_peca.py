"""Escolha da peça correta na página, usada na janela de correção.

O operador clica na peça que deveria ter sido reconhecida. Como o catálogo já
conhece todas as peças do CDR, o clique vira uma informação precisa (ID e
medida exata), e não apenas um print. Clicar de novo no mesmo ponto alterna
entre as peças sobrepostas, da menor para a maior. Arrastar desenha uma região
quando a peça certa não existe no catálogo.
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
    novo["candidatos"] = [selecao["id"]] if selecao.get("id") else []
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
    escala = min(1000 / pagina.size[0], 640 / pagina.size[1], 1.0)
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
            "Clique na peça que deveria ter sido reconhecida. Clique de novo no mesmo lugar para alternar "
            "entre peças sobrepostas (conteúdo e máscara, arte e moldura). Arraste para desenhar uma região."
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

    estado = {"selecao": None, "ultimo_ponto": None, "opcoes": [], "posicao": 0, "inicio": None, "marcas": []}

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

    def soltar(evento) -> None:
        inicio = estado["inicio"] or (evento.x, evento.y)
        if abs(evento.x - inicio[0]) >= ARRASTO_MINIMO_PX and abs(evento.y - inicio[1]) >= ARRASTO_MINIMO_PX:
            selecao = selecao_de_regiao(fatos, tamanho, inicio[0], inicio[1], evento.x, evento.y)
            destacar(selecao)
            var_info.set(f"Região desenhada: {selecao['largura_cm']:g} × {selecao['altura_cm']:g} cm (medida aproximada).")
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
