# Visão do produto e roteiro de arquitetura

Registrado em 23/09/2026, a partir da análise do estado da v0.9 e dos objetivos do
dono do projeto. Este documento orienta decisões; não descreve o que já existe.

## Objetivo

No futuro, a aplicação deve:

1. identificar o pedido recebido (arquivo CDR montado pelo cliente);
2. **acertar o máximo possível**, para que a produção seja agilizada;
3. falar com o cliente (WhatsApp ou e-mail) **somente quando for de fato necessário**:
   informação faltando ou ambiguidade real;
4. exportar para um arte-finalista, que revisa;
5. mandar para a produção.

Não é preciso acertar 100%. É preciso acertar muito **e saber quando não acertou**.
A mensagem ao cliente é a exceção, não a regra.

## O que está certo e deve ser mantido

- **Leitor de CDR sem CorelDRAW** (`zcfreader`). É o ativo mais valioso: qualquer
  automação no servidor depende dele, porque não pode haver um CorelDRAW aberto.
- **Fatos do arquivo, IA só decide, humano confirma.** Medidas vêm do CDR; a IA
  escolhe peças e cita a evidência; o validador rejeita o que não tem prova.
- **Medição com pedidos reais revisados.** Cada revisão gera um pacote em
  `Documentos/LeitorPedidosCDR/Relatorios`, usado pelo avaliador
  (`scripts/avaliar_caminhos.py`, `scripts/avaliar_agente.py`).

## O que precisa mudar

### 1. Confiança calibrada é o centro do produto

Como a mensagem ao cliente só deve sair quando necessária, o sistema precisa
separar, **por campo** (peça, medida, quantidade, material, acabamento):

- *certeza*: segue direto para o arte-finalista;
- *dúvida*: vira uma pergunta objetiva.

Hoje já existem sinais para isso (validador, escalonamento em camadas, perguntas
do agente, contradição com regras). Falta medir a **calibração**: quando o sistema
diz "certeza", com que frequência está certo. Meta: nas decisões marcadas como
certeza, o erro precisa ser raro o bastante para dispensar revisão campo a campo.

Métrica a acrescentar ao avaliador: para cada campo, precisão entre os marcados
como certos e proporção de pedidos que dispensariam contato com o cliente.

### 2. O cliente como validador, só na exceção

Quando houver dúvida, a mensagem deve:

- resumir o que foi entendido ("15 adesivos redondos 4 × 4 cm e 15 retangulares
  20 × 11 cm, adesivo recortado");
- fazer só as perguntas necessárias ("Qual o material do banner: lona ou adesivo?").

Cada resposta do cliente vira caso de teste sem custo adicional.

### 3. Motor separado da interface; de desktop para serviço

O fluxo final tem várias pessoas e etapas (entrada, atendimento, arte-finalista,
produção). Isso pede um **serviço com fila de pedidos** e telas no navegador, não um
programa de desktop que depende de alguém soltar o arquivo.

- **Motor** (leitor, agente, validador, camadas): continua em Python e vira serviço.
- **Telas**: página web de fila e revisão, compartilhada por atendimento e
  arte-finalista.
- A interface Tkinter atual (mais de 1.500 linhas) serve para testes; não deve
  receber lógica de negócio nova.

### 4. Consolidar os caminhos de interpretação

Existem cinco modos: estrutural, visual 0.7, modelo local 3B, regional
experimental e camadas. Consolidar no **fluxo em camadas** e remover os demais
depois que a medição confirmar que nada se perde.

### 5. Integrar com o que a gráfica já usa

- **Portal Flow (Birô Digital)**, sistema de ordens de serviço: o pedido aprovado
  deve virar uma OS lá, se houver API ou importação.
- **Entrada estruturada**: pedidos feitos por formulário (há um protótipo de
  portal em `Documentos/ChatGPT/Aplicação de Pedidos`, com BotConversa) não
  precisam de interpretação. O leitor de CDR cobre o que chega sem estrutura.

### 6. Plugin no CorelDRAW para o arte-finalista (a avaliar)

Um docker no CorelDRAW lê os objetos com fidelidade total pelo modelo do próprio
programa (PowerClip, faca de corte, cores especiais) e pode marcar as peças
aprovadas e enviar para produção. Complementa o leitor próprio, que continua
necessário para a entrada automática.

## Roteiro por etapas

Cada etapa entrega valor sozinha e confirma se a próxima vale a pena.

1. **Agora — testes e precisão.** Continuar gerando pacotes de revisão (com o
   motivo do erro e a peça certa indicada na página) e corrigir as causas. Medir
   a calibração da confiança.
2. **Texto de confirmação/perguntas no app**, copiado manualmente para o
   WhatsApp, só nos pedidos com dúvida. Mede quantos pedidos dispensam contato.
3. **Consolidar o motor**: um fluxo só, motor separado da interface.
4. **Serviço com fila e tela web**, com aprovação humana antes de qualquer envio.
5. **Integrações**: WhatsApp/e-mail na entrada, Portal Flow na saída.
6. **Envio automático das mensagens**, só quando a calibração justificar.

## Custos

- API: centavos por pedido no fluxo em camadas (média medida de US$ 0,0075 nos
  pedidos revisados; US$ 0,0039 no `4_etapa.cdr`). Definir limite de gasto por
  chave no OpenRouter.
- O investimento real é tempo de desenvolvimento e manutenção; por isso as etapas
  começam pelas mais baratas que validam a ideia.

## Perguntas em aberto

1. Como os pedidos chegam hoje (WhatsApp, e-mail) e em que volume diário?
2. O Portal Flow tem API ou importação de pedidos?
3. Quantas pessoas participam entre receber o pedido e mandar para a produção?
