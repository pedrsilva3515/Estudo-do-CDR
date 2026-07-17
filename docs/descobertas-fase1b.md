# Descobertas — Fase 1b (múltiplos bitmaps, deduplicação, CMYK, alfa)

Fonte: casos 16–20 gerados pela macro `GeradorCasosZCF_1b.bas` no CorelDRAW 2025 OEM
(26.0 build 101, mesma instalação da Fase 1/2), comparados par a par com
`fase2-diff-binario/zcf_diff.py`. Caso 21 (foto real) não foi gerado — nenhuma
`foto_real.jpg` foi fornecida, e o caso foi pulado como projetado. Relatórios completos em
`fase2-diff-binario/relatorios/diff_caso_1[6-9]*.md` e `diff_caso_20*.md`.

Isso fecha (ou refina) as hipóteses H1 e H2 abertas em `descobertas-fase2.md`.

## CONFIRMADO

### D1. H1 confirmada: cada imagem distinta gera um registro `UI` próprio (n=1, estrutura clara)

`caso_16` (duas imagens diferentes) tem **exatamente 2 registros `UI`** no `Bitmaps.dat`,
um logo em seguida do outro — o 2º começa exatamente no byte onde o 1º termina
(`8 + 8 + tamanho₁ = offset do UI #2`). Isso confirma que `Bitmaps.dat` é uma sequência
plana de registros `UI`, um por imagem armazenada, sem tabela de offsets separada — a
navegação é sequencial (responde a uma pergunta em aberto da Fase 2).

### D2. H2 confirmada: bitmaps duplicados são deduplicados (n=1, mas evidência direta e conclusiva)

`caso_17` (o mesmo bitmap usado duas vezes no documento) tem `Bitmaps.dat`
**byte-idêntico** ao `caso_01` (que tem só uma instância) — mesmo tamanho exato
(2.693.386 bytes) e diff binário zero. A segunda instância do bitmap na página é
referenciada a partir de `page1.dat` (ver D6), não duplicada no `Bitmaps.dat`.

**Isso explica em grande parte o "24 bitmaps reportados vs. 4 registros UI" do
helo.cdr**: o CorelDRAW conta *usos* de bitmap na interface, mas armazena cada *imagem
única* uma só vez. Os 24 usos do helo.cdr provavelmente correspondem a bem menos de 24
imagens distintas — plausivelmente perto de 4, uma por registro `UI`.

### D3. Estrutura interna do registro `UI` decodificada até o nível de pixel

Layout completo de um registro `UI` de imagem única (offsets absolutos, arquivo com 1
bitmap 947×947 24bpp):

```
0    uint32 LE   1              cabeçalho do arquivo (2× uint32, significado ainda aberto)
4    uint32 LE   1
8    tag         "UI\0\0"       registro de imagem (ver C1 em descobertas-fase2.md)
12   uint32 LE   tamanho        regra de tamanho: ver C1 (não-final = payload; final = distância até o fim do escopo)
16   24 bytes    sub-cabeçalho comum (ver D5)
40   tag         "RI"           registro aninhado (2 bytes, SEM padding — ver D4)
42   uint32 LE   tamanho        mesma regra de "distância até o fim do escopo" que o UI
46   6 bytes     desconhecido (constante "00 00 4e 00 00 00" nas amostras)
52   uint32 LE   ?              65536 em todas as amostras (flag/versão?)
56   uint32 LE   ?              65536 em todas as amostras
60   uint32 LE   ?              geralmente = largura (parece duplicar o campo 62; a
                                 confirmar se é realmente distinto)
62   uint32 LE   largura (px)
66   uint32 LE   altura (px)
70   uint32 LE   planos         observado sempre = 1
74   uint32 LE   bits/pixel     24 (RGB), 32 (CMYK) — ver D7
78   uint32 LE   stride         bytes por linha (largura × bytes/pixel, ver D7)
82   uint32 LE   tamanho pixels stride × altura
86   6 bytes     desconhecido
90   uint32 LE   resolução X    px/metro × 1000 (ver C4 em descobertas-fase2.md)
94   uint32 LE   resolução Y    px/metro × 1000
98   ~20 bytes   desconhecido
118  N bytes     dados de pixel brutos, sem compressão, até o fim do registro
```

O campo 60 precisa de mais amostras para confirmar se é um segundo campo de largura,
altura ou outra coisa (nas amostras de teste é numericamente igual ao campo 62 na
maioria dos casos, mas isso pode ser coincidência de dimensões).

### D4. Tag `RI`: 2 bytes de tag, sem padding — header de 6 bytes, não 8 (n=6)

Diferente do `UI` (`tag[2] + reservado[2] + tamanho[4]` = 8 bytes de header), o `RI`
usa `tag[2] + tamanho[4]` = **6 bytes de header**. Verificado em 6 amostras (caso_01,
02, 07, 18, 19, e os dois `RI` de caso_16): em todas, a fórmula
`offset_da_tag + 6 + tamanho = fim_do_escopo_do_RI` fecha exatamente (mesma regra de
"tamanho mede até o fim do escopo, no registro final" do `UI`, aplicada de forma
consistente e recursiva por nível de aninhamento — não é um caso especial, é a regra
geral do formato TLV usado em todo o `Bitmaps.dat`).

Verificado também que essa regra é relativa ao **escopo do contêiner imediato**, não ao
arquivo inteiro: em `caso_16`, o `RI` dentro do 1º `UI` (não-final, seguido por um 2º
`UI`) usa `tamanho` = distância até o fim do **payload do seu próprio `UI`**, não até o
fim do arquivo — e os dois registros `RI` de `caso_16` (imagens diferentes, mas mesmas
dimensões) relataram o mesmo `tamanho` exato (2.693.346), consistente com "distância até
o fim do escopo que os contém", que é do mesmo tamanho para as duas imagens idênticas em
dimensão.

### D5. Imagem grande (2400×2400) continua armazenada como pixels brutos — H2 original refutada nesse eixo (n=1)

`caso_18` (JPEG de 2400×2400 px, ~17,3 MB de pixels brutos) **não tem nenhuma assinatura
JPEG** dentro do `Bitmaps.dat` — é 1 único registro `UI`/`RI` com pixels descomprimidos,
mesmo padrão dos casos menores. Isso **refuta** a hipótese de que "imagem grande o
suficiente" por si só faz o CorelDRAW preservar o arquivo original comprimido.

A explicação mais provável agora para os JPEGs embutidos observados no `helo.cdr` é
outra: fotos reais de câmera (com metadados EXIF, perfil de cor incorporado, ou
originadas de um caminho de importação diferente — ex. "colar da área de transferência"
vs. "Importar arquivo") podem seguir um código de armazenamento diferente das imagens
sintéticas exportadas pelo próprio Corel usadas nestes testes. **O caso_21 (opcional, com
uma foto real) continua sendo o teste decisivo para essa hipótese** — ainda não foi
gerado nesta rodada.

### D6. Mover/duplicar bitmap só toca `page1.dat`, nunca `Bitmaps.dat` (n=2)

Confirmado de novo com `caso_17`: `Bitmaps.dat` idêntico ao base; toda a informação da
segunda instância (posição, referência à imagem) fica em `page1.dat`. Consistente com
C5 da Fase 2 (mover bitmap não toca `Bitmaps.dat`).

### D7. Espaço de cor determina bits por pixel e stride, de forma previsível (n=2)

| Caso | Espaço de cor | bpp | stride | tamanho pixels |
|---|---|---:|---:|---:|
| caso_02 (PNG RGB) | RGB | 24 | 2.844 (= 947×3) | 2.693.268 |
| caso_19 (TIFF CMYK) | CMYK | **32** | **3.788** (= 947×4) | 3.587.236 |

CMYK usa 4 bytes por pixel (K/C/M/Y de 8 bits cada, ordem exata ainda não decodificada),
consistente com stride = largura × 4.

## HIPÓTESE NOVA (n=1, não confirmada)

### D8. Canal alfa (transparência) é armazenado como um SEGUNDO registro `RI` (máscara em escala de cinza), aninhado dentro do mesmo `UI`

`caso_20` (PNG com transparência) tem `Bitmaps.dat` com **1 único registro `UI`**, mas
esse `UI` contém **dois registros `RI` em sequência**:

1. **RI #1** — imagem RGB normal: 947×947, 24 bpp, stride 2.844, exatamente igual ao
   `caso_02` (mesma imagem sem alfa) em todos os campos de pixel.
2. **RI #2**, logo em seguida — 947×947, **8 bpp**, stride 948 (= largura + 1),
   tamanho de dados 897.756 (= stride × altura): uma **máscara em escala de cinza do
   tamanho da imagem**, quase certamente o canal alfa extraído.

Ou seja: transparência não é um 4º canal intercalado (como RGBA), e sim uma imagem de
máscara separada, anexada como um segundo `RI` dentro do mesmo `UI`. Isso é consistente
com como CorelDRAW historicamente trata máscaras de bitmap (como um objeto de
"Transparência de Bitmap" separado internamente).

**Achado colateral não fechado:** o sub-cabeçalho comum de 24 bytes (offset 16–39, ver
D3) tem um campo no offset 24 que é `0` em todos os casos sem 2º `RI`, mas **2.693.378**
em `caso_20` — valor que corresponde a `(offset absoluto do RI #2) − 8` = `2.693.386 − 8`.
Hipótese: esse campo é um **ponteiro/offset relativo para o início do próximo `RI`**
(ou, equivalentemente, sinaliza "existe um 2º sub-registro, e ele começa aqui"). Só uma
amostra — precisa de outro caso com alfa e dimensões diferentes para confirmar se é um
offset (variaria com o tamanho da imagem) ou uma contagem/flag fixa.

## Casos de teste ainda recomendados (Fase 1c)

- **caso_21 — foto real** (ainda pendente, é opcional): decisivo para D5/H2 — se uma
  foto de câmera aparecer como JPEG embutido no `Bitmaps.dat`, confirma que o modo de
  armazenamento depende da origem/metadados da imagem, não só do tamanho.
- **Duas imagens diferentes, uma delas com alfa**: fecha D8 combinando com D1 (testa se o
  campo do offset 24 realmente varia como offset, e se um 2º `UI` também pode ter seu
  próprio 2º `RI` de máscara).
- **Bitmap com apenas 1 bit de profundidade (bitmap ao estilo "1 bit", preto e branco)**:
  testaria os limites do campo bpp e se stride é arredondado para múltiplo de byte.
