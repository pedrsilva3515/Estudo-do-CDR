# Fase 2 — Motor de diferenças binárias

Script Python que compara pares de arquivos `.cdr` (ZCF), extrai cada membro interno do
contêiner ZIP e reporta exatamente o que mudou: membros novos/removidos/idênticos/alterados,
e para cada membro alterado as regiões de bytes divergentes (offset, tamanho, hexdump
lado a lado). Sem dependências além da biblioteca padrão (Python 3.9+).

## Uso

Comparar um par:

```
python zcf_diff.py caso_00_base.cdr caso_01_add_bitmap_jpeg.cdr -o relatorio.md
```

Comparar todos os pares descritos nos manifestos `caso_*.json` de uma pasta
(cada caso é comparado contra o `arquivo_base` declarado no seu manifesto):

```
python zcf_diff.py --all ../casos-de-teste -o relatorios
```

## Saída

Um relatório Markdown por caso em `relatorios/diff_<caso>.md`, com tabela-resumo
(membros só no base / só na variante / idênticos / alterados) e, por membro alterado:

- **tamanhos iguais** → lista de regiões alteradas (diferenças a menos de 32 bytes de
  distância são fundidas numa região só), com hexdump base × variante;
- **tamanhos diferentes** → prefixo e sufixo comuns + hexdump do início do "miolo"
  divergente de cada lado.

Os relatórios versionados em `relatorios/` foram gerados a partir dos 16 casos da Fase 1.
As conclusões extraídas deles estão em [`../docs/descobertas-fase2.md`](../docs/descobertas-fase2.md).

## Limitações conhecidas

- Quando os tamanhos diferem, o alinhamento é só por prefixo/sufixo comum — uma inserção
  no meio "desloca" o resto e o miolo reportado fica maior do que a mudança real.
- Membros ruidosos (`metadata.xml`, `data1.dat`, `docPalette.xml`, `document.cdss`,
  `root.dat`, previews) mudam em quase todo save; ver C7 em `descobertas-fase2.md`.
