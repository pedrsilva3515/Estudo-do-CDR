# Descobertas — tipos e geometria vetorial

Fontes: 33 casos controlados (`caso_00` a `caso_32`) e um documento real
externo com 13 objetos, dos quais 6 são curvas.

## V1. Código de tipo do objeto em `loda`

No blob `loda` pertencente a cada `LIST/obj `, o `uint32` no offset `+16`
identifica a classe do objeto:

| Código | Tipo |
|---:|---|
| 1 | retângulo |
| 2 | elipse |
| 3 | curva |
| 4 | texto |
| 5 | bitmap |

A soma por tipo produzida pelo parser coincidiu com as contagens `Rect`,
`Ellipse`, `Curve`, `Text` e `Bitmap` de `META-INF/metadata.xml` em todos os
33 casos controlados. No documento real, os 13 objetos foram classificados
como 6 bitmaps, 6 curvas e 1 texto, também iguais ao XML.

## V2. `bbox` e matriz também valem para vetores

Os casos controlados de movimento, redimensionamento e rotação mostram que
objetos vetoriais usam os mesmos blocos estruturais já encontrados para
bitmaps:

- `bbox`: caixa absoluta visível, em 10.000 unidades por milímetro;
- `trfd`: matriz afim absoluta `[a,b,tx,c,d,ty]`;
- rotação do eixo X: `atan2(c,a)`.

No `caso_25`, o parser recupera `30,000000°`, exatamente o ângulo aplicado
pela macro. Objetos filhos de grupo preservam suas próprias matrizes absolutas.

## V3. Vetor compacto dos objetos curva

Nos seis objetos de código 3 do documento real, os cinco últimos offsets da
tabela inicial de `loda` delimitam uma seção com tamanho exato:

```text
uint32 indice_logico
uint32 numero_de_pontos
int32  coordenadas[numero_de_pontos][2]  # todos os X/Y contíguos
uint8  flags[numero_de_pontos]           # um byte por ponto
```

Assim, o tamanho da seção é sempre `8 + 9 × numero_de_pontos`. Foram
decodificados, sem sobra ou falta de bytes, vetores com 193, 258, 843, 451,
463 e 632 pontos. Depois da matriz, os extremos das coordenadas acompanham o
`bbox`; pequenas diferenças são esperadas porque a caixa inclui o traçado e
uma curva Bézier pode ultrapassar seus nós/controles de maneiras diferentes.

O parser expõe `geometria_curva`, `numero_pontos`, cada tripla `x/y/flag` e
`pontos_curva_absolutos`.

### Nível de confiança e pendências

- O layout e as contagens são estruturalmente fortes, mas os seis exemplos de
  curva vêm do mesmo documento real. Falta um caso controlado criado como
  curva simples para validação independente.
- A semântica dos bits das flags ainda não foi fechada. Portanto, já podemos
  contar e localizar pontos, mas ainda não classificar com segurança cada
  ponto como nó, controle, cúspide, suave, início ou fechamento de subcaminho.
- A origem da régua/página varia entre documentos. Até o campo dessa origem
  ser localizado, não é seguro decidir “fora da página” comparando o `bbox`
  diretamente com `±largura/2` e `±altura/2`.
