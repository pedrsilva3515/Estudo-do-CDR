# Fase 3 — Parser incremental (`zcfreader`)

Biblioteca Python que abre um `.cdr` moderno (formato ZCF) **sem depender do CorelDRAW
instalado** e extrai:

- as imagens de `content/data/Bitmaps.dat` (RGB, CMYK, máscara de transparência);
- nomes de layers/objetos e seus estilos de preenchimento/contorno/transparência de
  `content/data/page*.dat` (sem geometria ainda — ver limitações abaixo).

Objetos vetoriais (posição, tamanho, curvas) e texto ainda não têm parser — a árvore de
"chunks" binários de `page*.dat` só foi parcialmente decodificada, ver
`docs/descobertas-fase3-page1.md`.

Zero dependências externas — usa só `zipfile`, `struct` e `zlib` da biblioteca padrão
(inclusive o escritor de PNG é próprio, ver `zcfreader/png_writer.py`).

## Uso

```python
from zcfreader import abrir_cdr

with abrir_cdr("arquivo.cdr") as doc:
    print(doc.arquivos_de_dados)  # ex.: ['Bitmaps.dat', 'data1.dat', 'page1.dat']

    bitmaps = doc.bitmaps()  # None se o documento nao tiver nenhum bitmap
    if bitmaps:
        for registro in bitmaps:
            img = registro.imagem
            print(registro.indice, img.largura, img.altura, img.espaco_de_cor)
            registro.salvar_png(f"imagem_{registro.indice}.png")
```

Linha de comando:

```
python -m zcfreader.cli listar arquivo.cdr
python -m zcfreader.cli extrair arquivo.cdr --saida pasta/
```

Nomes e estilos de `page1.dat`:

```python
with abrir_cdr("arquivo.cdr") as doc:
    for item in doc.pagina(1) or []:
        print(item.nome, item.estilo)  # estilo=None se o objeto/layer nao tiver um

    # mais completo: TODOS os blocos de estilo, mesmo sem nome associado
    for offset, estilo in doc.estilos_da_pagina(1) or []:
        print(offset, estilo["fill"]["primaryColor"])
```

## O que está confirmado e implementado

Baseado nas descobertas de `docs/descobertas-fase2.md` e `docs/descobertas-fase1b.md`,
validadas nesta fase com testes automatizados (`tests/test_bitmaps.py`) rodando os 21
casos de teste da Fase 1/1b como fixtures, e com uma verificação manual adicional contra
o arquivo real `helo.cdr` (fora da amostra de testes — 4 imagens extraídas corretamente,
dimensões batendo com a análise manual original):

- Estrutura TLV do `Bitmaps.dat` (registros `UI`, um por imagem única — deduplicação).
- Estrutura aninhada `RI` (imagem + máscara de transparência opcional).
- Decodificação de pixels RGB (24 bpp, BGR na origem) e CMYK (32 bpp, ordem C,M,Y,K).
- Máscara de transparência (8 bpp, escala de cinza) combinada como canal alfa.
- Validação visual: canais de cor e ordem das linhas (top-down) confirmados comparando
  pixels decodificados com as cores exatas usadas para gerar as imagens-fonte na macro
  VBA (retângulo vermelho, elipses magenta/ciano, gradiente amarelo→azul).

### Correção feita durante esta fase

A regra de tamanho do registro `RI` documentada na Fase 1b estava **errada** — foi
escrita a partir de validação manual de poucos casos, e a implementação real (testada
contra todos os 21 casos) revelou uma regra mais simples, além de um campo de 8 bytes
entre imagens que não tinha sido identificado antes. Ver a seção D4 corrigida em
`docs/descobertas-fase1b.md` para o detalhe — é um bom lembrete de por que este projeto
exige testes automatizados antes de declarar uma regra de formato como fechada, mesmo
quando a validação manual "parece" bater.

## Limitações conhecidas

### Bitmaps (`content/data/Bitmaps.dat`)

- **Conversão CMYK→RGB é ingênua** (fórmula padrão sem gestão de cor / perfil ICC). Boa
  para preview e extração de conteúdo; as cores podem divergir um pouco do que o
  CorelDRAW renderiza com o perfil de cor do documento.
- **Metadado de orientação EXIF não é preservado.** Uma foto real importada com EXIF de
  rotação (comum em fotos de celular) pode ser extraída invertida/rotacionada — o
  `Bitmaps.dat` guarda os pixels brutos, sem sinalizar a orientação original. Não
  encontramos, até agora, nenhum campo no cabeçalho do `RI` que carregue essa informação
  (os ~20 bytes ainda não identificados no offset 98, ver D3 em `descobertas-fase1b.md`,
  são candidatos a investigar).
- **Performance**: a conversão CMYK→RGB e a composição do canal alfa usam laços Python
  puro por pixel — aceitável para inspeção/extração pontual, mas lento para imagens muito
  grandes (dezenas de milhões de pixels) ou processamento em lote. Se isso virar gargalo
  real, a especificação original do projeto já previa Rust como alternativa; um caminho
  mais simples seria vetorizar com `numpy` como dependência opcional.
- Campos ainda não identificados no cabeçalho do `RI` (ver D3 em
  `docs/descobertas-fase1b.md`) são ignorados, não interpretados.

### Página (`content/data/page*.dat`)

- **Nenhuma geometria é extraída** (posição, tamanho, ângulo, pontos de curva) — só
  nomes e estilo de preenchimento/contorno/transparência. A árvore de "chunks" binários
  que guarda a geometria não foi decodificada ainda (ver `docs/descobertas-fase3-page1.md`).
- **`doc.pagina()` não diferencia layer de shape** — os dois usam o mesmo padrão de nome.
- **O pareamento nome↔estilo de `doc.pagina()` só é confiável quando todo objeto tem
  nome.** A maioria dos objetos em documentos reais não é nomeada pelo usuário — nesse
  caso, use `doc.estilos_da_pagina()`, que devolve todos os blocos de estilo sem tentar
  associá-los a um nome. Verificado no `helo.cdr`: 24 blocos de estilo, só 2 nomes.
- Documentos com texto artístico podem ter dados binários (kerning, curvas de glifo) que
  colidem com o padrão heurístico de nome; um filtro (proporção de letras) reduz mas não
  elimina falsos positivos.

## Testes

```
python -m unittest discover -s fase3-parser/tests -v
```

Usa os arquivos em `casos-de-teste/*.cdr` (gerados pela Fase 1/1b) como fixtures; testes
que dependem de um arquivo específico são pulados (`SkipTest`) se o arquivo não existir,
em vez de falhar.
