# Validação da arquitetura de agente visual

Data: 19/09/2026
Estado: experimento separado; o fluxo do aplicativo v0.7.3 não foi alterado.

## Hipótese avaliada

Em vez de pedir que um modelo visual reconstrua sozinho todo o pedido, o CDR é transformado em um catálogo auditável de hipóteses geométricas. A visão seleciona IDs; largura e altura continuam vindo do arquivo. Hipóteses internas permanecem disponíveis para uma segunda consulta, sem competir com produtos inteiros na primeira imagem.

## Corpus

- 11 CDRs únicos com revisão do operador, obtidos dos relatórios da aplicação.
- 31 linhas de produto esperadas.
- Gabaritos locais podem complementar revisões mais recentes sem incorporar arquivos ou dados de clientes ao repositório.

## Resultado 1: teto geométrico

O catálogo de objetos prontos encontrou geometrias compatíveis para 30 das 31 linhas esperadas: **96,77%**.

O item inicialmente ausente era 47,2 x 102,1 cm em `MATERIAL_DA_REAL_FARMA_1.cdr`. A revisão do processo mostrou que essa caixa não existia como grupo no arquivo original: o operador agrupou os objetos soltos abaixo de “ADESIVOS BRANCO RECORTADOS / DO MESMO TAMANHO” para enviá-los juntos ao recorte.

Foi acrescentado experimentalmente o conceito de **bloco de produção derivado**. O detector:

- reconheceu a moldura que organiza a informação;
- separou as duas linhas de instrução;
- selecionou os 14 objetos produtivos posicionados abaixo delas;
- calculou a união desses objetos, sem incluir cabeçalho ou moldura.

O resultado foi **47,2105 x 102,1072 cm**, diferença total de apenas 0,17 mm em relação ao gabarito arredondado. Nenhum dos outros dez pedidos gerou um bloco derivado falso. Com hipóteses prontas e derivadas, a cobertura passou para **31 de 31 linhas (100%)**.

O teste considera separadamente:

- quantidade geométrica: quantas ocorrências estão desenhadas na montagem;
- quantidade do pedido: quantas unidades devem ser produzidas.

Essa distinção é necessária em arquivos como o Vinil Fosco, onde existe uma arte de cada tamanho, mas o pedido é 30, 30 e 60 unidades.

## Resultado 2: redução de ruído

A hierarquia por contenção preserva o catálogo completo, mas expõe primeiro apenas composições externas e filhos significativos.

No caso `VINIL SUPER COLA - TSCAR 014.cdr`, a primeira rodada caiu de 39 hipóteses para 4. Ícones, logotipos e partes internas deixaram de competir diretamente com os dois agrupamentos de produto. O modelo pode solicitar os filhos de uma composição quando precisar investigar detalhes.

## Resultado 3: modelo local de 3B como agente único

Máquina do ensaio: AMD Ryzen 7 5700G, 8 núcleos/16 threads, 29,9 GB de RAM utilizável, sem GPU dedicada. Modelo: Qwen2.5-VL 3B Q4_K_M em CPU.

| Caso | Candidatos total/expostos | Tempo | Pico de RAM do processo | Linhas exatas |
|---|---:|---:|---:|---:|
| Super Cola | 39 / 4 | 78,06 s | 4.918 MB | 1 / 3 |
| adesivoss | 10 / 10 | 80,41 s | 4.897 MB | 1 / 6 |
| Vinil Fosco | 3 / 3 | 76,22 s | 4.907 MB | 1 / 3 |
| **Total** |  | **234,69 s** | **4.918 MB** | **3 / 12** |

Conclusão: o hardware suporta confortavelmente o modelo atual, mas o modelo de 3B não deve ser o cérebro único. Mesmo com medidas exatas e candidatos reduzidos, ele omitiu produtos e associou quantidades à região errada.

## Observação sobre OCR

O OCR local leu corretamente, com alta confiança, instruções centrais dos casos explícitos:

- `4 UN (37X24,5 CM)` e `12 UN (46,5X9 CM)` no Super Cola;
- `30 UNI DE CADA` e `60 UNI` no Vinil Fosco.

Uma marcação de candidato sobre o texto ocultou o primeiro caractere de uma linha do Super Cola. Portanto, OCR deve rodar na imagem original antes de qualquer anotação. A associação quantidade/tamanho deve usar posição e abrangência regional; a IA entra somente quando essas regras deixam mais de uma solução plausível.

## Resultado 4: associação regional determinística

O protótipo passou a converter as caixas do OCR para as coordenadas físicas do CDR e aplicar três regras auditáveis:

- dimensão explícita seleciona uma hipótese com a mesma medida, priorizando a quantidade geométrica compatível;
- `N DE CADA` aplica a quantidade às artes abaixo abrangidas horizontalmente pela instrução;
- quantidade isolada seleciona a arte imediatamente abaixo com sobreposição horizontal.

No corpus completo, foram emitidas **7 associações, todas corretas e nenhuma falsa**:

- 1 no Vinil Transparente: `9 UN (23,4X18,4 CM)`;
- 3 no Super Cola: `4 UN (37X24,5 CM)`, `4 UN (46,5X9)` e `12 UN (46,5X9 CM)`;
- 3 no Vinil Fosco: 30 unidades para cada uma das duas artes abrangidas e 60 para a terceira.

Os outros oito arquivos não receberam associação regional automática. Isso é intencional: sem uma instrução reconhecida e uma relação espacial inequívoca, o protótipo se abstém. As sete linhas resolvidas representam precisão de 100% neste corpus, não conclusão automática das 31 linhas. A execução do OCR e das regras nos 11 arquivos levou cerca de 47 segundos no total, aproximadamente 4,3 segundos por pedido.

## Arquitetura recomendada após o ensaio

1. Extrair preview, nome, textos nativos, cores e todas as caixas do CDR.
2. Rodar OCR na imagem original, preservando polígonos e confiança.
3. Construir candidatos medíveis e uma hierarquia de composição/detalhe.
4. Derivar blocos operacionais pela união de objetos quando uma instrução e uma região delimitada definirem o conjunto, mesmo que o cliente não o tenha agrupado.
5. Associar deterministicamente instruções a candidatos por dimensão, proximidade, alinhamento e abrangência (`de cada`, colchetes e grupos).
6. Abrir uma tarefa visual pequena somente para regiões ambíguas. O modelo escolhe IDs existentes; não fornece medidas livres.
7. Aplicar validações de consistência: área escrita, quantidade desenhada, quantidade pedida, duplicidade e soma.
8. Mostrar ao operador a origem de cada campo e impedir exportação automática enquanto houver ambiguidade relevante.
9. Exportar objetos apenas depois da confirmação, reutilizando os IDs/caixas já aprovados.

## Hardware e tempo projetados

- O fluxo determinístico e OCR levou poucos segundos por arquivo no lote de teste.
- O Qwen 3B consumiu cerca de 4,9 GB e 76–80 segundos por chamada nesta máquina.
- Um modelo local maior cabe nos 32 GB, mas tende a elevar cada arbitragem para alguns minutos em CPU. Tamanho maior deve ser testado como árbitro regional, não adotado como substituto das regras.
- Um pedido explícito que não demande IA deve terminar em aproximadamente 3–10 segundos.
- Um pedido com uma arbitragem local deve ficar, nesta máquina, em aproximadamente 1,5–3 minutos incluindo preparação e revisão.
- API paga pode ser um fallback mais rápido, mas precisa de um ensaio controlado com os mesmos três casos antes de qualquer decisão de custo.

Esses tempos são faixas de engenharia, não SLA; variam com a quantidade de regiões ambíguas e a resolução do preview.

## Portões de decisão

- Cobertura por geometrias prontas ou blocos derivados mínima de 95%: **aprovado (100%)**.
- Modelo local 3B reconstruindo o pedido inteiro: **reprovado (25% das linhas exatas no recorte)**.
- Primeira regra de formação de bloco regional: **aprovada no caso Real Farma, sem falsos positivos nos outros dez casos**.
- Primeiras regras de associação regional: **aprovadas (7/7 corretas, zero falsas)**.
- Ampliação controlada para materiais e casos sem quantidade explícita: **próximo experimento**.
- Modelo maior ou API como árbitro regional: testar somente depois da associação determinística, nos mesmos casos e com a mesma métrica.

## Reproduzir

```powershell
$env:PYTHONPATH = "fase3-parser"
python scripts/validar_arquitetura_agente.py `
  "$env:USERPROFILE\Documents\LeitorPedidosCDR\Relatorios" `
  "C:\caminho\para\saida" `
  --gabaritos "C:\caminho\para\gabaritos-locais.json"

python scripts/testar_agente_local.py "C:\caminho\para\saida" 03 06 08
```

As pranchas, manifestos, gabaritos e CDRs de clientes são artefatos locais e não devem ser enviados ao GitHub.
