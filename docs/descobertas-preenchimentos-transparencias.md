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

Para CMYK, as quatro componentes seguem o modelo e a paleta:
`CMYK,USER,C,M,Y,K,opacidade,identificador`. Para RGB, as três componentes
seguem `RGB255,USER,R,G,B,opacidade,identificador`.

## API disponível

`ItemNomeado.estilo_tipado` e `doc.estilos_tipados_da_pagina()` devolvem
`PreenchimentoObjeto`, `CorObjeto` e `TransparenciaObjeto`. A API mantém o
JSON em `ItemNomeado.estilo` para compatibilidade.

## Limites atuais

Ainda faltam casos e leitura semântica para preenchimento em degradê, padrão,
textura, cor spot e transparência graduada. Esses formatos não devem ser
tratados como preenchimento uniforme até haver casos controlados.
