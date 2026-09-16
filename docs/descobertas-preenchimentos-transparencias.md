# Preenchimentos e transparências

## Evidência controlada

Os casos 67–71 alteram somente o preenchimento ou a transparência do
`RetanguloBase` do caso 00. Em `content/data/page1.dat`, cada objeto continua
a ter um JSON de estilo, já localizado pelo parser de página.

| Propriedade no CorelDRAW | Campo confirmado no JSON | Evidência |
| --- | --- | --- |
| Sem preenchimento | `fill.type = "0"` | caso 67 |
| Preenchimento uniforme | `fill.type = "1"` | casos 00, 68 e 69 |
| Cor CMYK | `fill.primaryColor = "CMYK,..."` | casos 00 e 68 |
| Cor RGB 0–255 | `fill.primaryColor = "RGB255,..."` | caso 69 |
| Sobreimpressão de preenchimento | `fill.overprint = "1"` | caso 70 |
| Transparência uniforme de 50% | `transparency.uniformTransparency = "0.5"` | caso 71 |
| Degradê linear | `fill.type = "2"` e `fill.fountainType = "1"` | caso 72 |
| Transparência graduada | `transparency.fill.type = "2"` | casos 76–79 |
| Padrão de duas cores | `fill.type = "8"` e `patternId` | caso 80 |

Para CMYK, as quatro componentes seguem o modelo e a paleta:
`CMYK,USER,C,M,Y,K,opacidade,identificador`. Para RGB, as três componentes
seguem `RGB255,USER,R,G,B,opacidade,identificador`.

Nos degradês, a cor inicial permanece em `primaryColor` e a final em
`secondaryColor`. O caso 72 também confirmou `angle`, `numSteps` e `rateValue`
(ponto médio) como campos do preenchimento. Os tipos de degradê são linear=1,
radial=2, cônico=3 e quadrado=4, confirmados respectivamente nos casos 72–75.
O caso 82 confirma que a orientação linear de 45 graus é registrada somente em
`fill.angle="45"`; a orientação padrão do caso 72 é `0`.
O caso 83 confirma que o ponto médio de 25% é registrado em
`fill.rateValue="25"`; o valor padrão é `50`.
O caso 84 confirma que cada parada adicional aparece em `intermediateColors`
como posição, cor, opacidade, modo de mistura e ponto médio.
O caso 85 confirma que um degradê com dez bandas discretas é registrado em
`fill.numSteps="10"`; o valor `0` dos casos anteriores indica transição suave.

A transparência graduada tem uma camada externa com `startTransparency` e
`endTransparency`. Sua geometria é serializada em `transparency.fill`, com os
mesmos códigos de degradê do preenchimento. Os casos 76–79 confirmam os tipos
linear, radial, cônico e quadrado, todos de 0 (opaco) para 1 (transparente).

Os dois padrões vetoriais de duas cores escolhidos manualmente confirmam
`patternId`, as duas cores e as dimensões de repetição `tilingWidth` e
`tilingHeight`: a trama linear usa id 5 e repetição de 1.000.000; o xadrez usa
id 1 e repetição de 100.000. Como esse estilo começa pelo campo
`StackedBitmapEffects`, o leitor aceita esse prefixo além do prefixo simples
`fill`.

## API disponível

`ItemNomeado.estilo_tipado` e `doc.estilos_tipados_da_pagina()` devolvem
`PreenchimentoObjeto`, `CorObjeto` e `TransparenciaObjeto`. A API mantém o
JSON em `ItemNomeado.estilo` para compatibilidade.

## Limites atuais

Ainda faltam casos e leitura semântica para variações de degradê (cores
intermediárias, ponto médio e geometria), outros padrões, textura e cor spot. Esses
formatos não devem ser tratados como
preenchimento uniforme até haver casos controlados.
