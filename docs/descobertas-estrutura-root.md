# Descobertas — árvore estrutural de `content/root.dat`

Fonte: casos controlados da Fase 1 e arquivo real com grupos e PowerClips.

## E1. `root.dat` é um índice RIFF completo

O arquivo começa com `RIFF/CDRT` ou `RIFF/CDRH` e contém árvores `LIST` com
tipos como:

- `page`, `layr` e `gobj` para páginas/layers;
- `grp ` para grupos;
- `obj ` para objetos;
- `lnkg` para grupos ligados;
- `clpt` para estruturas de conteúdo/recorte.

Isso substitui a necessidade de inferir a árvore somente pelos bytes de
`pageN.dat`.

## E2. Folhas de 16 bytes apontam para os membros de dados

Campos como `loda`, `bbox`, `obbx` e `trfd` têm payload de 16 bytes:

```text
uint32  id_do_arquivo
uint32  tamanho
uint32  offset
uint32  reservado (observado = 0)
```

Os IDs são os índices, em base zero, de `content/dataFileList.dat`.
`Bitmaps.dat` ocupa uma posição na lista quando presente, ainda que seus
registros de imagem também tenham identificadores internos próprios. Em um
arquivo sem bitmaps:

- `0` → `data1.dat`
- `1` → `masterPage.dat`
- `2` → `page1.dat`
- `3` → `page2.dat`, quando presente

Quando `Bitmaps.dat` é a primeira entrada, os demais IDs são deslocados em
uma posição: `data1.dat=1`, `masterPage.dat=2`, `page1.dat=3`; IDs seguintes
acompanham páginas/dados adicionais.

O intervalo apontado por `loda` identifica o blob pertencente ao objeto. Uma
instância de bitmap é associada ao objeto cujo intervalo contém o offset do
seu descritor.

## E3. `bbox` é a caixa visível absoluta na página

`bbox` aponta para quatro `int32`:

```text
[ esquerda, topo, direita, base ]
```

A unidade é 100.000 por cm. O tamanho é obtido por
`abs(direita-esquerda)` e `abs(topo-base)`.

Em bitmaps retangulares sem recorte, largura e altura do `bbox` batem com o
tamanho natural da imagem multiplicado pela escala da matriz. Em PowerClips
com contorno complexo, o `bbox` representa somente a área visível recortada,
enquanto a matriz continua representando a escala dos pixels da imagem inteira.

## E4. `trfd` contém a matriz absoluta do objeto

`trfd` aponta para 96 bytes. A matriz afim está no offset `+40` do bloco,
como seis `float64`:

```text
[ a, b, tx, c, d, ty ]
```

A matriz lida por `root.dat` é byte/numericamente igual à matriz encontrada
depois do descritor do bitmap. Ela já usa coordenadas absolutas da página.

### Correção de hipótese anterior

Não se deve multiplicar novamente pelas matrizes de grupos ancestrais. Nos
arquivos observados, filhos e grupos guardam suas próprias caixas/matrizes em
coordenadas da página; a matriz do grupo resume sua geometria, não é uma
transformação local a ser reaplicada aos filhos.

Isso permite tratar a escala do objeto bitmap como escala final e calcular o
DPI efetivo por:

```text
escala_x = hypot(a, c)
escala_y = hypot(b, d)
dpi_x = dpi_nativo_x / escala_x
dpi_y = dpi_nativo_y / escala_y
```

O parser só promove o valor a `dpi_efetivo_x/y` quando o descritor foi ligado
a um objeto de `root.dat` e sua matriz estrutural foi recuperada.

## E5. Ligação entre recipiente e conteúdo de PowerClip

Confirmada com `caso_15` e três casos adicionais: dois PowerClips na mesma
página, um em cada uma de duas páginas e dois níveis aninhados.

O conteúdo fica sob `LIST/clpt` e seu grupo raiz recebe um identificador
imediato na folha `spnd`. O `loda` do objeto recipiente contém, em um dos
offsets declarados por sua própria tabela, um campo de 16 bytes:

```text
uint32  spnd_do_grupo_de_conteudo
uint32  1
uint32  0
uint32  flag  # observado como 0 ou 1
```

Assim, a página do recipiente pode ser propagada ao grupo `clpt` e a todos os
seus descendentes. Em PowerClips aninhados, a propagação é iterativa: depois
que o recipiente interno herda a página do grupo externo, seu próprio vínculo
atribui a mesma página ao próximo grupo de conteúdo.

No documento real `Debora ellen fdf.cdr`, os quatro vínculos observados são
`3`, `5`, `7` e `9`. Dois estão em curvas diretamente na página e dois em
curvas dentro de outro PowerClip. O resultado atribui página 1 aos 13 objetos,
incluindo os 10 guardados em `data1.dat`.
