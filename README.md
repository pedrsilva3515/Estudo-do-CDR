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
| 1 | Gerador de casos de teste (macro VBA para CorelDRAW 2025 OEM) | **Entregue — aguardando execução no CorelDRAW** |
| 2 | Motor de diferenças binárias (Python) | Não iniciada — depende dos arquivos gerados na Fase 1 |
| 3 | Parser incremental (Python) | Não iniciada |
| 4 | Especificação pública + biblioteca instalável com testes | Não iniciada |

## Estrutura do repositório

```
docs/
  evidencias-amostra-helo.md   Evidências coletadas do arquivo de exemplo real (helo.cdr)
fase1-gerador-casos/
  GeradorCasosZCF.bas          Macro VBA que gera os casos de teste + manifestos JSON
  README.md                    Instruções de instalação/execução da macro
```

## Estado atual

- A estrutura do contêiner ZCF foi verificada em um arquivo real (ver
  [docs/evidencias-amostra-helo.md](docs/evidencias-amostra-helo.md)), incluindo uma
  descoberta nova: os registros `UI` do `Bitmaps.dat` seguem estrutura TLV
  (tag + tamanho uint32 little-endian + payload).
- A macro da Fase 1 está pronta para ser testada dentro do CorelDRAW 2025 OEM.
  Os arquivos `.cdr` gerados por ela serão os insumos da Fase 2.
