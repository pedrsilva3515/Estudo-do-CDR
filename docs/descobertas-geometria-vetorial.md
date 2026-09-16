# Descobertas — tipos e geometria vetorial

Fontes: 33 casos controlados iniciais (`caso_00` a `caso_32`), cinco casos
controlados específicos de curvas (`caso_62` a `caso_66`) e um documento real
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

## V4. Segmentos, subcaminhos e fechamento

Os casos 62–66 isolam curva aberta, curva fechada, dois subcaminhos mistos,
dois subcaminhos abertos e um segmento Bézier. Os dois bits superiores de
`flag` identificam o papel do ponto:

| Máscara `flag & 0xC0` | Papel |
|---:|---|
| `0x00` | início de subcaminho |
| `0x40` | fim de segmento reto |
| `0x80` | fim de segmento Bézier |
| `0xC0` | ponto de controle Bézier |

O bit `0x08` aparece no início e no último ponto de um subcaminho fechado. O
último ponto repete as coordenadas do primeiro. Um subcaminho aberto não usa
esse bit. Isso também separa vários subcaminhos dentro do mesmo objeto, mesmo
quando todos estão abertos.

O parser agora expõe `geometria.subcaminhos`, `numero_subcaminhos`,
`possui_subcaminho_aberto`, `subcaminho.fechado`, `ponto.papel` e
`ponto.marca_fechamento`. `doc.curvas_com_subcaminhos_abertos()` entrega
diretamente os objetos problemáticos para uma conferência automatizada.

No arquivo real “Debora ellen fdf.cdr”, as seis curvas somam 12 subcaminhos
(1, 1, 6, 2, 1 e 1 por objeto), todos fechados. Portanto, esse arquivo não
tem curva aberta entre os objetos vetoriais decodificados.

### Nível de confiança e pendências

- O layout, a contagem de pontos, os tipos de segmento e o fechamento agora
  têm casos controlados independentes.
- Os bits inferiores que diferenciam nó cúspide, suave e simétrico ainda não
  foram fechados; o parser preserva a flag bruta.
- A origem da régua/página varia entre documentos. Até o campo dessa origem
  ser localizado, não é seguro decidir “fora da página” comparando o `bbox`
  diretamente com `±largura/2` e `±altura/2`.
