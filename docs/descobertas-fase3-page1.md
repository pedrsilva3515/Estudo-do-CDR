# Descobertas — Fase 3 (`page1.dat`, primeira fatia)

Investigação inicial da estrutura de `content/data/page*.dat`, motivada pela C5/C8 da
Fase 2 ("objetos e suas relações — grupo, PowerClip, posição — vivem em `pageN.dat`").
Ao contrário do `Bitmaps.dat`, **`page1.dat` não foi totalmente decodificado nesta
rodada** — é uma árvore de "chunks" binários bem mais complexa. O que segue é o que foi
confirmado o suficiente para já virar código (`fase3-parser/zcfreader/page.py`), mais o
que ficou registrado como observação para retomar depois.

## CONFIRMADO

### P1. As propriedades de estilo (preenchimento/contorno/transparência) são gravadas como JSON em texto puro (n=4 documentos, 6 objetos)

Ao contrário do resto do arquivo (binário denso), o preenchimento, contorno e
transparência de cada objeto são gravados como uma **string JSON legível**, sem nenhuma
ofuscação. Exemplo real (`caso_00_base`, retângulo CMYK 0,100,100,0):

```json
{
  "fill": {
    "overprint": "0",
    "primaryColor": "CMYK,USER,0,100,100,0,100,00000000-0000-0000-0000-000000000000",
    "screenSpec": "0,0,45000000,60,0",
    "secondaryColor": "CMYK,USER,0,0,0,0,100,00000000-0000-0000-0000-000000000000",
    "type": "1"
  },
  "outline": {
    "color": "CMYK,USER,0,0,0,100,100,00000000-0000-0000-0000-000000000000",
    "width": "2000"
  },
  "transparency": {}
}
```

- `primaryColor`/`outline.color` seguem o padrão `"CMYK,USER,C,M,Y,K,tint,GUID"` — os 4
  primeiros números batem exatamente com os valores passados para `CreateCMYKColor` na
  macro VBA, confirmado em `caso_00` (vermelho), `caso_10` (alterado para ciano) e
  `caso_12` (retângulo vermelho + elipse verde, cada um com seu próprio JSON).
- **A string é precedida por um `uint32` little-endian com o tamanho exato em bytes** —
  verificado em `caso_00` (344) e `caso_10` (342), batendo com `len()` do JSON até o
  último `}`.
- `json.loads()` da biblioteca padrão decodifica direto, sem nenhum tratamento especial.
- Ao trocar a cor (`caso_10`), o JSON inteiro é **substituído por um novo bloco**, não
  editado em memória — o tamanho do bloco pai (ver P3) aumenta e o offset de outros
  itens desloca. Isso é consistente com "salvar" reescrevendo a árvore de objetos, não
  fazendo patch binário in-place.

### P2. Nomes de layers e objetos são UTF-16LE, terminados em `\0\0`, precedidos por um GUID de 16 bytes (n=6 documentos)

Cada nome (de layer ou de objeto — **não dá para diferenciar um do outro só pelo
padrão**, ver limitações) aparece como texto UTF-16LE puro, terminado por dois bytes
zero, com um GUID de 16 bytes imediatamente antes. Exemplo (`caso_00`, offset 750-794):

```
750  86 2f e5 52 b6 4f a3 43 97 f5 61 6a 9f 43 33 b8   <- GUID (16 bytes)
766  52 00 65 00 74 00 61 00 6e 00 67 00 75 00 6c 00   <- "Retangul" (UTF-16LE)
782  6f 00 42 00 61 00 73 00 65 00 00 00               <- "oBase" + \0\0
```

Verificado em `caso_00`, `caso_09` (achou `CamadaTeste`, a layer criada na macro),
`caso_12`/`caso_13` (achou `ElipseTeste` e `RetanguloBase` nos dois, nomes distintos e
consistentes com a ordem de criação), e nos 2 documentos base (sempre acham
`Linhas-guia` e `Camada 1` — layers padrão criadas pelo próprio CorelDRAW, não pela
macro; confirma que todo documento novo já nasce com essas 2 layers).

**Não há um prefixo de tamanho explícito para o nome** (diferente do JSON, P1) — o
parser lê até encontrar o terminador duplo `\0\0` alinhado em posição par.

### P3. Padrão de "chunk" recorrente: tamanho + contagem + tabela de offsets (n=vários, semântica ainda não fechada)

Em vários pontos do arquivo aparece a mesma assinatura de 8+ bytes:

```
uint32 LE  tamanho_do_bloco
uint32 LE  contagem_de_itens
uint32 LE[contagem]  tabela de offsets/tamanhos (semântica ainda não decodificada por completo)
```

Exemplo em `caso_00`, offset 80: `tamanho=111, contagem=3, offsets=[20,36,...]`. Ao
trocar a cor do objeto (`caso_10`), o bloco equivalente passa a `tamanho=123,
contagem=4` — a mudança de cor **adicionou um item** à tabela em vez de só editar um
campo, reforçando a leitura de P1 (novo bloco de estilo substitui, não edita).

Esse padrão se repete em pelo menos 6 pontos diferentes do mesmo arquivo, em
profundidades diferentes (parece uma árvore, não uma lista plana) — indício forte de que
é a moldura estrutural geral do formato "chunk" do `page*.dat` (análogo ao papel que
`UI`/`RI` cumprem no `Bitmaps.dat`).

### P4. O "chunk" do objeto: tabela de offsets decodificada o bastante para achar nome, estilo e o início da geometria (n=2 objetos, 2 documentos)

Usando as âncoras já confirmadas (offset exato do nome — P2 — e do bloco JSON — P1)
como referência, dá para calibrar a tabela de offsets de P3 **especificamente para o
chunk que envolve um objeto** (`RetanguloBase`, em `caso_00` e `caso_12`):

```
670  uint32 LE   616            tamanho do chunk (aponta exatamente para offset 1286 = 670+616)
674  uint32 LE   7              "contagem" (semântica exata ainda não fechada — ver abaixo)
678  uint32 LE[] 20,52,1,80,96,124,476,480,608,612,616   tabela de valores (11, não 7 — ver abaixo)
```

Os valores da tabela, quando somados ao início do chunk (670), batem **exatamente** com
marcos já confirmados por outro caminho:

| Valor na tabela | Posição absoluta (670+valor) | O que é |
|---:|---:|---|
| 96 | 766 | **Início do nome** `RetanguloBase` (confirmado por P2) |
| 124 | 794 | Início do bloco `[flag uint32=1][tamanho uint32][JSON]` (P1) |
| 476 | 1146 | **Fim exato do JSON** (802 + 344 = 1146) — bate byte a byte |

Isso confirma que a tabela é, pelo menos em parte, uma lista de **offsets relativos ao
início do chunk**, e que o valor "7" declarado como contagem não corresponde 1:1 ao
número de valores brutos da tabela (11) — possivelmente contagem conta "propriedades"
enquanto alguns valores da tabela são pares (offset+tipo) ou sub-tamanhos, não só
offsets. Não fechado — próxima rodada.

### P5. H3 CONFIRMADA: unidade de coordenada vetorial = exatamente 100.000 unidades/cm (0,1 µm) (n=2 casos, delta limpo e exato)

Os casos `caso_22` (move `RetanguloBase` +5 cm X, −1 cm Y) e `caso_23` (aumenta só a
largura em +4 cm) fecharam a hipótese H3 da Fase 2, que vinha de uma estimativa
aproximada no movimento de um *bitmap*. Agora confirmado para um objeto **vetorial**,
com deltas exatos, sem arredondamento:

```
delta X (+5 cm) -> +500.000 unidades   (500.000 / 5 = 100.000 unid/cm, exato)
delta Y (−1 cm) -> −100.000 unidades   (100.000 / 1 = 100.000 unid/cm, exato)
```

**Nota importante para quem for usar essa descoberta:** o manifesto JSON de `caso_22`/
`caso_23` saiu com todos os campos de posição/tamanho zerados — bug no macro
`GeradorCasosZCF_1c.bas` (`GetPosition`/`GetSize` foram chamados com os parâmetros
envolvidos em `CDbl(x0)`, que cria um valor temporário e não escreve de volta em `x0`;
o padrão `CDbl()` da skill `coreldraw-vba` serve para conversão de entrada, não para
capturar saída `ByRef`). A confirmação acima não depende do manifesto — veio de
comparar os bytes de `caso_22`/`caso_23` contra `caso_00` e achar deltas que batem
exatamente com o que a macro *deveria* ter feito (o `Move`/`SetSize` em si funcionaram
normalmente; só o log ficou incompleto). Fica registrado para não reusar esse padrão de
log sem corrigir.

### P6. Localização da geometia de `RetanguloBase`: região fixa no início do arquivo, não dentro do "chunk nomeado" do objeto (n=3 casos)

A posição/tamanho de `RetanguloBase` **não está** nos 4 floats encontrados depois do
JSON de estilo (P3/P4) — esses 4 floats (`10.1444091796875, 9.52587890625, 1.875,
1.875`) ficaram **idênticos** em `caso_22` (objeto movido) e mudaram de forma confusa em
`caso_23` — não são a geometria, ou pelo menos não são só isso (hipótese aberta: podem
ser um ponto de referência/âncora de rotação, independente de posição).

A geometria de verdade está numa região **bem mais cedo no arquivo**, a partir do
offset absoluto 16 — a mesma região que já aparecia nos primeiros hex dumps deste
projeto como "3 blocos de 16 bytes quase idênticos" (ver `docs/descobertas-fase2.md`,
C5, que já suspeitava disso a partir do movimento de um bitmap). Confirmado agora:

- **Essa região é específica de `RetanguloBase`, não da página inteira**: comparando
  `caso_00` (só o retângulo) com `caso_12` (retângulo + elipse, retângulo sem se mover),
  os 48 bytes da região ficam **byte-idênticos** — adicionar outro objeto em outra
  posição não altera nada aqui. Ou seja, não é um bounding-box agregado da página; é
  algo específico do primeiro objeto (a confirmar se é "por índice de criação" ou "por
  algum outro critério" com mais objetos nomeados).
- **Layout de cada bloco de 16 bytes** (`int32` LE, 4 campos): `[X, flag=2, campo?, Y]`.
  - Campo 0 (**X**): delta exato de +500.000 no `caso_22` (move +5cm X); **inalterado**
    no `caso_23` (resize sem mover X) — confirma que é a coordenada X.
  - Campo 1 (constante `2` em todos os casos testados): não muda com posição nem
    tamanho — provável tipo/flag, não geometria.
  - Campo 2 (**hipótese, não confirmado**): muda de forma não-linear no `caso_22`
    (+349.285 a +350.285, não é múltiplo limpo de 100.000) mas fica **inalterado** no
    `caso_23` (resize sem mudar posição). Padrão consistente com um **checksum/valor
    derivado de (X,Y)** recalculado a cada mudança de posição, não uma coordenada bruta
    — hipótese razoável, não fechada.
  - Campo 3 (**Y**): delta exato de −100.000 no `caso_22` (move −1cm Y) — confirma que é
    a coordenada Y. **Mas também muda no `caso_23`** (resize só de largura): +133.333,
    o que **não é compatível com "Y simples"**, já que a altura não mudou. 133.333 ≈
    400.000 (delta de largura em unidades) ÷ 3 — condizente com um **ponto de controle
    de curva Bézier cúbica** (regra clássica "1/3 e 2/3 do segmento" usada para
    representar uma aresta reta como Bézier), não uma posição pura. **Hipótese forte,
    não fechada**: os retângulos podem ser armazenados internamente como curvas
    fechadas (4 cantos + pontos de controle), não como um bounding box simples — comum
    em formatos vetoriais, e explicaria por que um campo "parece Y" mas reage a mudança
    de largura.
  - **3º bloco de 16 bytes** difere dos outros 2 por uma constante fixa: campo X é
    1.000 unidades mais negativo (`-751713` vs `-750713`). 1.000 unidades = 0,01 cm =
    **exatamente metade da largura do contorno** (`"width":"2000"` no JSON de estilo,
    P1, na mesma escala de 100.000 unid/cm → 2000 unid = 0,02cm, metade = 1.000
    unidades). Hipótese: blocos 1–2 = bounding box só do preenchimento; bloco 3 =
    bounding box incluindo a expansão do contorno (que se estende para fora do
    caminho, centrado nele).

**Resumo do nível de confiança:** unidade (100.000/cm) e a existência de campos X/Y
nessa região — **confirmados**. Layout exato dos 4 campos por bloco, significado do
campo 2 (checksum?) e do padrão 1/3 do campo Y sob resize (Bézier?), e diferença do
3º bloco (contorno?) — **hipóteses fortes, consistentes com todas as evidências
coletadas, mas não fechadas**. Não testado ainda: rotação, um objeto com altura
alterada (só testamos largura), e se esse padrão se repete para outros objetos além do
primeiro criado no documento.

### Próximos casos de teste sugeridos (Fase 1d)

- Redimensionar só a **altura** (complementa `caso_23`, que só mexeu na largura) — se a
  hipótese Bézier estiver certa, deve mexer no campo X (não no Y) de forma fracionada.
- Rotacionar o retângulo por um ângulo conhecido — para ver se aparece em algum lugar
  próximo dessa mesma região, ou se vive em outro lugar (matriz de transformação?).
- Criar um SEGUNDO objeto nomeado e movê-lo (não o primeiro) — para confirmar se cada
  objeto tem sua própria região de 3 blocos, e onde ela fica localizada em relação ao
  primeiro objeto (logo depois? em outro lugar determinado pela ordem de criação?).

## HIPÓTESES / OBSERVAÇÕES (não confirmadas — precisam de mais amostras)

- ~~H4 — Unidade de coordenada~~: **confirmada, virou P5 acima** (100.000 unidades/cm,
  exato, testado com um objeto vetorial movido por delta conhecido).
- **Contagem de objetos no `helo.cdr`:** o arquivo real tem **24 blocos de estilo JSON**
  em `page1.dat` — o mesmo número que o CorelDRAW reporta como "24 bitmaps" na
  interface. Consistente com a hipótese de deduplicação da Fase 1b (D2): são
  provavelmente 24 *objetos/instâncias* na página, referenciando só 4 imagens únicas no
  `Bitmaps.dat`. Só 2 desses objetos têm nome (as layers padrão) — os outros 22 (as
  instâncias de bitmap, presumivelmente) não foram nomeados pelo usuário, o que é o
  cenário comum em arquivos reais.

## Impacto na biblioteca (`fase3-parser/zcfreader/page.py`)

Dado que a árvore de chunks (P3) não está fechada, o parser desta rodada **não tenta
decodificá-la** — em vez disso, faz duas varreduras heurísticas independentes e bem mais
simples, validadas com testes automatizados contra 6 casos de teste:

1. `parse_page()`: acha nomes (P2) e pareia cada um com o próximo bloco de estilo JSON
   (P1) que aparecer antes do nome seguinte. **Só é confiável quando todo objeto tem
   nome** — funciona bem nos casos de teste (a macro nomeia os objetos que cria), mas
   sub-representa documentos reais como o `helo.cdr`, onde a maioria dos objetos não é
   nomeada (ver observação acima).
2. `parse_estilos()`: acha **todos** os blocos JSON de estilo, sem depender de nome —
   mais completo, mas sem conseguir dizer a qual objeto cada um pertence.

Nenhuma geometria (posição, tamanho, pontos de curva) é extraída ainda — fica para uma
próxima rodada, que provavelmente vai exigir decodificar P3 de verdade (a árvore de
chunks) para conseguir associar cada JSON de estilo ao seu objeto de forma confiável,
independente de nome.

## Próximos passos sugeridos

- Decodificar a semântica da tabela de offsets de P3 comparando `caso_00` (1 objeto) com
  `caso_12` (2 objetos) e `caso_13` (2 objetos agrupados) byte a byte, tentando entender
  como a árvore cresce por objeto e como o agrupamento (`caso_13`) e o PowerClip
  (`caso_15`) alteram a hierarquia — `caso_15` chamou atenção na Fase 2 por *diminuir* o
  tamanho do `page1.dat` em relação ao `caso_12`, o que sugere reestruturação, não só
  adição.
- Uma vez a árvore entendida, localizar os campos de geometria (posição, largura,
  altura, ângulo de rotação) e testar a hipótese H3 (unidade ~0,1 µm) com casos que
  isolem só a posição (ex. gerar um caso novo movendo um objeto vetorial simples, não um
  bitmap, por uma distância conhecida).
- Testar `parse_page()`/`parse_estilos()` contra mais arquivos reais (não só o `helo.cdr`)
  para confirmar se o padrão P1/P2/P3 se mantém em documentos com curvas, texto e
  PowerClip — ou se algum desses tipos de objeto usa uma representação de estilo
  diferente da JSON.
