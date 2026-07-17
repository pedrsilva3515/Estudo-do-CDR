# Fase 1 — Gerador de casos de teste (macro VBA)

Macro para CorelDRAW 2025 OEM que gera os arquivos `.cdr` de teste da Fase 1, cada um variando
**uma única característica** em relação a um documento base, com um manifesto JSON ao lado de
cada arquivo descrevendo exatamente o que mudou.

## Instalação

1. Abra o CorelDRAW e pressione `Alt+F11` para abrir o editor VBA.
2. Em `GlobalMacros`, insira um **módulo** novo (botão direito → Inserir → Módulo).
3. Cole o conteúdo de [`GeradorCasosZCF.bas`](GeradorCasosZCF.bas) no módulo
   (não é necessário importar arquivo — é só colar; nenhum form é usado).
4. Se quiser mudar a pasta de saída, edite a constante `PASTA_SAIDA` no topo
   (padrão: `C:\CDR_Testes\`).
5. Coloque o cursor dentro da Sub `GerarCasosDeTeste` e pressione `F5`.

## O que a macro gera

Na pasta de saída:

| Arquivo | Base de comparação | O que isola |
|---|---|---|
| `caso_00_base.cdr` | — | Documento mínimo (1 retângulo vermelho) |
| `caso_01_add_bitmap_jpeg.cdr` | caso_00 | Bitmap importado de JPEG |
| `caso_02_add_bitmap_png.cdr` | caso_00 | Bitmap importado de PNG |
| `caso_03_add_bitmap_tiff.cdr` | caso_00 | Bitmap importado de TIFF |
| `caso_04_add_bitmap_bmp.cdr` | caso_00 | Bitmap importado de BMP |
| `caso_05_remove_bitmap.cdr` | caso_01 | Remoção de bitmap |
| `caso_06_move_bitmap.cdr` | caso_01 | Mover bitmap (só transformação) |
| `caso_07_bitmap_dpi_096.cdr` | caso_08 | DPI do bitmap (mesmos 400×400 px, 96 DPI) |
| `caso_08_bitmap_dpi_300.cdr` | caso_07 | DPI do bitmap (mesmos 400×400 px, 300 DPI) |
| `caso_09_nova_layer.cdr` | caso_00 | Layer nova vazia |
| `caso_10_altera_cor.cdr` | caso_00 | Troca de cor de preenchimento |
| `caso_11_texto.cdr` | caso_00 | Texto artístico |
| `caso_12_dois_objetos.cdr` | caso_00 | Segundo objeto (elipse) — base dos casos 13 e 15 |
| `caso_13_grupo.cdr` | caso_12 | Agrupamento (mesmos objetos do caso_12) |
| `caso_14_segunda_pagina.cdr` | caso_00 | Segunda página |
| `caso_15_powerclip.cdr` | caso_12 | PowerClip (mesmos objetos do caso_12) |

Além disso:

- `caso_XX_*.json` — manifesto de cada caso (tipo de alteração, parâmetros, arquivo base,
  data e versão do Corel);
- `fonte_base.jpg/png/tif/bmp`, `fonte_dpi096.jpg`, `fonte_dpi300.jpg` — imagens-fonte
  exportadas pelo próprio Corel (a **mesma** imagem em 4 formatos, mais o par de DPI);
- `fonte_master.cdr` — documento usado para gerar as imagens-fonte;
- `log_geracao.txt` — log com um registro por caso (OK ou erro com número/descrição).

Observações de desenho dos casos:

- Os casos 13 (grupo) e 15 (PowerClip) partem do `caso_12`, não do base — assim o diff
  binário entre `caso_12` e cada um deles isola **só** a operação de agrupar/clipar, sem
  misturar com a criação da elipse.
- O par 07/08 usa duas fontes JPEG com pixels idênticos (400×400) e só o DPI diferente,
  para isolar onde o DPI é gravado.

## Restrições da versão OEM respeitadas

- Nenhum form `.frm`/`.frx` — só um módulo colado à mão.
- `MsgBox` usa constantes numéricas: `48` (= vbExclamation) e `64` (= vbInformation).
- `vbCrLf`/`vbDirectory` também foram substituídos por `Chr$(13) & Chr$(10)` e `16`.

## Se algo falhar

Cada caso é isolado: uma falha é registrada em `log_geracao.txt` e a macro continua nos
demais. Os pontos com maior chance de precisar de ajuste fino na sua build do Corel são:

1. **`ExportBitmap`** (geração das imagens-fonte) — a assinatura varia entre versões.
   Se o log acusar erro aqui, me mande o número/descrição do erro que eu ajusto os parâmetros.
2. **`FindShapes(Type:=cdrBitmapShape)`** (casos 05/06).
3. **`AddToPowerClip`** (caso 15).

Me devolva o `log_geracao.txt` (ou só as linhas de erro) que a gente corrige pontualmente
antes de seguir para a Fase 2.

## Próxima fase

Com os `.cdr` gerados e validados, a Fase 2 será um script Python que extrai os `.dat`
internos de cada par (base vs. variante) e reporta offsets, tamanho e hexdump de cada
trecho alterado.
