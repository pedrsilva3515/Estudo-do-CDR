# Evidências — arquivo de exemplo `helo.cdr`

Análise do arquivo real `helo.cdr` (4.226.173 bytes como ZIP; salvo pelo CorelDRAW em formato
ZCF). Data da análise: 2026-07-17. **Tamanho da amostra: 1 arquivo (n=1)** — pelo critério de
validação do projeto, nada aqui é "confirmado" ainda; tudo é observação ou hipótese que precisa
ser reproduzida nos casos de teste da Fase 1.

## 1. Contêiner ZIP (observado, n=1)

O `.cdr` é um ZIP comum. `file` o identifica como "Corel Draw drawing, version 17-22".
Conteúdo completo (17 arquivos, 19.110.992 bytes descomprimidos):

| Caminho | Bytes | Observação |
|---|---:|---|
| `mimetype` | 45 | Texto: `application/x-vnd.corel.zcf.draw.document+zip` |
| `content/root.dat` | 6.864 | Não analisado ainda |
| `content/dataFileList.dat` | 46 | Índice ASCII (ver §2) |
| `content/data/Bitmaps.dat` | 18.880.632 | Ver §4 |
| `content/data/data1.dat` | 20.888 | Não analisado ainda |
| `content/data/masterPage.dat` | 541 | Não analisado ainda |
| `content/data/page1.dat` | 26.521 | Não analisado ainda |
| `META-INF/container.xml` | 690 | Ver §3 |
| `META-INF/metadata.xml` | 8.440 | |
| `META-INF/links.xml` | 53 | Apenas `<linkInfo />` (documento sem links externos) |
| `META-INF/textinfo.xml` | 597 | |
| `color/color.xml` | 426 | |
| `color/docPalette.xml` | 107 | |
| `color/profiles/rgb/srgb color space profile.icm` | 3.144 | |
| `styles/document.cdss` | 25.868 | |
| `previews/thumbnail.png` | 124.363 | |
| `previews/page1.png` | 11.767 | |

## 2. `dataFileList.dat` (observado, n=1)

Texto ASCII puro, um nome por linha, separado por `\n` (LF), **sem** newline final:

```
Bitmaps.dat
data1.dat
masterPage.dat
page1.dat
```

Os nomes são relativos a `content/data/`. É o índice que diz ao leitor quais arquivos de
dados existem.

## 3. `META-INF/container.xml` (observado, n=1)

Segue o padrão de contêiner do OASIS Open Document Format
(namespace `urn:oasis:names:tc:opendocument:xmlns:container`) com extensão própria da Corel
(`urn:corel:namespaces:zcf:xmlns:container`, prefixo `crl:`). Três `rootfile`:

- `crl:file-kind="main"` → `content/root.dat`, media-type `application/x-vnd.corel.cdr.rootdata`
- `crl:file-kind="thumbnail"` → `previews/thumbnail.png` (com `crl:image-width/height`)
- `crl:file-kind="page"` → `previews/page1.png`, com `crl:index="1"` e
  `crl:caption=":[Página 1];br:[Página 1];"` (legenda com variantes por idioma — o prefixo
  vazio parece ser o default e `br` o locale pt-BR)

Vale comparar com a especificação pública do ODF container como ponto de partida.

## 4. `Bitmaps.dat` (18.880.632 bytes)

### Observações reproduzidas nesta análise (n=1)

- Primeiros 8 bytes do arquivo: `01 00 00 00 01 00 00 00` (significado desconhecido —
  possivelmente versão e/ou contadores).
- A tag ASCII `UI` seguida de 2 bytes zero (`55 49 00 00`) ocorre **exatamente 4 vezes**,
  nos offsets: `8`, `4.720.182`, `9.443.268`, `14.161.978`.
- Assinaturas JPEG (`FF D8 FF`): **exatamente 4**, nos offsets `16.844.202`, `17.741.247`,
  `18.010.492`, `18.262.570` — todas dentro do 4º bloco `UI`. Nenhuma assinatura PNG
  (`89 50 4E 47...`) no arquivo inteiro.
- O CorelDRAW reporta 24 bitmaps neste documento; portanto 20 bitmaps **não** estão
  armazenados como JPEG reconhecível.
- **Atualização (Fase 1b, resolvido):** essas 4 assinaturas JPEG são coincidência
  estatística em dados de pixel bruto, não um segundo modo de armazenamento — ver D9 em
  [descobertas-fase1b.md](descobertas-fase1b.md). Os 4 blocos `UI` do helo.cdr, incluindo
  o 4º, são pixels RGB descomprimidos como todos os outros.

### Descoberta nova: registros `UI` são TLV (hipótese forte, n=1)

Os 4 bytes imediatamente após cada tag `UI\0\0` são um **uint32 little-endian com o tamanho
do payload** do registro. Verificação: `offset_da_tag + 8 (tag+tamanho) + tamanho` cai
exatamente no offset da tag seguinte:

| Offset da tag | Tamanho lido (LE) | Fim calculado | Offset da próxima tag |
|---:|---:|---:|---:|
| 8 | 4.720.166 | 4.720.182 | 4.720.182 ✓ |
| 4.720.182 | 4.723.078 | 9.443.268 | 9.443.268 ✓ |
| 9.443.268 | 4.718.702 | 14.161.978 | 14.161.978 ✓ |
| 14.161.978 | 4.718.654 | 18.880.640 | — (fim do arquivo = 18.880.632) ⚠ |

Estrutura hipotética do registro: `tag (4 bytes ASCII+padding) + tamanho (uint32 LE) + payload`.

**Atualização (Fase 2):** o "excesso de 8 bytes" do último registro se repetiu em TODOS os
7 casos de teste com bitmap — é regra do formato, não anomalia: no registro final,
`tamanho` = bytes da tag até o EOF (equivale a medir a partir do início da tag).
Ver C1 em [descobertas-fase2.md](descobertas-fase2.md).

- **Endianness:** os campos de tamanho são little-endian (consistente com formato Windows/x86).
- Os payloads dos 4 registros `UI` começam com os **mesmos 24 bytes**
  (`00 00 00 00 20 00 00 00 00 00 00 00 00 00 00 00 02 00 00 00 FF 00 00 00`), sugerindo um
  sub-cabeçalho comum. Logo adiante (offset 40 do arquivo) aparece a sequência `52 49 06 06`
  (`RI` + 2 bytes) seguida de outros campos — possível registro aninhado, ainda não decodificado.

### Hipótese de trabalho (herdada da investigação anterior — REFUTADA na Fase 1b)

A hipótese original era que bitmaps importados de formatos diferentes (PNG, TIFF, BMP)
seriam guardados em formato interno de compressão próprio, o que explicaria 24 bitmaps
reportados vs. 4 assinaturas JPEG. Os casos `caso_01`–`caso_04` (Fase 1) e o `caso_21`
(Fase 1b, foto real) mostraram que **todo bitmap testado é armazenado como pixels RGB
descomprimidos**, independente do formato de origem ou de ser uma foto real de câmera.
O descompasso "24 bitmaps vs. poucos registros `UI`" é explicado por deduplicação
(D2 em [descobertas-fase1b.md](descobertas-fase1b.md)), não por formato de armazenamento.

## O que ainda não foi investigado

- Estrutura interna de `root.dat`, `page1.dat`, `data1.dat`, `masterPage.dat`.
- Como bitmaps, cores e objetos se referenciam entre os `.dat`.
- Se existe índice/tabela de offsets apontando para cada um dos 24 bitmaps individualmente
  (a estrutura TLV dos registros `UI` sugere que a navegação pode ser sequencial por
  registros, não por tabela — a confirmar).
