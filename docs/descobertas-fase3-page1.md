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

### Geometria: candidato forte, ainda não confirmado (bloqueado por falta de caso de teste)

Logo depois do fim do JSON (offset 1146 em `caso_00`), aparecem 4 números em ponto
flutuante (`float32` LE): **10.1444091796875, 9.52587890625, 1.875, 1.875**. São fortes
candidatos a bounding box / posição do objeto — mas:

- Esses valores são **idênticos** entre `caso_00` e `caso_12` (onde `RetanguloBase` não
  foi movido nem redimensionado) — consistente com "são a geometria do retângulo", mas
  não prova nada sozinho, já que nada mudou.
- O mesmo padrão **não se replicou para o objeto `ElipseTeste`** no `caso_12` — o cálculo
  do início do chunk pela regra "nome está sempre 96 bytes após o início do chunk" só
  vale para o retângulo; a elipse claramente usa uma tabela/estrutura diferente (`size`/
  `count` deram valores absurdos ao tentar aplicar a mesma regra), o que faz sentido:
  retângulo e elipse provavelmente têm sub-tipos de chunk geométrico distintos
  (bounding box vs. centro+raios).
- **Não havia, até esta rodada, nenhum caso de teste que movesse ou redimensionasse um
  objeto vetorial por um delta conhecido** (o `caso_06` da Fase 1 move um *bitmap*, não
  o retângulo vetorial) — sem isso, não dá para saber com confiança qual float é X, qual
  é Y, e se são posição, tamanho, ou algo do documento todo (ex. página).

**Ação tomada:** macro nova `GeradorCasosZCF_1c.bas` (Fase 1c), com dois casos
desenhados para fechar isso — mesma lógica de isolar uma variável por vez que já
funcionou para o DPI do bitmap (Fase 1b, `caso_07`/`caso_08`):

- `caso_22_move_retangulo`: move `RetanguloBase` por um delta conhecido e **assimétrico**
  (+5 cm X, −1 cm Y — de propósito diferente em cada eixo, para não confundir X com Y se
  a ordem dos campos for ambígua). O manifesto grava posição/tamanho antes e depois via
  `GetPosition`/`GetSize`, então o gabarito é exato mesmo que a semântica do parâmetro de
  `CreateRectangle2` não seja 100% conhecida.
- `caso_23_resize_retangulo`: aumenta **só a largura** de `RetanguloBase` em 4 cm,
  mantendo a altura — isola tamanho de posição (`SetSize` normalmente mantém um canto/
  centro de referência, então a posição não deve mudar, ou muda de forma previsível).

Pendente: rodar a macro no CorelDRAW e comparar `caso_22`/`caso_23` contra `caso_00`.

## HIPÓTESES / OBSERVAÇÕES (não confirmadas — precisam de mais amostras)

- **H4 — Unidade de coordenada:** a hipótese H3 da Fase 2 (`~100.000 unidades/cm`,
  baseada no diff do `caso_06`) não foi revisitada nesta rodada. Vários candidatos a
  campo de coordenada aparecem perto dos blocos de nome/estilo (ex. valores como
  `40001`, `2000`, `16001` no início do arquivo), mas nenhum foi cruzado com uma posição
  conhecida de forma conclusiva ainda.
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
