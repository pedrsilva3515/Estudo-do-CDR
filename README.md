# Estudo do CDR — Engenharia Reversa do Formato ZCF

Projeto de engenharia reversa do formato `.cdr` moderno do CorelDRAW (ZCF — *ZIP Container Format*),
com o objetivo de produzir:

1. **Uma especificação técnica aberta** do formato interno (`root.dat`, `page*.dat`,
   `masterPage.dat`, `Bitmaps.dat`, `dataFileList.dat`), com offsets, cabeçalhos, tipos de
   registro, endianness e referências cruzadas — tudo baseado em evidência reproduzível.
2. **Uma biblioteca de leitura em Python** capaz de abrir um `.cdr` sem depender do CorelDRAW
   instalado, expondo páginas, layers, objetos, textos, curvas, bitmaps, cores e metadados.
3. **Pontos de integração** com a automação existente da gráfica (Kanban de produção,
   manifestos de job, validação de arquivos antes da fila de impressão).

## MVP de interpretação de pedidos

O primeiro contrato JSON para transformar montagens recebidas em pedidos
estruturados está documentado em
[docs/mvp-interpretacao-pedidos.md](docs/mvp-interpretacao-pedidos.md). O comando
`python -m zcfreader.cli pedido arquivo.cdr` extrai quantidades, dimensões,
componentes, modo de cor, DPI, alertas e pendências sem inventar informações
ausentes.

### Instalação em outro computador

Requer Python 3.10 ou mais recente. O parser não depende do CorelDRAW para abrir
arquivos CDR modernos no formato ZCF.

```powershell
git clone https://github.com/pedrsilva3515/Estudo-do-CDR.git
cd Estudo-do-CDR
git switch codex/mvp-interpretacao-pedidos
python -m pip install -e .
cdr-pedido pedido "C:\pedidos\arquivo.cdr" --saida pedido.json
```

Para usar a interface com arrastar e soltar:

```powershell
python -m pip install -e ".[gui,api]"
cdr-pedido-gui
```

Na janela **Configurar IA**, o operador pode baixar o modelo visual local
Qwen2.5-VL 3B quantizado (cerca de 2,77 GB, mais um runtime pequeno). O download
é feito pela própria aplicação, pode ser retomado depois de uma interrupção e é
validado antes de o modo local ser liberado. O modelo roda somente em CPU e foi
escolhido para os computadores da gráfica com 32 GB de RAM e sem placa de vídeo.
Também permanecem disponíveis o modo estrutural rápido e a análise opcional por
API, pela OpenAI ou pelo [OpenRouter](https://openrouter.ai). Com o OpenRouter,
uma única chave dá acesso a modelos de visão de vários fornecedores (Claude,
GPT, Gemini, Qwen); o campo de modelo aceita qualquer ID de
`openrouter.ai/models`. As requisições pedem somente provedores que não retêm
dados (`data_collection: deny`). A chave também pode vir da variável
`OPENROUTER_API_KEY`.

A leitura visual nunca substitui a lista de itens da leitura estrutural. Ela
preenche material e acabamento ausentes, acrescenta apenas instruções com
quantidade e medida lidas pelo OCR e registra o restante em
`sugestoes_visuais`, com alerta de revisão.

A mesma janela contém a opção **Ativar arquitetura regional experimental**.
Quando marcada, ela executa uma segunda leitura em paralelo, sem substituir os
itens do fluxo estável. O botão **Ver análise regional** mostra candidatos,
papel estrutural, quantidade, medidas, material, acabamento e evidências. Uma
falha nessa camada gera um alerta, mas não impede a entrega do resultado
principal. A opção vem desligada por padrão.

### Fluxo 0.7

A versão 0.7 trata o resultado estrutural como hipótese. A etapa visual recebe
textos nativos com suas posições, procura instruções convertidas em curvas,
repetições e documentos com materiais mistos, e pode criar, remover ou reagrupar
itens. Uma reconstrução só é aplicada quando todos os itens propostos possuem
quantidade e dimensões válidas; o resultado continua marcado para conferência.
Antes do modelo visual, um OCR local em CPU produz textos e caixas espaciais;
isso evita depender do modelo de linguagem para simplesmente transcrever uma
legenda nítida.

Quando o CorelDRAW está instalado, a aplicação abre uma instância invisível e
temporária para renderizar os objetos em alta resolução. O documento não é
salvo nem alterado. Sem CorelDRAW, o processamento continua usando o preview
embutido no CDR, com a limitação de resolução registrada no diagnóstico.

Na 0.7.1, a ordem passou a ser visual primeiro: o modelo cria um mapa sem
receber candidatos geométricos; em seguida o parser mede o CDR de forma
independente. Uma segunda consulta à IA só ocorre quando quantidade ou número
de produtos divergem. O reconciliador entende instruções regionais como
`30 UNI DE CADA`, descarta curvas abertas usadas como colchetes e padroniza as
unidades antes de comparar as leituras.

Na 0.7.2, toda linha do OCR que contenha simultaneamente quantidade e dimensões
passa a ser uma hipótese obrigatória quando não possui item correspondente no
mapa da IA. Ela força a adjudicação e pode recuperar textos convertidos em
curvas, como `4 UN (46,5X9)`. Na segunda passagem, uma diferença objetiva entre
o número de itens completos prevalece sobre um rótulo contraditório da IA como
`estrutura_confere: sim`. A seção auxiliar de instruções não é somada quando a
lista adjudicada já existe, evitando duplicações e falsos itens extraídos do
conteúdo interno da arte.

Na 0.7.3, o parser cria também um inventário geométrico profundo. Ele procura
produtos dentro de grandes grupos, detecta arte e contorno sobrepostos, consolida
repetições do mesmo tamanho, mede blocos numéricos e calcula a união de curvas
sem incluir os cabeçalhos de texto. A IA usa esse inventário como menu de
hipóteses, não como lista pronta. Se o modelo local devolver itens sem medidas
ou entrar em repetição, o reconciliador seleciona deterministicamente as caixas
externas e mantém o resultado marcado para revisão. O contrato local limita o
número e o tamanho dos campos para evitar respostas JSON truncadas.

O harness de regressão pode ser executado sobre os pacotes revisados:

```powershell
$env:PYTHONPATH="fase3-parser"
python scripts/avaliar_relatorios.py "$env:USERPROFILE\Documents\LeitorPedidosCDR\Relatorios"
```

Ele compara itens sem depender da ordem da tabela e mede quantidade, dimensões,
material, acabamento, total de unidades e correspondência integral.

Uma arquitetura de agente por candidatos identificados está sendo validada fora
do fluxo da aplicação. Ela preserva medidas determinísticas do CDR e usa visão
somente para selecionar produtos e resolver ambiguidades. Método, resultados de
hardware e critérios de decisão estão em
[docs/validacao-arquitetura-agente.md](docs/validacao-arquitetura-agente.md).

### Fluxo 0.9: agente em camadas (experimental)

No modo **Agente em camadas (OpenRouter)**, cada pedido passa por camadas cada
vez mais caras, e só avança quando a anterior não resolve com segurança:

1. **Regras regionais**, sem IA e sem custo: aceitas somente quando todas as
   peças são produtos confirmados com quantidade escrita.
2. **Modelo rápido** (padrão `google/gemini-3.1-flash-lite`).
3. **Modelo de reforço** (padrão `google/gemini-3.8-flash`): somente quando
   o modelo rápido faz perguntas, termina com erros de validação, não encontra
   itens ou contradiz uma regra confirmada.
4. **Operador**: perguntas restantes aparecem em **Ver perguntas**.

O agente (`zcfreader/agente.py`) recebe fatos que não pode alterar: peças
candidatas com ID e medida exata do CDR, textos numerados e a imagem com os
IDs desenhados. Ele escolhe IDs e cita o texto que prova cada quantidade e
material; um validador rejeita IDs inexistentes, peças contadas duas vezes,
quantidades ausentes do texto citado e materiais sem prova. As medidas nunca
vêm do modelo. Há limite de custo por pedido (US$ 0,08).

Convenções da gráfica podem ser escritas em
`%APPDATA%\LeitorPedidosCDR\regras_da_casa.md`, criado no primeiro uso.

Medição nos 11 pedidos revisados (22/09/2026):

| Caminho | Pedidos corretos | Custo médio por pedido |
|---|---:|---:|
| Regras regionais | 6/11 | — |
| Gemini 3.1 Flash Lite | 8/11 | US$ 0,004 |
| Gemini 3.8 Flash | 8/10 | US$ 0,018 |
| Camadas (simulação com respostas salvas) | 10/11 | US$ 0,0075 |

O corpus é pequeno e os mesmos casos orientaram o validador; os números
precisam ser confirmados em pedidos novos. Para medir:

```powershell
$env:PYTHONPATH="fase3-parser"
python scripts/avaliar_agente.py "$env:USERPROFILE\Documents\LeitorPedidosCDR\Relatorios" `
  --camadas google/gemini-3.1-flash-lite google/gemini-3.8-flash --orcamento-usd 0.15
```

### Revisão e diagnóstico

Depois de cada análise, a interface permite confirmar o resultado ou corrigir,
adicionar e excluir itens. A revisão gera automaticamente um pacote ZIP em
`Documentos/LeitorPedidosCDR/Relatorios`, contendo resultado original, resultado
correto, evidências estruturais, resposta visual, preview, diagnóstico e resumo.
O CDR original não é incluído por padrão e só entra no pacote quando o operador
marca essa opção. Um histórico local em JSONL registra os casos para futuras
avaliações e testes de regressão.

Quando a arquitetura regional experimental está ativa, a janela de correção
oferece **Comparar com análise regional**. O pareamento usa medidas do CDR e
desempata produtos de mesmo tamanho por quantidade e material. O operador pode
aplicar uma sugestão selecionada por vez. A aplicação pede confirmação, não
apaga campos que a leitura regional deixou vazios, não adiciona produto sem
quantidade de pedido confirmada e registra candidato e campos aplicados no
relatório.

Para atualizar uma cópia existente, execute `git pull` na mesma branch.

> Para continuar o trabalho em outro computador, comece por
> [docs/RETOMADA.md](docs/RETOMADA.md). O documento registra branch, comandos,
> estado dos testes, descobertas fechadas e o próximo estudo recomendado.

## Princípio metodológico

Nenhuma conclusão sobre o formato é declarada com base em um único arquivo. Um arquivo
permite formular hipóteses; confirmar exige comparar arquivos que diferem em **exatamente uma
característica por vez** e observar quais bytes mudam. Toda descoberta é documentada com nível
de confiança explícito (`confirmado por N casos` vs. `hipótese não testada`).

## Fases

| Fase | Entregável | Status |
|------|-----------|--------|
| 1 | Gerador de casos de teste (macro VBA para CorelDRAW 2025 OEM) | **Concluída** — 16/16 casos gerados sem falhas (Corel 26.0 build 101) |
| 1b | Casos extras para fechar hipóteses sobre múltiplos bitmaps | **Concluída** — 6/6 casos gerados sem falhas, incluindo a foto real (caso_21) |
| 2 | Motor de diferenças binárias (Python) | **Concluída** — 21 pares comparados, relatórios versionados |
| 3 | Parser incremental (Python) | **Em andamento** — bitmaps, páginas, PowerClip, layers, texto, contornos, curvas e preenchimentos uniformes/transparência uniforme já têm leitura e testes; degradês e padrões são o próximo bloco |
| 4 | Especificação pública + biblioteca instalável com testes | Não iniciada |

## Estrutura do repositório

```
docs/
  evidencias-amostra-helo.md   Evidências do arquivo de exemplo real (helo.cdr)
  descobertas-fase2.md         Descobertas confirmadas + hipóteses, com nível de confiança
  descobertas-fase1b.md        Descobertas dos casos 16-20 (multi-bitmap, dedup, CMYK, alfa)
  descobertas-fase3-page1.md   Descobertas sobre page1.dat (nomes, estilo JSON, chunks)
casos-de-teste/                67 .cdr controlados (caso_00–66) + manifestos JSON + imagens-fonte
ferramentas-estudo/            Gerador reproduzível dos casos avançados 28–66
fase1-gerador-casos/
  GeradorCasosZCF.bas          Macro VBA que gera os casos de teste + manifestos JSON
  README.md                    Instruções de instalação/execução da macro
fase2-diff-binario/
  zcf_diff.py                  Motor de diff binário entre pares de .cdr (ZCF)
  relatorios/                  Um relatório Markdown por caso de teste
  README.md                    Uso e limitações do motor
fase3-parser/
  zcfreader/                   Biblioteca Python (zero dependências) que extrai bitmaps
                                de um .cdr sem precisar do CorelDRAW instalado
  tests/                       Testes automatizados usando casos-de-teste/ como fixtures
  README.md                    Uso, o que está confirmado e limitações conhecidas
```

## Estado atual (resumo das descobertas)

Detalhes e contagem de amostras em [docs/descobertas-fase2.md](docs/descobertas-fase2.md)
e [docs/descobertas-fase1b.md](docs/descobertas-fase1b.md):

- **`Bitmaps.dat` decodificado em grande parte**: sequência plana de registros `UI`
  (um por imagem única — deduplicado, ver abaixo), cada um com um sub-registro `RI`
  aninhado (tag 2 bytes + tamanho, sem padding) contendo largura, altura, bpp, stride,
  tamanho dos pixels e resolução (px/metro × 1000). Pixels gravados **descomprimidos**
  em todos os casos sintéticos testados, inclusive JPEG de 2400×2400 px.
- **Deduplicação confirmada**: o mesmo bitmap usado 2× no documento gera 1 único
  registro `UI` — a 2ª instância é só uma referência em `page1.dat`. Explica em grande
  parte o "24 bitmaps reportados vs. poucos registros UI" do helo.cdr.
- **Transparência (alfa) é um 2º `RI`** (máscara em escala de cinza) aninhado dentro do
  mesmo `UI`, não um 4º canal RGBA. CMYK usa 32 bpp (4 × 8 bits) num único `RI`.
- **Objetos e relações estruturais vivem em `pageN.dat`, `dataN.dat` e `root.dat`** —
  conteúdo de PowerClip fica em `dataN.dat` e é ligado ao recipiente pelo índice
  RIFF de `root.dat`; mover ou duplicar um bitmap não altera um byte do `Bitmaps.dat`.
- Texto embute a fonte (`font/fontTable.dat` + `embed/embedding0`); página nova cria
  `page2.dat` + preview + entrada no `dataFileList.dat`.
- **Pendência resolvida:** os "JPEGs embutidos" do helo.cdr eram coincidência estatística
  em dados de pixel bruto de alta entropia, não um segundo modo de armazenamento —
  confirmado importando uma foto real de câmera (`caso_21`) e reanalisando os 4 blocos do
  helo.cdr com verificação de marcador JPEG válido. **Todo bitmap testado até agora,
  sintético ou real, é armazenado como pixels descomprimidos.**
- **Fase 3 iniciada:** a biblioteca `zcfreader` (`fase3-parser/`) já extrai bitmaps de
  qualquer `.cdr` real como PNG, sem o CorelDRAW instalado — validada contra os 21 casos
  de teste e contra o `helo.cdr` original (4 imagens extraídas corretamente). No processo,
  uma regra de formato documentada na Fase 1b (tamanho do registro `RI`) se mostrou
  errada sob teste automatizado e foi corrigida — ver `docs/descobertas-fase1b.md`.
- **`page1.dat` parcialmente decodificado:** as propriedades de preenchimento/contorno/
  transparência de cada objeto são gravadas como **JSON em texto puro** (não binário),
  e nomes de layers/objetos aparecem em UTF-16LE — ambos já extraíveis pela biblioteca.
  A geometria vetorial detalhada (como os pontos das curvas) continua aberta, mas a
  hierarquia, caixa e matriz dos objetos já são obtidas por `root.dat` — ver
  `docs/descobertas-fase3-page1.md` e `docs/descobertas-estrutura-root.md`.
- **Ligação instância → imagem única confirmada:** descritores em `pageN.dat` ou
  `dataN.dat` carregam largura/altura/bpp e um identificador que aponta para o prefixo
  do registro `UI` correspondente em `Bitmaps.dat`. `doc.instancias_bitmaps()` já
  diferencia quantidade de objetos bitmap e quantidade de imagens únicas, inclusive
  deduplicação e conteúdo dentro de `dataN.dat` — ver
  `docs/descobertas-referencias-bitmaps.md`.
- **Árvore de objetos e geometria de bitmap:** `root.dat` foi identificado como um
  índice RIFF que descreve páginas, layers, grupos e objetos e aponta para `loda`,
  `bbox` e `trfd` nos membros de dados. Isso liga cada instância ao objeto dono e
  confirma matriz absoluta, tamanho visível e DPI efetivo — ver
  `docs/descobertas-estrutura-root.md`.
- **Tipos e curvas vetoriais:** o campo de tipo em `loda` distingue retângulo,
  elipse, curva, texto e bitmap. O parser separa segmentos retos/Bézier, pontos
  de controle, múltiplos subcaminhos e caminhos abertos/fechados. A conferência
  `doc.curvas_com_subcaminhos_abertos()` já sinaliza objetos problemáticos — ver
  `docs/descobertas-geometria-vetorial.md`.
- **Página, sangria e objetos fora do corte:** o cabeçalho de `data1.dat`
  fornece tamanho padrão e sangria; páginas com tamanho próprio têm um bloco
  estrutural de 68 bytes em `pageN.dat`. O parser já sinaliza objetos que saem
  do corte e distingue se permanecem dentro da sangria — ver
  `docs/descobertas-paginas-limites.md`.
- **PowerClip → página:** o campo de vínculo do recipiente aponta para o grupo
  `clpt` de conteúdo. A página agora é propagada também por PowerClips aninhados,
  incluindo objetos armazenados em `dataN.dat`.
- **Texto e fonte:** `META-INF/textinfo.xml` fornece conteúdo, parágrafos e idioma;
  o bloco estrutural `txsm` fornece fonte, tamanho e atributos por objeto. Textos
  artísticos e de parágrafo já são distinguidos — ver
  `docs/descobertas-texto.md`.
- **Layers e impressão:** `LIST/layr` fornece nome, hierarquia e flags de
  visibilidade, impressão e bloqueio. Objetos dentro de PowerClip também recebem
  a layer do recipiente — ver `docs/descobertas-layers.md`.
- **Contornos:** largura física, linha fina, cor, tracejado, pontas, junções,
  alinhamento, escala, sobreimpressão e setas já são lidos por objeto — ver
  `docs/descobertas-contornos.md`.
- **Metadados de pre-flight sem engenharia reversa binária:**
  `META-INF/metadata.xml` fornece tamanho nominal da página, orientação, número de
  páginas/layers, contagens por tipo de objeto e efeito, fontes usadas e versão do
  CorelDRAW. `zcfreader` já lê o núcleo desses campos por `doc.metadados()` — ver
  `docs/descobertas-metadata.md`. Em documentos com páginas de tamanhos diferentes,
  o XML ainda precisa de um caso controlado para definir qual página o resumo representa.
