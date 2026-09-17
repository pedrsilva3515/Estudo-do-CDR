# MVP — interpretação de pedidos em CDR

O primeiro incremento transforma um arquivo CDR em um JSON auditável. Ele
combina o conteúdo textual do documento com a geometria dos objetos e mantém
origem e confiança de cada informação. Campos ausentes não são inventados.

## Uso

```powershell
$env:PYTHONPATH = "fase3-parser"
python -m zcfreader.cli pedido "C:\pedidos\arquivo.cdr"
python -m zcfreader.cli pedido "C:\pedidos\arquivo.cdr" --saida pedido.json
```

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
desduplicadas. Cada bitmap é associado à quantidade mais próxima no eixo
horizontal. Isso também permite representar como um único conjunto várias
peças lado a lado que compartilham uma quantidade.

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

