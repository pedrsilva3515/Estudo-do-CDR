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

## Resultado no documento real

Os 13 objetos tiveram estilo de contorno decodificado, incluindo o texto.
Todos estão sem contorno (`width=0`), sem tracejado e sem sobreimpressão.

## Implementação e pendências

- `objeto.contorno` expõe presença, largura, cor, tracejado, escala, pontas,
  junção e sobreimpressão.
- Ainda faltam hairline real, setas, alinhamento interno/externo, contorno
  caligráfico/variável e confirmação dos enums de pontas/junções.
- A caixa `bbox` observada descreve a geometria do objeto e não mudou com a
  largura nesses casos; não se deve usá-la para inferir a espessura.
