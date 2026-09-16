# Descobertas — páginas, sangria e limites de objetos

Fonte: cinco casos controlados novos (`caso_28` a `caso_32`), gerados pelo
CorelDRAW 26.0, mais o documento real externo.

## L1. Cabeçalho de `data1.dat`

Campos confirmados por alterações isoladas:

```text
offset +12  uint32  largura padrão da página
offset +16  uint32  altura padrão da página
offset +42  uint32  sangria
offset +670 int32   DrawingOriginX
offset +674 int32   DrawingOriginY
```

Todos usam 10.000 unidades por milímetro. O caso de sangria de 3 mm grava
`30000` no offset `42`; o documento padrão com 4 mm grava `40000`.

`DrawingOriginX/Y` controla a origem da régua/API. Alterá-la de `(0,0)` para
`(5,-7 cm)` não muda nenhum `bbox` nem a classificação dos objetos fora da
página. Portanto, esses campos não devem ser confundidos com posição física.

## L2. Tamanho individual de página

O tamanho do cabeçalho é o padrão do documento e corresponde à página 1 no
caso misto. Quando uma página tem tamanho próprio, seu `LIST/page` possui um
`LIST/lgob` direto cujo `loda` aponta para um bloco de 68 bytes:

```text
uint32[8] cabeçalho = 68, 2, 20, 32, 0, 40, 52, 68
offset +52 uint32 largura
offset +56 uint32 altura
```

No `caso_32`, a página 1 é A4 (`210 × 297 mm`) e a página 2 é
`100 × 200 mm`. O XML continua resumindo A4, mas o bloco da página 2 contém
`1000000 × 2000000` e é recuperado pelo parser.

## L3. Coordenadas locais e conferência de bordas

Os objetos de cada `pageN.dat` usam coordenadas locais aproximadamente
centradas em zero. Casos com quadrados atravessando 5 mm em cada lado
confirmaram as quatro comparações contra `±largura/2` e `±altura/2`.

Pequenos deslocamentos inferiores a 0,1 mm foram observados após a organização
interna das páginas pelo Corel. Por isso, `doc.conferencia_limites()` usa
tolerância padrão de 0,1 mm para evitar falsos positivos na borda exata.

O resultado informa o excesso em cada lado e se o objeto ultrapassa também a
sangria. O `caso_31` confirma a distinção: o objeto sai do corte cerca de 3 mm,
mas permanece dentro da sangria configurada.

## L4. PowerClips participam da conferência

A ligação recipiente → grupo `clpt` foi confirmada por casos controlados
simples, duplos, multipágina, aninhados e fora da página. O parser propaga o índice da página
por essa relação, de modo que objetos guardados em `dataN.dat` também entram
em `doc.conferencia_limites()`.

A associação só é aceita quando o ID `spnd` do grupo é único e o campo de
vínculo começa em um offset declarado pela tabela do `loda`; relações
ambíguas permanecem sem página em vez de serem adivinhadas.

No `caso_36`, recipiente e elipse recortada ultrapassam a borda direita. A
conferência retorna duas ocorrências: uma de `page1.dat` e outra de
`data1.dat`, provando que o conteúdo interno deixou de ser omitido.
