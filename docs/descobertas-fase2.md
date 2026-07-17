# Descobertas — Fase 2 (diff binário sobre os casos de teste)

Fonte: 16 casos gerados pela macro da Fase 1 no CorelDRAW 2025 OEM (26.0 build 101),
comparados com o motor `fase2-diff-binario/zcf_diff.py`. Relatórios completos por caso em
`fase2-diff-binario/relatorios/`. Contagem de amostras (n) indicada por descoberta —
critério do projeto: só vira "confirmado" com n ≥ 2-3 isolando a mesma variável.

## CONFIRMADO

### C1. Estrutura TLV dos registros `UI` no `Bitmaps.dat` (n=8 arquivos)

`Bitmaps.dat` = cabeçalho de 8 bytes (`01 00 00 00 01 00 00 00`) seguido de registros:

```
tag      4 bytes   ASCII "UI" + 2 bytes zero (55 49 00 00)
tamanho  4 bytes   uint32 little-endian
payload  N bytes
```

- Em registros **não-finais**: `tamanho` = bytes do payload (o registro seguinte começa em
  `offset_tag + 8 + tamanho`). Verificado nos 3 primeiros registros do helo.cdr.
- No registro **final**: `tamanho` = bytes da tag até o fim do arquivo (equivale a
  `payload + 8`). **Não é anomalia — é regra**: reproduzido em TODOS os 8 arquivos
  analisados (helo + 7 casos de teste). Um leitor deve tratar o último registro
  truncando no EOF.
- Endianness little-endian confirmada em todos os campos numéricos decodificados.

### C2. `Bitmaps.dat` só existe quando o documento tem bitmap (n=16)

`caso_00_base` e todos os casos sem bitmap não têm o membro `content/data/Bitmaps.dat`;
ele aparece exatamente nos casos 01–08. O `dataFileList.dat` lista os `.dat` presentes
em ordem alfabética (`Bitmaps.dat`, `data1.dat`, `masterPage.dat`, `page1.dat`, ...) e é
atualizado junto (entrada `page2.dat` adicionada no caso_14).

### C3. Pixels armazenados DESCOMPRIMIDOS, formato de origem descartado (n=6)

- Os 4 formatos de origem (JPEG, PNG, TIFF, BMP) da **mesma imagem** produziram
  `Bitmaps.dat` do mesmo tamanho exato (2.693.386 bytes), sem nenhuma assinatura
  JPEG/PNG interna: os pixels são gravados brutos (24 bpp neste cenário).
- **TIFF vs BMP: byte-idênticos.** PNG difere em apenas 588 bytes de pixel
  (diferenças de decodificação/gamma). JPEG difere nos pixels (decodificação com perdas)
  e no campo de resolução (ver C4).
- Consequência: o arquivo original importado NÃO é preservado dentro do `.cdr`
  (nesta versão/cenário) — o que o helo.cdr mostrou com JPEGs embutidos precisa de mais
  investigação (hipótese H2).

### C4. Cabeçalho da imagem e localização do DPI (n=6, par 07/08 isola a variável)

Layout observado no início do `Bitmaps.dat` com 1 bitmap (offsets absolutos do arquivo;
imagem de referência 400×400 px, 24 bpp):

| Offset | Tipo | Valor observado | Interpretação |
|---:|---|---|---|
| 0 | uint32 LE | 1 | desconhecido (versão?) |
| 4 | uint32 LE | 1 | desconhecido |
| 8 | tag+uint32 | `UI`, tamanho | registro UI (C1) |
| 16 | 24 bytes | `00.. 20 00 00 00 .. 02 00 00 00 ff 00 00 00` | sub-cabeçalho igual em todas as amostras (inclusive helo) |
| 40 | tag | `RI` + campo de tamanho | registro aninhado da imagem |
| 62 | uint32 LE | 400 | **largura em px** |
| 66 | uint32 LE | 400 | **altura em px** |
| 70 | uint32 LE | 1 | planos? |
| 74 | uint32 LE | 24 | **bits por pixel** |
| 78 | uint32 LE | 1200 | **stride da linha** (largura × 3) |
| 82 | uint32 LE | 480000 | **tamanho dos dados de pixel** (W×H×3) |
| 90 | uint32 LE | 3779527 / 11811023 | **resolução X em px/metro × 1000** |
| 94 | uint32 LE | idem | **resolução Y em px/metro × 1000** |
| 118 | bytes | ... | **pixels brutos até o fim do arquivo** |

- O par caso_07 (96 DPI) vs caso_08 (300 DPI) difere em **apenas 6 bytes**: os campos
  dos offsets 90 e 94. 96 DPI → 3.779.527 (= 96/0,0254 × 1000); 300 DPI → 11.811.023.
- Detalhe elegante que valida a interpretação: o JPEG importado registra 11.811.023
  (300 dpi convertido de JFIF: 300/0,0254 × 1000), enquanto PNG/TIFF/BMP registram
  11.811.000 (11.811 px/m nativos do formato × 1000) — mesma resolução nominal, caminhos
  de metadado diferentes.
- Offsets 62..118 são relativos ao arquivo com 1 bitmap; a posição é provavelmente
  relativa ao registro `RI` (offset 40) — a confirmar com casos multi-bitmap.

### C5. Mover bitmap não toca `Bitmaps.dat`; geometria fica em `page1.dat` (n=1 — hipótese forte)

`caso_01` vs `caso_06` (bitmap movido 2 cm): `Bitmaps.dat` **byte-idêntico**. As mudanças
ficam em `page1.dat` (e nos membros "ruidosos" de C7). No diff do `page1.dat`, campos
int32 LE mudam com delta ≈ ±200.000 para 2 cm → unidade interna ≈ 0,1 µm
(100.000 unidades/cm) — hipótese H3.

### C6. Novos membros por tipo de conteúdo (n=1 cada — a reproduzir)

| Conteúdo novo | Membros que passam a existir |
|---|---|
| Bitmap | `content/data/Bitmaps.dat` |
| Texto artístico | `font/fontTable.dat` + `embed/embedding0` (fonte embutida) |
| Segunda página | `content/data/page2.dat` + `previews/page2.png` + entrada no `dataFileList.dat` e no `container.xml` |

### C7. Membros "ruidosos" mudam em quase todo save (n=15)

`META-INF/metadata.xml`, `color/docPalette.xml`, `content/data/data1.dat`,
`content/root.dat` e `styles/document.cdss` mudaram em praticamente todos os pares
(timestamps, GUIDs, previews re-renderizados). `previews/*.png` muda sempre que o visual
muda. Para as próximas análises, o diff deve tratá-los como ruído de fundo e focar em
`page*.dat`, `masterPage.dat` e `Bitmaps.dat` — que só mudam quando a alteração é
estrutural.

### C8. Mapa alteração → membros estruturais alterados (resumo dos 15 diffs)

| Caso | Alteração | Membros estruturais afetados |
|---|---|---|
| 01–04 | adicionar bitmap | +`Bitmaps.dat`; `page1.dat`, `masterPage.dat` |
| 05 | remover bitmap | −`Bitmaps.dat`; `page1.dat` |
| 06 | mover bitmap | só `page1.dat` |
| 07/08 | DPI do bitmap | 6 bytes no `Bitmaps.dat` |
| 09 | nova layer | `page1.dat`, `masterPage.dat` |
| 10 | trocar cor | `page1.dat`, `masterPage.dat` |
| 11 | texto | +`fontTable.dat`, +`embed/embedding0`; `page1.dat`, `masterPage.dat` |
| 12 | segundo objeto | `page1.dat`, `masterPage.dat` |
| 13 | agrupar | só `page1.dat` |
| 14 | segunda página | +`page2.dat`; `page1.dat`, `masterPage.dat`, `dataFileList.dat` |
| 15 | PowerClip | só `page1.dat` |

Leitura: **objetos e suas relações (grupo, PowerClip, posição) vivem em `pageN.dat`** —
consistente e o alvo natural do parser da Fase 3.

## HIPÓTESES (não confirmadas)

- **H1 — Registro `RI` aninhado:** dentro do payload `UI` há um registro `RI` com campo
  de tamanho próprio (no caso_07: `RI` no offset 40 com tamanho 480.078;
  40 + 480.078 = 480.118 = EOF exato, sugerindo "tamanho até o fim" como no `UI` final).
  Estrutura interna do aninhamento ainda não fechada.
- **H2 — helo.cdr: 4 registros `UI` vs 24 bitmaps reportados:** nos casos de teste,
  1 bitmap = 1 registro `UI`. Se a regra geral for "1 imagem armazenada por registro UI",
  o helo teria só 4 imagens armazenadas e os 24 "bitmaps" da interface seriam instâncias/
  usos (deduplicação). Os JPEGs embutidos no helo (achados dentro do 4º registro) também
  contradizem C3 — pode haver mais de um modo de armazenamento (ex.: "manter original"
  para imagens grandes, ou versão do Corel diferente). **Precisa dos casos 16-19 abaixo.**
- **H3 — Coordenadas em `page1.dat`:** int32 LE, ~100.000 unidades por cm (0,1 µm).
  Delta observado no caso_06: +200.032 em X, −198.976 em Y para um movimento nominal de
  (+2, −2) cm.

## Casos de teste da Fase 1b (16-20) — resultado

H1 e H2 foram testadas e majoritariamente resolvidas com os casos 16–20. Ver
[descobertas-fase1b.md](descobertas-fase1b.md) para o detalhe completo:

- H1 confirmada: bitmaps diferentes → 1 registro `UI` por imagem, sequenciais.
- H2 confirmada (deduplicação): o mesmo bitmap usado 2× no documento gera 1 único
  registro `UI` — a 2ª instância é só uma referência em `page1.dat`. Explica o
  descompasso "24 bitmaps reportados vs. poucos registros UI" do helo.cdr.
- H2 (imagem grande → JPEG embutido) **refutada** nesse eixo: JPEG de 2400×2400
  continua vindo como pixels brutos. A hipótese que sobra é que os JPEGs embutidos do
  helo.cdr vêm de fotos reais de câmera (metadado/origem diferente), ainda não testado
  (caso_21, opcional, pendente).
- Descoberta nova: transparência (canal alfa) é um 2º registro `RI` (máscara em escala
  de cinza) aninhado dentro do mesmo `UI`, não um 4º canal RGBA.
