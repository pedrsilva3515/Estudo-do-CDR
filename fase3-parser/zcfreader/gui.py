"""Interface gráfica simples para analisar pedidos em arquivos CDR."""
from __future__ import annotations

from copy import deepcopy
import json
import os
from pathlib import Path
from queue import Empty, Queue
import threading
from time import perf_counter
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from .configuracao import (
    MODELOS_OPENAI,
    carregar_configuracao,
    obter_chave_openai,
    salvar_chave_openai,
    salvar_configuracao,
)
from .pedido import interpretar_pedido
from .relatorios import gerar_pacote_diagnostico, normalizar_resultado_corrigido
from .modelos_locais import (
    NOME_MODELO,
    TAMANHO_TOTAL_MODELOS,
    analisar_com_modelo_local,
    instalar_modelo,
    modelo_instalado,
)
from .visao_api import analisar_com_openai, mesclar_analise_visual

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
        self.raiz.geometry("1020x740")
        self.raiz.minsize(880, 640)
        self.raiz.configure(bg=COR_FUNDO)
        self.resultado: dict | None = None
        self.resultado_original: dict | None = None
        self.resultado_estrutural: dict | None = None
        self.analise_visual: dict | None = None
        self.duracao_analise = 0.0
        self.arquivo: Path | None = None
        self.configuracao = carregar_configuracao()
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
        ttk.Button(cabecalho, text="Configurar IA", style="Secondary.TButton", command=self.configurar_ia).place(relx=1, x=0, y=8, anchor="ne")

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
        self.rotulo_alertas.pack(fill="x", pady=(0, 8))
        acoes = ttk.Frame(rodape)
        acoes.pack(fill="x")
        self.var_incluir_cdr = tk.BooleanVar(value=False)
        ttk.Checkbutton(acoes, text="Incluir CDR no pacote de diagnóstico", variable=self.var_incluir_cdr).pack(side="left")
        self.botao_exportar = ttk.Button(acoes, text="Exportar JSON", style="Secondary.TButton", command=self.exportar, state="disabled")
        self.botao_exportar.pack(side="right")
        self.botao_corrigir = ttk.Button(
            acoes, text="Corrigir resultado", style="Secondary.TButton",
            command=self.corrigir_resultado, state="disabled",
        )
        self.botao_corrigir.pack(side="right", padx=(0, 8))
        self.botao_confirmar = ttk.Button(
            acoes, text="Confirmar correto", style="Primary.TButton",
            command=self.confirmar_resultado, state="disabled",
        )
        self.botao_confirmar.pack(side="right", padx=(0, 8))

    def procurar(self) -> None:
        caminho = filedialog.askopenfilename(title="Escolha o pedido", filetypes=[("CorelDRAW", "*.cdr"), ("Todos os arquivos", "*.*")])
        if caminho:
            self.analisar(Path(caminho))

    def configurar_ia(self) -> None:
        janela = tk.Toplevel(self.raiz)
        janela.title("Configurar processamento")
        janela.geometry("540x600")
        janela.resizable(False, False)
        janela.configure(bg=COR_FUNDO)
        janela.transient(self.raiz)
        janela.grab_set()
        corpo = ttk.Frame(janela, padding=24)
        corpo.pack(fill="both", expand=True)
        ttk.Label(corpo, text="Processamento visual", style="Titulo.TLabel", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        ttk.Label(corpo, text="O modelo local roda na CPU e nunca envia o pedido para a internet.", style="Subtitulo.TLabel").pack(anchor="w", pady=(4, 14))

        modelo_card = ttk.Frame(corpo, style="Card.TFrame", padding=12)
        modelo_card.pack(fill="x", pady=(0, 14))
        ttk.Label(modelo_card, text=NOME_MODELO, style="Card.TLabel", font=("Segoe UI", 10, "bold")).pack(anchor="w")
        var_status_modelo = tk.StringVar()
        rotulo_modelo = ttk.Label(modelo_card, textvariable=var_status_modelo, style="Card.TLabel", foreground=COR_SECUNDARIA)
        rotulo_modelo.pack(anchor="w", pady=(3, 8))
        progresso_download = ttk.Progressbar(modelo_card, mode="determinate", maximum=100)
        fila_download: Queue = Queue()

        def atualizar_status_modelo() -> None:
            if modelo_instalado():
                var_status_modelo.set("Instalado e pronto para uso em CPU")
                botao_download.configure(text="Modelo instalado", state="disabled")
            else:
                tamanho_gb = TAMANHO_TOTAL_MODELOS / 1_000_000_000
                var_status_modelo.set(f"Não instalado • download de {tamanho_gb:.2f} GB + runtime")
                botao_download.configure(text="Baixar modelo local", state="normal")

        def baixar_modelo() -> None:
            botao_download.configure(state="disabled", text="Baixando…")
            progresso_download.pack(fill="x", pady=(0, 7))

            def progresso(etapa: str, atual: int, total: int) -> None:
                fila_download.put(("progresso", etapa, atual, total))

            def tarefa() -> None:
                try:
                    instalar_modelo(progresso)
                    fila_download.put(("ok",))
                except Exception as erro:
                    fila_download.put(("erro", erro))

            threading.Thread(target=tarefa, daemon=True).start()
            consultar_download()

        def consultar_download() -> None:
            finalizou = False
            try:
                while True:
                    evento = fila_download.get_nowait()
                    if evento[0] == "progresso":
                        _, etapa, atual, total = evento
                        percentual = (atual / total * 100) if total else 0
                        progresso_download.configure(value=percentual)
                        var_status_modelo.set(
                            f"{etapa}: {atual / 1_000_000:.0f} de {total / 1_000_000:.0f} MB ({percentual:.0f}%)"
                        )
                    elif evento[0] == "ok":
                        finalizou = True
                        progresso_download.pack_forget()
                        var_modo.set("Modelo visual local (CPU)")
                        self.configuracao = {
                            "modo": "local", "provedor": "openai",
                            "modelo": var_modelo.get() or MODELOS_OPENAI[0],
                        }
                        salvar_configuracao(self.configuracao)
                        atualizar_status_modelo()
                        messagebox.showinfo(
                            "Modelo pronto",
                            "O modelo local foi instalado, ativado e já pode ser usado.",
                            parent=janela,
                        )
                    else:
                        finalizou = True
                        progresso_download.pack_forget()
                        atualizar_status_modelo()
                        messagebox.showerror("Falha no download", str(evento[1]), parent=janela)
            except Empty:
                pass
            if not finalizou and str(botao_download["state"]) == "disabled":
                janela.after(150, consultar_download)

        botao_download = ttk.Button(modelo_card, style="Secondary.TButton", command=baixar_modelo)
        botao_download.pack(anchor="w")
        atualizar_status_modelo()

        modos = {
            "Somente estrutural (rápido)": "estrutural",
            "Modelo visual local (CPU)": "local",
            "Automático (local e API como reserva)": "automatico",
            "Sempre usar API": "api",
        }
        inverso = {valor: rotulo for rotulo, valor in modos.items()}
        ttk.Label(corpo, text="Modo", style="Subtitulo.TLabel").pack(anchor="w")
        var_modo = tk.StringVar(value=inverso.get(self.configuracao.get("modo"), next(iter(modos))))
        combo_modo = ttk.Combobox(corpo, textvariable=var_modo, values=list(modos), state="readonly")
        combo_modo.pack(fill="x", pady=(4, 12))

        ttk.Label(corpo, text="Modelo OpenAI", style="Subtitulo.TLabel").pack(anchor="w")
        var_modelo = tk.StringVar(value=self.configuracao.get("modelo", MODELOS_OPENAI[0]))
        ttk.Combobox(corpo, textvariable=var_modelo, values=MODELOS_OPENAI, state="readonly").pack(fill="x", pady=(4, 12))

        ttk.Label(corpo, text="Chave da API", style="Subtitulo.TLabel").pack(anchor="w")
        chave_existente = obter_chave_openai()
        marcador = "••••••••••••" if chave_existente else ""
        var_chave = tk.StringVar(value=marcador)
        ttk.Entry(corpo, textvariable=var_chave, show="•").pack(fill="x", pady=(4, 8))
        ttk.Label(
            corpo,
            text="A chave é salva no Gerenciador de Credenciais do Windows. Ao usar API, o preview e o resultado estrutural são enviados à OpenAI e podem gerar cobrança.",
            style="Subtitulo.TLabel", wraplength=450, justify="left",
        ).pack(anchor="w", pady=(0, 14))

        def salvar() -> None:
            modo = modos[var_modo.get()]
            if modo == "local" and not modelo_instalado():
                messagebox.showwarning("Modelo necessário", "Baixe o modelo local antes de ativar este modo.", parent=janela)
                return
            if modo == "api" and not chave_existente and not var_chave.get().strip():
                messagebox.showwarning("Chave necessária", "Informe uma chave da API para ativar este modo.", parent=janela)
                return
            self.configuracao = {"modo": modo, "provedor": "openai", "modelo": var_modelo.get()}
            salvar_configuracao(self.configuracao)
            if var_chave.get() != marcador:
                salvar_chave_openai(var_chave.get())
            janela.destroy()

        ttk.Button(corpo, text="Salvar configuração", style="Primary.TButton", command=salvar).pack(anchor="e")

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
        self.resultado_original = None
        self.resultado_estrutural = None
        self.analise_visual = None
        self.botao_procurar.configure(state="disabled")
        self.botao_exportar.configure(state="disabled")
        self.botao_confirmar.configure(state="disabled")
        self.botao_corrigir.configure(state="disabled")
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
            inicio = perf_counter()
            estrutural = interpretar_pedido(caminho)
            resultado = deepcopy(estrutural)
            visual = None
            modo = self.configuracao.get("modo", "estrutural")
            pendente = bool(resultado.get("pendencias"))
            if modo == "local" or (modo == "automatico" and pendente and modelo_instalado()):
                visual = analisar_com_modelo_local(caminho, resultado)
                resultado = mesclar_analise_visual(resultado, visual, fonte="modelo_local")
                resultado["processamento"] = {"modo": modo, "provedor": "local", "modelo": NOME_MODELO}
            elif modo == "api" or (modo == "automatico" and pendente):
                chave = obter_chave_openai()
                if not chave:
                    raise RuntimeError(
                        "O modo automático encontrou pendências, mas não há modelo local nem chave de API. "
                        "Abra 'Configurar IA' para baixar o modelo ou informar uma chave."
                    )
                visual = analisar_com_openai(caminho, resultado, chave, self.configuracao["modelo"])
                resultado = mesclar_analise_visual(resultado, visual)
                resultado["processamento"] = {"modo": modo, "provedor": "openai", "modelo": self.configuracao["modelo"]}
            else:
                resultado["processamento"] = {"modo": "estrutural", "provedor": None, "modelo": None}
            self.fila.put(("ok", {
                "resultado": resultado, "estrutural": estrutural, "visual": visual,
                "duracao": perf_counter() - inicio,
            }))
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
        self.resultado_estrutural = conteudo["estrutural"]
        self.analise_visual = conteudo["visual"]
        self.duracao_analise = conteudo["duracao"]
        self.resultado_original = deepcopy(conteudo["resultado"])
        self._mostrar_resultado(conteudo["resultado"])

    def _mostrar_resultado(self, resultado: dict) -> None:
        self.resultado = resultado
        for linha in self.tabela.get_children():
            self.tabela.delete(linha)
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
        nome_usado = any(
            item.get(campo, {}).get("fonte") == "nome_arquivo"
            for item in itens for campo in ("quantidade", "material", "acabamento")
        )
        origem_nome = " • nome usado como evidência" if nome_usado else ""
        processamento = resultado.get("processamento", {})
        if processamento.get("provedor") == "local":
            origem_ia = " • IA local em CPU"
        elif processamento.get("provedor"):
            origem_ia = f" • IA: {processamento.get('modelo')}"
        else:
            origem_ia = " • análise estrutural"
        self.rotulo_status.configure(
            text=f"{len(itens)} item(ns) • modo de cor {modo}{origem_nome}{origem_ia} • "
            + ("revisão necessária" if pendencias else "análise concluída"),
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
        self.botao_confirmar.configure(state="normal")
        self.botao_corrigir.configure(state="normal")

    def _salvar_feedback(self, correto: dict, situacao: str, observacao: str = "") -> None:
        if self.arquivo is None or self.resultado_original is None:
            return
        try:
            destino = gerar_pacote_diagnostico(
                self.arquivo, self.resultado_original, correto,
                resultado_estrutural=self.resultado_estrutural,
                analise_visual=self.analise_visual,
                duracao_segundos=self.duracao_analise,
                situacao=situacao,
                observacao_operador=observacao,
                incluir_cdr=self.var_incluir_cdr.get(),
            )
        except Exception as erro:
            messagebox.showerror("Falha ao gerar relatório", str(erro))
            return
        self.botao_confirmar.configure(state="disabled")
        self.botao_corrigir.configure(state="disabled")
        self.rotulo_alertas.configure(text=f"Revisão registrada • pacote: {destino.name}")
        abrir = messagebox.askyesno(
            "Pacote de diagnóstico criado",
            f"O relatório foi salvo em:\n{destino}\n\nDeseja abrir a pasta?",
        )
        if abrir and hasattr(os, "startfile"):
            os.startfile(destino.parent)

    def confirmar_resultado(self) -> None:
        if self.resultado is not None:
            self._salvar_feedback(self.resultado, "confirmado")

    def corrigir_resultado(self) -> None:
        if self.resultado is None:
            return
        dados = deepcopy(self.resultado)
        janela = tk.Toplevel(self.raiz)
        janela.title("Corrigir resultado")
        janela.geometry("900x560")
        janela.minsize(760, 500)
        janela.transient(self.raiz)
        janela.grab_set()
        corpo = ttk.Frame(janela, padding=20)
        corpo.pack(fill="both", expand=True)
        ttk.Label(corpo, text="Corrija o pedido", style="Titulo.TLabel", font=("Segoe UI", 16, "bold")).pack(anchor="w")
        ttk.Label(
            corpo, text="Edite, adicione ou exclua itens. O resultado anterior será preservado no relatório.",
            style="Subtitulo.TLabel",
        ).pack(anchor="w", pady=(3, 12))

        colunas = ("item", "quantidade", "largura", "altura", "material", "acabamento")
        tabela = ttk.Treeview(corpo, columns=colunas, show="headings", height=9)
        titulos = ("Item", "Quantidade", "Largura (cm)", "Altura (cm)", "Material", "Acabamento")
        larguras = (50, 90, 105, 105, 230, 160)
        for coluna, titulo, largura in zip(colunas, titulos, larguras):
            tabela.heading(coluna, text=titulo)
            tabela.column(coluna, width=largura, anchor="center" if coluna != "material" else "w")
        tabela.pack(fill="both", expand=True)

        def atualizar_tabela() -> None:
            for linha in tabela.get_children():
                tabela.delete(linha)
            for indice, item in enumerate(dados.get("itens", [])):
                dim = item.get("dimensoes", {})
                tabela.insert("", "end", iid=str(indice), values=(
                    indice + 1, item.get("quantidade", {}).get("valor") or "",
                    _numero((dim.get("largura_mm") or 0) / 10),
                    _numero((dim.get("altura_mm") or 0) / 10),
                    item.get("material", {}).get("valor") or "",
                    item.get("acabamento", {}).get("valor") or "",
                ))

        def formulario_item(indice: int | None = None) -> None:
            atual = dados["itens"][indice] if indice is not None else {}
            editor = tk.Toplevel(janela)
            editor.title("Editar item" if indice is not None else "Adicionar item")
            editor.geometry("430x360")
            editor.resizable(False, False)
            editor.transient(janela)
            editor.grab_set()
            frame = ttk.Frame(editor, padding=20)
            frame.pack(fill="both", expand=True)
            dim = atual.get("dimensoes", {})
            valores = {
                "Quantidade": str(atual.get("quantidade", {}).get("valor") or 1),
                "Largura (cm)": _numero((dim.get("largura_mm") or 0) / 10),
                "Altura (cm)": _numero((dim.get("altura_mm") or 0) / 10),
                "Material": atual.get("material", {}).get("valor") or "",
                "Acabamento": atual.get("acabamento", {}).get("valor") or "",
            }
            variaveis: dict[str, tk.StringVar] = {}
            for rotulo, valor in valores.items():
                ttk.Label(frame, text=rotulo, style="Subtitulo.TLabel").pack(anchor="w")
                variaveis[rotulo] = tk.StringVar(value=valor)
                ttk.Entry(frame, textvariable=variaveis[rotulo]).pack(fill="x", pady=(3, 10))

            def salvar_item() -> None:
                try:
                    quantidade = int(variaveis["Quantidade"].get())
                    largura = float(variaveis["Largura (cm)"].get().replace(",", "."))
                    altura = float(variaveis["Altura (cm)"].get().replace(",", "."))
                    if quantidade <= 0 or largura <= 0 or altura <= 0:
                        raise ValueError
                except ValueError:
                    messagebox.showwarning("Valores inválidos", "Use números maiores que zero para quantidade e tamanho.", parent=editor)
                    return
                item = deepcopy(atual) if atual else {}
                item.update({
                    "quantidade": {"valor": quantidade, "unidade": "unidade", "fonte": "correcao_operador", "confianca": 1.0},
                    "dimensoes": {"largura_mm": largura * 10, "altura_mm": altura * 10, "tipo": "corrigido", "fonte": "correcao_operador", "confianca": 1.0},
                    "material": {"valor": variaveis["Material"].get().strip() or None, "fonte": "correcao_operador", "confianca": 1.0},
                    "acabamento": {"valor": variaveis["Acabamento"].get().strip() or None, "fonte": "correcao_operador", "confianca": 1.0},
                })
                if indice is None:
                    dados.setdefault("itens", []).append(item)
                else:
                    dados["itens"][indice] = item
                atualizar_tabela()
                editor.destroy()

            ttk.Button(frame, text="Salvar item", style="Primary.TButton", command=salvar_item).pack(anchor="e", pady=(4, 0))

        def editar_selecionado() -> None:
            selecionado = tabela.selection()
            if selecionado:
                formulario_item(int(selecionado[0]))
            else:
                messagebox.showinfo("Selecione um item", "Selecione a linha que deseja editar.", parent=janela)

        def excluir_selecionado() -> None:
            selecionado = tabela.selection()
            if not selecionado:
                return
            del dados["itens"][int(selecionado[0])]
            atualizar_tabela()

        botoes = ttk.Frame(corpo, padding=(0, 10, 0, 0))
        botoes.pack(fill="x")
        ttk.Button(botoes, text="Editar item", command=editar_selecionado).pack(side="left")
        ttk.Button(botoes, text="Adicionar item", command=lambda: formulario_item()).pack(side="left", padx=6)
        ttk.Button(botoes, text="Excluir item", command=excluir_selecionado).pack(side="left")
        ttk.Label(corpo, text="Observação para o diagnóstico", style="Subtitulo.TLabel").pack(anchor="w", pady=(12, 3))
        var_observacao = tk.StringVar()
        ttk.Entry(corpo, textvariable=var_observacao).pack(fill="x")

        def finalizar() -> None:
            correto = normalizar_resultado_corrigido(dados)
            self._mostrar_resultado(correto)
            janela.destroy()
            self._salvar_feedback(correto, "corrigido", var_observacao.get())

        ttk.Button(corpo, text="Finalizar correção e gerar relatório", style="Primary.TButton", command=finalizar).pack(anchor="e", pady=(12, 0))
        tabela.bind("<Double-1>", lambda _evento: editar_selecionado())
        atualizar_tabela()

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
