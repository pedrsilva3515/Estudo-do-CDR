# Descobertas — gestão de cor

O contexto de cor do documento é armazenado em `color/color.xml`. O caso 104
alterou somente o intento de renderização para `Saturation`; o XML mudou de
`RelativeColorimetric` para `Saturation`. A API `doc.contexto_cor()` expõe o
modelo, o intento e os indicadores de objetos RGB, CMYK e em cinza.
