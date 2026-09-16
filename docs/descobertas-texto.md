# Descobertas — texto e fontes

Fonte: `caso_11`, seis casos controlados novos (`caso_37` a `caso_42`) e
um documento real externo. Os casos isolam conteúdo, tamanho, família,
texto artístico, texto de parágrafo e dois objetos independentes.

## T1. Conteúdo textual em `META-INF/textinfo.xml`

Cada objeto textual aparece como um `TextStream`; seu conteúdo está em um
ou mais elementos `TextRun`. Os atributos observados incluem:

```xml
<TextRun break="para" lang="1046">Texto Alfa 123</TextRun>
```

`break="para"` separa parágrafos e `lang="1046"` representa o código de
idioma gravado pelo documento. O `caso_41`, com duas linhas em uma caixa de
parágrafo, produziu dois `TextRun` dentro do mesmo `TextStream`.

Nos casos com dois objetos na mesma página, duas páginas e texto dentro de
PowerClip, a ordem dos `TextStream` coincidiu com a ordem dos objetos de texto
em `root.dat`. `doc.textos_por_objeto()` usa essa correspondência somente
quando as contagens são idênticas; se divergirem, devolve `None` em vez de
produzir uma associação parcial.

## T2. Tipos de objeto

O campo de tipo em `loda +16` distingue:

- `4`: texto artístico;
- `6`: texto de parágrafo.

Ambos são expostos como `tipo_objeto="texto"`, preservando a contagem XMP, e
o novo campo `tipo_texto` informa `artistico` ou `paragrafo`.

## T3. Fonte, tamanho e atributos no bloco `txsm`

A folha `txsm` do objeto aponta para um bloco em `pageN.dat`/`dataN.dat` que
contém JSON textual. O dicionário `character.latin` inclui, entre outros:

- `font`, `version` e `charset`;
- `size`;
- `italic`, `underline`, `strikeout` e `weight`;
- preenchimento e contorno do texto.

O tamanho usa 10.000 unidades por milímetro, a mesma unidade geométrica:

```text
12 pt -> 42333
24 pt -> 84667
tamanho_pt = size / 10000 * 72 / 25,4
```

Texto artístico trouxe um JSON de estilo. O texto de parágrafo com duas
linhas trouxe dois estilos completos, um por parágrafo, ambos Arial 12 pt.
O parser expõe essa sequência como `objeto.estilos_texto`.

## T4. `fontTable.dat`, fontes auxiliares e incorporação

`font/fontTable.dat` contém nomes UTF-16LE, família PostScript, versão, estilo
e entradas por conjunto de escrita. Por isso, o resumo XMP pode listar fontes
auxiliares como `MS Gothic` mesmo quando o trecho latino usa Arial. Para a
fonte efetiva de um objeto latino, `txsm/character/latin/font` é a fonte mais
específica confirmada.

Arquivos de fonte incorporada aparecem em `embed/embeddingN`, mas ainda falta
decodificar a correspondência formal entre cada entrada da tabela e cada
embedding, além de distinguir incorporação completa e subconjunto.

## Implementação e limites atuais

- `doc.textos()` lê conteúdo, quebras e idioma de `textinfo.xml`.
- `doc.textos_por_objeto()` acrescenta página, caixa, matriz e estilo ao conteúdo.
- Objetos estruturais expõem `tipo_texto` e `estilos_texto`.
- Fonte e tamanho foram confirmados por mudanças isoladas e no arquivo real.
- A associação por ordem foi confirmada em três configurações controladas, mas
  ainda deve ser testada com texto em master page e variantes antigas do CDR.
- Ainda faltam estilos mistos dentro do mesmo parágrafo, texto excedente,
  kerning, alinhamento e detecção confiável de fonte ausente/substituída.
