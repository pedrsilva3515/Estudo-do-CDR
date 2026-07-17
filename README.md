# Estudo do CDR — Engenharia Reversa do Formato ZCF

Projeto de engenharia reversa do formato `.cdr` moderno do CorelDRAW (ZCF — *ZIP Container Format*),
com o objetivo de produzir:

1. **Uma especificação técnica aberta** do formato interno (`root.dat`, `page*.dat`,
   `masterPage.dat`, `Bitmaps.dat`, `dataFileList.dat`), com offsets, cabeçalhos, tipos de
   registro, endianness e referências cruzadas — tudo baseado em evidência reproduzível.
2. **Uma biblioteca de leitura em Python** capaz de abrir um `.cdr` sem depender do CorelDRAW
   instalado, expondo páginas, layers, objetos, textos, curvas, bitmaps, cores e metadados.
3. **Pontos de integração** com a automação existente da gráfica (Kanban de produção,
   manifestos de job, validação de arquivos antes da fila de impressão).

## Princípio metodológico

Nenhuma conclusão sobre o formato é declarada com base em um único arquivo. Um arquivo
permite formular hipóteses; confirmar exige comparar arquivos que diferem em **exatamente uma
característica por vez** e observar quais bytes mudam. Toda descoberta é documentada com nível
de confiança explícito (`confirmado por N casos` vs. `hipótese não testada`).

## Fases

| Fase | Entregável | Status |
|------|-----------|--------|
| 1 | Gerador de casos de teste (macro VBA para CorelDRAW 2025 OEM) | **Concluída** — 16/16 casos gerados sem falhas (Corel 26.0 build 101) |
| 1b | Casos extras para fechar hipóteses sobre múltiplos bitmaps | **Entregue — aguardando execução no CorelDRAW** (`GeradorCasosZCF_1b.bas`) |
| 2 | Motor de diferenças binárias (Python) | **Concluída** — 15 pares comparados, relatórios versionados |
| 3 | Parser incremental (Python) | Não iniciada — próximo alvo: `Bitmaps.dat` (estrutura já mapeada) e depois `pageN.dat` |
| 4 | Especificação pública + biblioteca instalável com testes | Não iniciada |

## Estrutura do repositório

```
docs/
  evidencias-amostra-helo.md   Evidências do arquivo de exemplo real (helo.cdr)
  descobertas-fase2.md         Descobertas confirmadas + hipóteses, com nível de confiança
casos-de-teste/                16 .cdr gerados pela Fase 1 + manifestos JSON + imagens-fonte
fase1-gerador-casos/
  GeradorCasosZCF.bas          Macro VBA que gera os casos de teste + manifestos JSON
  README.md                    Instruções de instalação/execução da macro
fase2-diff-binario/
  zcf_diff.py                  Motor de diff binário entre pares de .cdr (ZCF)
  relatorios/                  Um relatório Markdown por caso de teste
  README.md                    Uso e limitações do motor
```

## Estado atual (resumo das descobertas)

Detalhes e contagem de amostras em [docs/descobertas-fase2.md](docs/descobertas-fase2.md):

- **`Bitmaps.dat` decodificado em grande parte**: registros TLV `UI` (tag + tamanho
  uint32 LE + payload), com regra especial confirmada para o último registro; cabeçalho
  de imagem com largura, altura, bpp, stride, tamanho dos pixels e resolução
  (armazenada como px/metro × 1000); pixels gravados **descomprimidos** — o arquivo de
  origem (JPEG/PNG/TIFF/BMP) é descartado na importação (neste cenário).
- **Objetos e relações (posição, grupo, PowerClip) vivem em `pageN.dat`** — mover um
  bitmap não altera um byte do `Bitmaps.dat`.
- Texto embute a fonte (`font/fontTable.dat` + `embed/embedding0`); página nova cria
  `page2.dat` + preview + entrada no `dataFileList.dat`.
- Pendência principal: conciliar "24 bitmaps vs. 4 registros UI com JPEGs embutidos"
  do arquivo real helo.cdr (hipótese de deduplicação/segundo modo de armazenamento) —
  precisa dos casos 16–19 propostos.
