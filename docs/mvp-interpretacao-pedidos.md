# MVP — interpretação de pedidos em CDR

O primeiro incremento transforma um arquivo CDR em um JSON auditável. Ele
combina o conteúdo textual do documento com a geometria dos objetos e mantém
origem e confiança de cada informação. Campos ausentes não são inventados.

## Estado do MVP

- [x] abrir CDR/ZCF sem depender do CorelDRAW;
- [x] ler textos nativos, quantidades, bitmaps, dimensões, cor e DPI;
- [x] produzir JSON com evidências, alertas e pendências;
- [x] agrupar composições por proximidade em dois eixos e contorno externo;
- [x] interpretar instruções globais e locais de material/acabamento;
- [ ] gerar preview e aplicar OCR a textos convertidos em curvas;
- [x] disponibilizar tela inicial de revisão para o operador;
- [ ] permitir correção manual dos campos antes da exportação.

O primeiro marco é deliberadamente conservador: o resultado automático ainda
não deve liberar um pedido para produção sem revisão humana.

Na versão 0.2, retângulos, curvas externas, símbolos, bitmaps e grupos isolados
formam candidatos de arte. Objetos internos contidos são descartados, textos de
quantidade são associados um a um pela distância em dois eixos, e peças sem
quantidade explícita são contadas pelas composições. Instruções que contêm sua
própria quantidade têm escopo local; as demais são aplicadas como escopo global.
Peças sem quantidade escrita, mas com o mesmo tamanho e material, podem ser
consolidadas com confiança reduzida e indicação explícita no JSON.

## Uso

```powershell
$env:PYTHONPATH = "fase3-parser"
python -m zcfreader.cli pedido "C:\pedidos\arquivo.cdr"
python -m zcfreader.cli pedido "C:\pedidos\arquivo.cdr" --saida pedido.json
```

Interface gráfica:

```powershell
python -m pip install -e ".[gui]"
cdr-pedido-gui
```

Para construir um executável do Windows, execute
`powershell -ExecutionPolicy Bypass -File scripts/build_gui.ps1`. O resultado
fica em `dist/Leitor-de-Pedidos-CDR.exe`.

O relatório inicial contém:

- quantidade e texto de origem;
- dimensões físicas da arte ou do conjunto;
- componentes bitmap, dimensões em pixels, espaço de cor e DPI efetivo;
- modo de cor e intento de renderização do documento;
- alertas objetivos, inicialmente RGB em documento CMYK e bitmap abaixo de
  150 DPI;
- pendências, como material não informado;
- limitações que exigem conferência visual.

## Como os itens são formados

Textos com formas como `1und`, `2 un`, `3 unidades` ou `qtd: 5` são
reconhecidos como quantidade. Cópias exatamente sobrepostas são
desduplicadas. Cada composição é associada a no máximo um texto de quantidade,
considerando a distância nos dois eixos. Quando não há quantidade escrita, as
composições são contadas e podem ser consolidadas por tamanho e material.

Essa associação é uma hipótese explícita do MVP e precisa aparecer para
confirmação na interface. Ela não deve disparar produção automaticamente.

## Próxima etapa: visão

Textos convertidos em curvas não aparecem em `textinfo.xml`. Alguns materiais
e observações também podem existir somente dentro de imagens. A próxima etapa
deve:

1. extrair `metadata/thumbnails/thumbnail.bmp` ou renderizar a área total;
2. usar OCR/visão para propor textos e regiões;
3. cruzar cada região com as caixas e medidas confirmadas pelo parser;
4. preencher apenas valores com evidência e nível de confiança;
5. pedir confirmação do operador para material, acabamento ou associações
   ambíguas.

O parser estrutural continua sendo a fonte para medidas, DPI, modo de cor e
propriedades técnicas. Visão serve para interpretar a intenção visual, não
para substituir medidas disponíveis no CDR.
