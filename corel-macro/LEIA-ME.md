# Macro do Leitor de Pedidos no CorelDRAW

Janela dentro do CorelDRAW 2025 (versão 26) que analisa o arquivo aberto e,
ao clicar num item, seleciona no desenho a peça que o programa interpretou.
A análise roda fora do Corel, pela pasta `Documentos\Estudo-do-CDR` (a mesma
do aplicativo), chamada por `scripts\ponte_corel.bat`.

Versão 1: analisar, mostrar os itens e selecionar a peça. A correção pela
seleção no Corel vem na versão 2.

## Instalar (uma vez)

1. No CorelDRAW, abra o editor: **Alt+F11** (menu Ferramentas → Scripts →
   Editor de scripts; em versões antigas, Ferramentas → Macros).
2. No painel da esquerda, clique em **GlobalMacros**.
3. Menu **Arquivo → Importar arquivo...** e escolha `corel-macro\LeitorPedidos.bas`.
4. Menu **Inserir → UserForm**. Na janela Propriedades (F4), troque **(Name)**
   para `frmLeitor`.
5. Clique com o botão direito em `frmLeitor` → **Exibir código**. Apague o que
   houver e cole todo o conteúdo de `corel-macro\frmLeitor_codigo.txt`.
6. **Ctrl+S** para salvar e feche o editor.

## Usar

- Abra o pedido no CorelDRAW (o arquivo precisa estar salvo).
- Alt+F8 (ou Ferramentas → Scripts → Executar script) → `AbrirLeitorPedidos`.
- **Analisar (sem IA)**: grátis. Se as regras não resolvem sozinhas, os itens
  aparecem como "(a confirmar)".
- **Analisar com IA**: o mesmo fluxo do aplicativo (regras, depois a IA
  configurada no aplicativo).
- Clique num item da lista: a peça fica selecionada e a tela aproxima nela.

## Atualizar

`LeitorPedidos.bas`: no editor, remova o módulo `LeitorPedidos` (botão direito →
Remover, sem exportar) e importe de novo. `frmLeitor`: apague o código e cole o
novo.
