# Descobertas — `META-INF/metadata.xml`

Fonte: 28 casos numerados (`caso_00` a `caso_27`), 2 documentos-fonte e um
arquivo real externo, todos no formato ZCF. O XML foi comparado com os
manifestos dos casos e com a estrutura efetivamente presente no contêiner.

## M1. Tamanho nominal da página está disponível diretamente

`META-INF/metadata.xml` contém os campos XMP:

- `cdrinfo:PageWidth` e `cdrinfo:PageHeight`, em 10.000 unidades por mm;
- `cdrinfo:PageDimensions`, já formatado em texto;
- `cdrinfo:PageSizeName` (por exemplo, `A4`);
- `cdrinfo:PageOrientation`, como código numérico;
- `cdrinfo:NumPages` e `cdrinfo:NumLayers`.

Nos 30 arquivos controlados, `2100000 × 2970000` corresponde a
`210 × 297 mm`, coerente com `PageDimensions` e `PageSizeName=A4`. A escala é
a mesma já observada para coordenadas: 100.000 unidades por cm.

O parser deriva `retrato`/`paisagem` comparando largura e altura, sem depender
de uma interpretação ainda não documentada do enum `PageOrientation`.

### Página padrão versus tamanhos individuais

O `caso_32` usa página 1 A4 e página 2 de `100 × 200 mm`, deixando a página 2
ativa no salvamento. Mesmo assim, o XML continua declarando `210 × 297 mm`.
Logo, esses campos representam o tamanho padrão/primeira página, não a página
ativa nem cada página individual. Os overrides individuais ficam nos membros
`pageN.dat`; o parser os expõe por `doc.paginas_estruturais()`.

## M2. Contagens de objetos e efeitos também estão no XML

O recurso `cdrinfo:Objects` fornece `Total`, `Group`, `Curve`, `Rect`,
`Bitmap`, `Ellipse`, `Text` e outros tipos. `cdrinfo:Effects` fornece contagens
de `PowerClip`, `Contour`, `DropShadow`, `Blend`, `Transparency` e outros.

Essas contagens são muito úteis para inventário e triagem, mas são um resumo:
elas não identificam cada objeto, sua layer, geometria ou relações. A árvore de
`page*.dat` continua necessária para isso.

## M3. Informações adicionais já disponíveis

O mesmo XML expõe:

- fontes usadas e indicador global de fontes incorporadas;
- versão interna, versão do aplicativo e build do CorelDRAW;
- resolução X/Y do documento;
- perfis de cor e modo de cor;
- resumo de preenchimentos, contornos e cores spot;
- objetos OLE e links de bitmap;
- estatísticas de texto e curvas.

A primeira implementação em `zcfreader/metadata.py` cobre o tamanho da página,
contagens principais, fontes e versão. Os demais grupos podem ser adicionados
incrementalmente sem engenharia reversa binária.
