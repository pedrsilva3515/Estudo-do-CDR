# Descobertas — contornos

Fonte: oito casos controlados (`caso_49` a `caso_56`) gerados pelo
CorelDRAW 26.0, mais o documento real externo. Foram isolados ausência,
largura, tracejado, pontas/junções e escala com o objeto.

## C1. Propriedades em JSON

O `loda` do objeto contém um JSON textual com a chave `outline`. Texto usa a
mesma estrutura dentro de `txsm/character/outline`. Campos confirmados:

```text
width             largura
color             especificação de cor
dashDotSpec       sequência do tracejado
endCaps           código das pontas
joinType          código das junções
scaleWithObject   escalar junto com o objeto
overprint         sobreimpressão
```

## C2. Unidade da largura

Mudanças controladas e releitura pelo Corel confirmaram 10.000 unidades por
milímetro no JSON:

```text
0,2 mm -> 2000
0,5 mm -> 5000
1,0 mm -> 10000
```

`ContornoObjeto.largura_mm` faz essa conversão diretamente.

## C3. Ausência não é hairline

`SetNoOutline()` e atribuir largura zero produziram o mesmo estado: tipo de
contorno zero no Corel e `width="0"` no JSON. Portanto, largura zero é tratada
como ausência, não como hairline. Ainda é necessário gerar um hairline real
pela interface/propriedade específica antes de definir sua representação.

## C4. Demais campos

- O segundo estilo de linha produziu `dashDotSpec="2,1,3"`.
- Ativar escala gravou `scaleWithObject="1"`.
- Alterar pontas e junções para o código 1 gravou `endCaps="1"` e
  `joinType="1"`.
- Contorno sólido padrão omite esses campos; o parser usa zero/falso.

Casos adicionais fecharam os códigos expostos pela biblioteca de tipos do
Corel e confirmados no JSON:

| Campo | 0 | 1 | 2 |
|---|---|---|---|
| `justification` | centro | interno | externo |
| `endCaps` | reta | arredondada | quadrada |
| `joinType` | mitra | arredondada | chanfrada |

Setas não são gravadas apenas por índice. `leftArrow` e `rightArrow` contêm
uma descrição geométrica iniciada por comandos como `M`, `L` e `C`, seguida
por um identificador depois de `|`. O parser preserva a especificação inteira.

### Linha fina (hairline)

O comando nativo `OnPenHair` do Corel gera `width=762` no JSON, equivalente
a `0,0762 mm` ou exatamente `0,003 pol`. Ao reabrir o arquivo, a automação do
próprio Corel informa contorno presente (`Type=1`) e largura `0.003` em
polegadas. Portanto, linha fina não é largura zero: `width=0` continua sendo
ausência de contorno. `ContornoObjeto.linha_fina` expõe essa distinção.

## Resultado no documento real

Os 13 objetos tiveram estilo de contorno decodificado, incluindo o texto.
Todos estão sem contorno (`width=0`), sem tracejado e sem sobreimpressão.

## Implementação e pendências

- `objeto.contorno` expõe presença, largura, cor, tracejado, escala, pontas,
  junção e sobreimpressão.
- O caso 99 confirmou o contorno caligráfico: `nibAngle` e `nibStretch` são
  expostos como `angulo_caligrafico` e `aspecto_caligrafico`.
- O caso 100 confirmou nós de largura variável. O campo
  `variableAttributes` usa grupos separados por `|`: posição normalizada,
  largura dos dois lados (em unidades de 1/10.000 mm) e uma flag. A API
  expõe cada grupo como `NoLarguraVariavel` em `contorno.larguras_variaveis`.
- O caso 101 confirmou `miterLimit`; ele é convertido para
  `contorno.limite_mitra` como número decimal.
- O caso 102 confirmou ajustes de seta. `leftArrowAttributes` e
  `rightArrowAttributes` trazem, separados por `|`, comprimento e largura em
  unidades nativas, deslocamentos, espelhamentos horizontal/vertical e
  rotação em milionésimos de grau. A API os expõe em `OpcoesSeta`.
- A caixa `bbox` observada descreve a geometria do objeto e não mudou com a
  largura nesses casos; não se deve usá-la para inferir a espessura.
