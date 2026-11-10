<!--
Regras da casa: convenções desta gráfica que o agente deve seguir.
Escreva uma regra por linha, em linguagem natural.
Tudo o que estiver fora deste comentário é enviado ao modelo.
Revisadas com o operador em 22/10/2026 e 10/11/2026.
-->

QUANDO PERGUNTAR
- Pergunte ao operador só quando o arquivo permite duas respostas diferentes e nada nele decide (ex.: dois textos de quantidade sobrepostos, "100UN" em cima de "150UN"). Não pergunte o que estas regras já respondem.
- Quando um texto responde, preencha o campo com o que está escrito, mesmo que você também registre um aviso. Deixe vazio só o que não está escrito em lugar nenhum e não tem padrão abaixo.

GRADE MONTADA
- Quando o cliente manda muitas peças pequenas da mesma medida (6 ou mais, de até uns 15 cm) já montadas lado a lado, iguais ou diferentes, é UMA grade: 1 linha, quantidade 1, medida da grade inteira (use medir_uniao com todas as peças).
- Quando o cliente manda UMA peça e escreve a quantidade ("50 unidades", "100 adesivos"), é quantidade x medida da peça.
- Peças grandes repetidas (faixas, placas, artes diferentes de 20 cm ou mais) contam uma a uma.
- A mesma grade desenhada duas vezes no mesmo lugar (camada de impressão e camada de corte) e o contorno da folha em volta dela são a mesma grade, não itens a mais.

O QUE NÃO É PRODUTO
- Faca de recorte: contorno em vetor, sem preenchimento, ao lado ou em volta da arte (às vezes na cor "CutContour"). Pode vir de formas variadas. Não é um item: serve de contorno da arte. Se houver faca, a MEDIDA do item é a da faca (ela costuma ser maior que a arte por causa da borda branca), não a da arte. A faca NÃO quer dizer que a gráfica vai recortar: às vezes o cliente recorta em casa.
- Fundo da montagem, contorno da folha, legendas, cabeçalhos, telefone e nome de quem montou o arquivo não são produtos.

QUANTIDADE
- Sem quantidade escrita e com uma peça só: 1 (padrão da gráfica).
- "N de cada" vale N para cada peça desenhada.
- A quantidade escrita vale mais que o desenho: o cliente costuma desenhar UMA peça e escrever quantas quer. "02 VINIL", "03 UNID", "550 unidades" com uma peça desenhada = 2, 3, 550 unidades dessa peça. Não pergunte; use o número escrito. "1.100UND" = 1100.
- Um texto de quantidade junto de cada cópia ("5 UN" em cima de uma placa, "12 UN" em cima da outra igual): o pedido é a soma.
- Item escrito e não desenhado ("ads recortados 4x4 100und" sem nenhuma peça de 4x4 no arquivo): é um item do pedido. Liste com ids vazio, medida_escrita com a medida do texto e a quantidade escrita; a arte vem depois com o cliente.

MATERIAL (use os nomes do Portal Flow)
- Adesivo Leitoso Interm., Adesivo Fosco, Adesivo Transparente, Adesivo Blackout, Adesivo Fosco Blackout, Adesivo Perfurado, Papel Outdoor, Lona Brilho 440g, Lona Fosca, PS 1 mm, PS 2 mm, Material do Cliente (Adesivo, Lona, Prismático).
- "Adesivo" ou "vinil" sem tipo: Adesivo Leitoso Interm. Não pergunte.
- Nada escrito sobre o material da peça: Adesivo Leitoso Interm. (padrão da gráfica), com texto_material null.
- Um título de material ("VINIL FOSCO", "ADESIVOS", "Paineis outdoor") vale para todas as peças da coluna abaixo dele, não só a primeira fileira.
- Erros de digitação são comuns: "ADEIVO" = adesivo, "SEM CROTE" = sem recorte, "trasparente"/"tranparente" = transparente, "painel oudoor"/"outdor" = Papel Outdoor.
- PS sem espessura escrita: PS 2 mm. Não pergunte.
- Prismático (branco ou amarelo): Material do Cliente Prismático Branco / Amarelo.
- "Brilhoso" (vinil/adesivo brilhoso): Adesivo Leitoso Interm.
- "Branco fosco": Adesivo Fosco. "Branco fosco blackout": Adesivo Fosco Blackout.
- "Painel", "panel" ou "outdoor" no nome do arquivo: Papel Outdoor. Na arte, "outdoor" sozinho pode ser só o tema.
- "Banner": Lona Brilho 440g com acabamento Banner. "Lona" sem tipo: Lona Brilho 440g. "Lona fosca": Lona Fosca.
- "Super cola": não decida, pergunte ao operador.
- Arquivo com vários produtos ("lona e adesivos", "paineis e adesivo"): o material de cada peça vem do texto mais próximo dela; o nome do arquivo não vale para todas.

ACABAMENTO
- Só informe um acabamento quando ele estiver escrito: num texto do arquivo, em letras convertidas em curvas ou no nome do arquivo. A informação às vezes vem só no e-mail ou no WhatsApp, que você não vê: sem nada escrito ao seu alcance, o acabamento é nenhum (sem recorte). Nunca deduza o recorte pela faca, pela borda branca ou pelo formato da peça.
- "Recortado", "com recorte", "com corte", "+ corte", "ads recortados": Recorte. Não pergunte se é recorte eletrônico: Recorte é o recorte eletrônico. "Sem recorte": sem acabamento.
- "Somente recorte", "corte especial", "refilado", "ilhós", "verniz", "laminação": use o nome correspondente do Portal Flow.
