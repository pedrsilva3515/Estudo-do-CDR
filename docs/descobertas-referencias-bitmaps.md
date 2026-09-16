# Descobertas — ligação objeto/instância → `Bitmaps.dat`

Fonte: todos os casos numerados (`caso_00` a `caso_27`) e um arquivo real
externo com 6 objetos bitmap e 4 imagens únicas. A contagem encontrada pelo
parser foi comparada com `cdrinfo:Objects/inObj:Bitmap` de
`META-INF/metadata.xml` em cada caso.

## R1. Identificador de cada imagem única

Cada registro `UI` de `Bitmaps.dat` é precedido por dois `uint32` little-endian.
O primeiro valor é um identificador da imagem. No primeiro `UI`, esse par é o
próprio cabeçalho de 8 bytes do arquivo; nos registros seguintes, aparece nos
8 bytes imediatamente anteriores à tag `UI`.

Esse identificador não é necessariamente sequencial. No arquivo real testado,
as quatro imagens têm IDs `29`, `39`, `40` e `53`.

## R2. Descritor de instância confirmado

Cada uso de bitmap contém o seguinte descritor em `pageN.dat` ou `dataN.dat`:

```text
uint16  tipo                    observado = 2
uint16  bits_por_pixel          24 (RGB) ou 32 (CMYK)
uint32  largura                 pixels
uint32  altura                  pixels
uint32  indice_logico           semântica exata ainda não fechada
uint32  identificador_bitmap    aponta para o prefixo do UI em Bitmaps.dat
uint32  zero
uint32  campo/flag ainda aberto
uint32  0xffffffff              sentinela confirmada
uint32  zero
uint32  zero
...     campos seguintes ainda não interpretados
```

A ligação não depende só do ID: o parser exige também que largura, altura e
bpp coincidam com o registro `RI`, além das sentinelas estruturais. Isso reduz
fortemente o risco de falso positivo em dados binários.

## R3. Deduplicação e instâncias confirmadas ponta a ponta

- `caso_17`: 1 registro `UI`, 2 descritores de instância, ambos apontando para
  o mesmo ID. Confirma a reutilização da mesma imagem por dois objetos.
- `caso_16`: 2 registros `UI`, 2 descritores, cada descritor apontando para um
  ID diferente.
- `caso_19`: o campo de 16 bits do descritor vale 32 e coincide com o bitmap
  CMYK de 32 bpp; nos casos RGB vale 24.
- Nos 28 casos numerados, a quantidade de descritores encontrada coincide com
  a contagem de objetos bitmap declarada em `metadata.xml`.

## R4. `dataN.dat` também pode conter objetos bitmap

Nos casos simples, os descritores ficam em `page1.dat`. No arquivo real, que
contém PowerClips, os 6 descritores foram encontrados em `data1.dat`, enquanto
`page1.dat` contém a estrutura externa. Portanto, um leitor não pode procurar
referências apenas em páginas; precisa varrer `pageN.dat` e `dataN.dat`.

No arquivo real:

- ID 29 → 2 instâncias;
- ID 39 → 2 instâncias;
- ID 40 → 1 instância;
- ID 53 → 1 instância.

Total: 6 objetos bitmap referenciando 4 imagens únicas, exatamente igual ao
resumo XMP do documento.

## O que isso desbloqueia

Já é possível inventariar instâncias reais e dizer qual imagem única cada uma
usa. A associação posterior com `root.dat` também fornece a geometria
permanente do objeto e permite calcular DPI efetivo (R5 e documento da árvore).

## R5. Matriz afim junto ao descritor da instância

Depois do descritor existe uma representação vetorial do limite do bitmap e,
em seguida, uma matriz afim de seis `float64`:

```text
[ a, b, tx, c, d, ty ]
```

O campo no offset `+40` do descritor é a quantidade de nós dessa representação.
Cada nó acrescenta 9 bytes; portanto a matriz começa em:

```text
offset_descritor + 144 + 9 × numero_de_nos
```

Evidências:

- limite retangular comum: 5 nós → matriz em `+189`;
- objeto real com 26 nós → matriz em `+378`;
- objeto real com 263 nós → matriz em `+2511`;
- `caso_01` versus `caso_06`: apenas `tx` e `ty` mudam, respectivamente
  `+200.000` e `−200.000`, exatamente o movimento VBA de `+2 cm, −2 cm`;
- `caso_17`: as duas instâncias da mesma imagem têm matrizes próprias e
  translações diferentes.

As escalas são `hypot(a,c)` e `hypot(b,d)`. Isso permite calcular tamanho e
DPI depois da transformação. O parser mantém os nomes
`matriz_local`, `largura_local_mm`, `altura_local_mm` e
`dpi_efetivo_local_x/y` para distinguir a leitura direta do descritor da
validação estrutural posterior, não porque a matriz use coordenadas relativas.

### Validação pela árvore estrutural

`root.dat` foi posteriormente decodificado como árvore RIFF e liga cada objeto
ao seu bloco `loda`, `bbox` e `trfd`. A matriz de `trfd` é igual à encontrada
junto do descritor e já está em coordenadas absolutas da página: matrizes de
grupos não devem ser multiplicadas novamente. Quando essa ligação estrutural é
confirmada, o parser expõe o resultado como `dpi_efetivo_x/y`. Ver
`docs/descobertas-estrutura-root.md`.
