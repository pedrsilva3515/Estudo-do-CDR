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
| 1b | Casos extras para fechar hipóteses sobre múltiplos bitmaps | **Concluída** — 6/6 casos gerados sem falhas, incluindo a foto real (caso_21) |
| 2 | Motor de diferenças binárias (Python) | **Concluída** — 21 pares comparados, relatórios versionados |
| 3 | Parser incremental (Python) | Não iniciada — `Bitmaps.dat` está mapeado o suficiente para começar |
| 4 | Especificação pública + biblioteca instalável com testes | Não iniciada |

## Estrutura do repositório

```
docs/
  evidencias-amostra-helo.md   Evidências do arquivo de exemplo real (helo.cdr)
  descobertas-fase2.md         Descobertas confirmadas + hipóteses, com nível de confiança
  descobertas-fase1b.md        Descobertas dos casos 16-20 (multi-bitmap, dedup, CMYK, alfa)
casos-de-teste/                21 .cdr gerados pelas Fases 1/1b + manifestos JSON + imagens-fonte
fase1-gerador-casos/
  GeradorCasosZCF.bas          Macro VBA que gera os casos de teste + manifestos JSON
  README.md                    Instruções de instalação/execução da macro
fase2-diff-binario/
  zcf_diff.py                  Motor de diff binário entre pares de .cdr (ZCF)
  relatorios/                  Um relatório Markdown por caso de teste
  README.md                    Uso e limitações do motor
```

## Estado atual (resumo das descobertas)

Detalhes e contagem de amostras em [docs/descobertas-fase2.md](docs/descobertas-fase2.md)
e [docs/descobertas-fase1b.md](docs/descobertas-fase1b.md):

- **`Bitmaps.dat` decodificado em grande parte**: sequência plana de registros `UI`
  (um por imagem única — deduplicado, ver abaixo), cada um com um sub-registro `RI`
  aninhado (tag 2 bytes + tamanho, sem padding) contendo largura, altura, bpp, stride,
  tamanho dos pixels e resolução (px/metro × 1000). Pixels gravados **descomprimidos**
  em todos os casos sintéticos testados, inclusive JPEG de 2400×2400 px.
- **Deduplicação confirmada**: o mesmo bitmap usado 2× no documento gera 1 único
  registro `UI` — a 2ª instância é só uma referência em `page1.dat`. Explica em grande
  parte o "24 bitmaps reportados vs. poucos registros UI" do helo.cdr.
- **Transparência (alfa) é um 2º `RI`** (máscara em escala de cinza) aninhado dentro do
  mesmo `UI`, não um 4º canal RGBA. CMYK usa 32 bpp (4 × 8 bits) num único `RI`.
- **Objetos e relações (posição, grupo, PowerClip) vivem em `pageN.dat`** — mover ou
  duplicar um bitmap não altera um byte do `Bitmaps.dat`.
- Texto embute a fonte (`font/fontTable.dat` + `embed/embedding0`); página nova cria
  `page2.dat` + preview + entrada no `dataFileList.dat`.
- **Pendência resolvida:** os "JPEGs embutidos" do helo.cdr eram coincidência estatística
  em dados de pixel bruto de alta entropia, não um segundo modo de armazenamento —
  confirmado importando uma foto real de câmera (`caso_21`) e reanalisando os 4 blocos do
  helo.cdr com verificação de marcador JPEG válido. **Todo bitmap testado até agora,
  sintético ou real, é armazenado como pixels descomprimidos.**
