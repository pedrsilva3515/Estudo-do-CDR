"""Interface gráfica simples para analisar pedidos em arquivos CDR."""
from __future__ import annotations

import json
from pathlib import Path
from queue import Empty, Queue
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .pedido import interpretar_pedido

try:
    from tkinterdnd2 import DND_FILES, TkinterDnD
except ImportError:  # A interface continua utilizável pelo botão Procurar.
    DND_FILES = None
    TkinterDnD = None


COR_FUNDO = "#eef2f7"
COR_TEXTO = "#172033"
COR_SECUNDARIA = "#5f6b7a"
COR_AZUL = "#246bfd"
COR_AZUL_ESCURO = "#1554c0"
COR_BORDA = "#cbd5e1"
COR_SUCESSO = "#087f5b"


def _numero(valor: float) -> str:
    return f"{valor:.2f}".rstrip("0").rstrip(",").rstrip(".")


class AplicacaoPedido:
    def __init__(self, raiz: tk.Tk):
        self.raiz = raiz
        self.raiz.title("Leitor de pedidos CDR")
        self.raiz.geometry("980x680")
        self.raiz.minsize(820, 580)
        self.raiz.configure(bg=COR_FUNDO)
        self.resultado: dict | None = None
        self.arquivo: Path | None = None
        self.fila: Queue = Queue()
        self._configurar_estilos()
        self._montar_interface()

    def _configurar_estilos(self) -> None:
        estilo = ttk.Style(self.raiz)
        estilo.theme_use("clam")
        estilo.configure("TFrame", background=COR_FUNDO)
        estilo.configure("Card.TFrame", background="white")
        estilo.configure("Titulo.TLabel", background=COR_FUNDO, foreground=COR_TEXTO, font=("Segoe UI", 20, "bold"))
        estilo.configure("Subtitulo.TLabel", background=COR_FUNDO, foreground=COR_SECUNDARIA, font=("Segoe UI", 10))
        estilo.configure("Card.TLabel", background="white", foreground=COR_TEXTO, font=("Segoe UI", 10))
        estilo.configure("Total.TLabel", background="white", foreground=COR_SUCESSO, font=("Segoe UI", 18, "bold"))
        estilo.configure("Primary.TButton", font=("Segoe UI", 10, "bold"), foreground="white", background=COR_AZUL, padding=(16, 9))
        estilo.map("Primary.TButton", background=[("active", COR_AZUL_ESCURO), ("disabled", "#94a3b8")])
        estilo.configure("Secondary.TButton", font=("Segoe UI", 10), padding=(14, 8))
        estilo.configure("Treeview", font=("Segoe UI", 10), rowheight=31, background="white", fieldbackground="white", borderwidth=0)
        estilo.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background="#e8eef7", foreground=COR_TEXTO, padding=(8, 8))
        estilo.map("Treeview", background=[("selected", "#dbeafe")], foreground=[("selected", COR_TEXTO)])

    def _montar_interface(self) -> None:
        cabecalho = ttk.Frame(self.raiz, padding=(28, 22, 28, 12))
        cabecalho.pack(fill="x")
        ttk.Label(cabecalho, text="Leitor de pedidos CDR", style="Titulo.TLabel").pack(anchor="w")
        ttk.Label(
            cabecalho,
            text="Arraste o arquivo do cliente, confira os itens encontrados e exporte o resultado.",
            style="Subtitulo.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        conteudo = ttk.Frame(self.raiz, padding=(28, 0, 28, 24))
        conteudo.pack(fill="both", expand=True)

        self.drop = tk.Frame(conteudo, bg="white", highlightbackground=COR_BORDA, highlightthickness=2, cursor="hand2")
        self.drop.pack(fill="x", pady=(0, 14))
        self.drop_texto = tk.Label(
            self.drop,
            text="Solte um arquivo .CDR aqui",
            bg="white", fg=COR_TEXTO, font=("Segoe UI", 14, "bold"), pady=20,
        )
        self.drop_texto.pack()
        tk.Label(
            self.drop, text="ou use o botão abaixo", bg="white", fg=COR_SECUNDARIA,
            font=("Segoe UI", 9), pady=0,
        ).pack()
        self.botao_procurar = ttk.Button(self.drop, text="Procurar arquivo", style="Primary.TButton", command=self.procurar)
        self.botao_procurar.pack(pady=(10, 20))
        self.drop.bind("<Button-1>", lambda _e: self.procurar())
        self.drop_texto.bind("<Button-1>", lambda _e: self.procurar())
        if DND_FILES is not None and hasattr(self.drop, "drop_target_register"):
            self.drop.drop_target_register(DND_FILES)
            self.drop.dnd_bind("<<Drop>>", self._arquivo_solto)

        resumo = ttk.Frame(conteudo, style="Card.TFrame", padding=16)
        resumo.pack(fill="x", pady=(0, 14))
        resumo.columnconfigure(0, weight=1)
        self.rotulo_arquivo = ttk.Label(resumo, text="Nenhum arquivo analisado", style="Card.TLabel", font=("Segoe UI", 11, "bold"))
        self.rotulo_arquivo.grid(row=0, column=0, sticky="w")
        self.rotulo_total = ttk.Label(resumo, text="0 unidades", style="Total.TLabel")
        self.rotulo_total.grid(row=0, column=1, rowspan=2, sticky="e", padx=(20, 0))
        self.rotulo_status = ttk.Label(resumo, text="Aguardando arquivo", style="Card.TLabel", foreground=COR_SECUNDARIA)
        self.rotulo_status.grid(row=1, column=0, sticky="w", pady=(5, 0))
        self.progresso = ttk.Progressbar(resumo, mode="indeterminate", length=160)

        tabela_card = ttk.Frame(conteudo, style="Card.TFrame", padding=1)
        tabela_card.pack(fill="both", expand=True)
        colunas = ("item", "quantidade", "tamanho", "material", "acabamento", "confianca")
        self.tabela = ttk.Treeview(tabela_card, columns=colunas, show="headings")
        titulos = {
            "item": "Item", "quantidade": "Quantidade", "tamanho": "Tamanho (cm)",
            "material": "Material", "acabamento": "Acabamento", "confianca": "Confiança",
        }
        larguras = {"item": 55, "quantidade": 95, "tamanho": 140, "material": 210, "acabamento": 145, "confianca": 100}
        for coluna in colunas:
            self.tabela.heading(coluna, text=titulos[coluna])
            self.tabela.column(coluna, width=larguras[coluna], anchor="center" if coluna != "material" else "w")
        barra = ttk.Scrollbar(tabela_card, orient="vertical", command=self.tabela.yview)
        self.tabela.configure(yscrollcommand=barra.set)
        self.tabela.pack(side="left", fill="both", expand=True)
        barra.pack(side="right", fill="y")

        rodape = ttk.Frame(conteudo, padding=(0, 14, 0, 0))
        rodape.pack(fill="x")
        self.rotulo_alertas = ttk.Label(rodape, text="", style="Subtitulo.TLabel")
        self.rotulo_alertas.pack(side="left", fill="x", expand=True)
        self.botao_exportar = ttk.Button(rodape, text="Exportar JSON", style="Secondary.TButton", command=self.exportar, state="disabled")
        self.botao_exportar.pack(side="right")

    def procurar(self) -> None:
        caminho = filedialog.askopenfilename(title="Escolha o pedido", filetypes=[("CorelDRAW", "*.cdr"), ("Todos os arquivos", "*.*")])
        if caminho:
            self.analisar(Path(caminho))

    def _arquivo_solto(self, evento) -> None:
        caminhos = self.raiz.tk.splitlist(evento.data)
        if caminhos:
            self.analisar(Path(caminhos[0]))

    def analisar(self, caminho: Path) -> None:
        if caminho.suffix.casefold() != ".cdr":
            messagebox.showwarning("Arquivo inválido", "Escolha um arquivo com extensão .cdr.")
            return
        if not caminho.is_file():
            messagebox.showerror("Arquivo não encontrado", f"Não foi possível abrir:\n{caminho}")
            return
        self.arquivo = caminho
        self.resultado = None
        self.botao_procurar.configure(state="disabled")
        self.botao_exportar.configure(state="disabled")
        self.rotulo_arquivo.configure(text=caminho.name)
        self.rotulo_status.configure(text="Analisando estrutura, textos, dimensões e imagens…", foreground=COR_AZUL)
        self.rotulo_total.configure(text="…")
        self.rotulo_alertas.configure(text="")
        for linha in self.tabela.get_children():
            self.tabela.delete(linha)
        self.progresso.grid(row=1, column=1, sticky="e", padx=(20, 0), pady=(8, 0))
        self.progresso.start(12)
        threading.Thread(target=self._executar_analise, args=(caminho,), daemon=True).start()
        self.raiz.after(100, self._consultar_fila)

    def _executar_analise(self, caminho: Path) -> None:
        try:
            self.fila.put(("ok", interpretar_pedido(caminho)))
        except Exception as erro:  # erro é apresentado ao operador de forma legível
            self.fila.put(("erro", erro))

    def _consultar_fila(self) -> None:
        try:
            estado, conteudo = self.fila.get_nowait()
        except Empty:
            self.raiz.after(100, self._consultar_fila)
            return
        self.progresso.stop()
        self.progresso.grid_forget()
        self.botao_procurar.configure(state="normal")
        if estado == "erro":
            self.rotulo_status.configure(text="Não foi possível analisar o arquivo", foreground="#b42318")
            self.rotulo_total.configure(text="0 unidades")
            messagebox.showerror("Falha na análise", str(conteudo))
            return
        self._mostrar_resultado(conteudo)

    def _mostrar_resultado(self, resultado: dict) -> None:
        self.resultado = resultado
        itens = resultado.get("itens", [])
        for item in itens:
            dimensoes = item.get("dimensoes") or {}
            largura = (dimensoes.get("largura_mm") or 0) / 10
            altura = (dimensoes.get("altura_mm") or 0) / 10
            material = item.get("material", {})
            acabamento = item.get("acabamento", {})
            confiancas = [item.get("quantidade", {}).get("confianca", 0), dimensoes.get("confianca", 0)]
            if material.get("valor"):
                confiancas.append(material.get("confianca", 0))
            confianca = min(confiancas) if confiancas else 0
            self.tabela.insert("", "end", values=(
                item.get("indice", ""), item.get("quantidade", {}).get("valor", "?"),
                f"{_numero(largura)} × {_numero(altura)}",
                material.get("valor") or "Confirmar", acabamento.get("valor") or "Confirmar",
                f"{confianca * 100:.0f}%",
            ))
        total = resultado.get("total_unidades", 0)
        self.rotulo_total.configure(text=f"{total} unidade{'s' if total != 1 else ''}")
        modo = resultado.get("modo_cor", {}).get("documento") or "não identificado"
        pendencias = resultado.get("pendencias", [])
        self.rotulo_status.configure(
            text=f"{len(itens)} item(ns) • modo de cor {modo} • " + ("revisão necessária" if pendencias else "análise concluída"),
            foreground=COR_SUCESSO if not pendencias else "#9a6700",
        )
        alertas = len(resultado.get("alertas", []))
        detalhes = []
        if alertas:
            detalhes.append(f"{alertas} alerta(s)")
        if pendencias:
            detalhes.append("Confirmar: " + ", ".join(pendencias))
        self.rotulo_alertas.configure(text=" • ".join(detalhes) or "Nenhuma pendência detectada")
        self.botao_exportar.configure(state="normal")

    def exportar(self) -> None:
        if self.resultado is None or self.arquivo is None:
            return
        destino = filedialog.asksaveasfilename(
            title="Salvar resultado", defaultextension=".json",
            initialfile=f"{self.arquivo.stem}-pedido.json", filetypes=[("JSON", "*.json")],
        )
        if not destino:
            return
        Path(destino).write_text(json.dumps(self.resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        messagebox.showinfo("Resultado exportado", f"Arquivo salvo em:\n{destino}")


def main() -> None:
    raiz = TkinterDnD.Tk() if TkinterDnD is not None else tk.Tk()
    AplicacaoPedido(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    main()
