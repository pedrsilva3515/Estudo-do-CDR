# Retomada do projeto

Este arquivo é o ponto de entrada para continuar o estudo em outro computador.

## Estado versionado

- Repositório: `pedrsilva3515/Estudo-do-CDR`
- Branch de trabalho: `claude/zcf-format-reverse-engineering-hdgcjw`
- Último marco técnico antes deste documento: preenchimentos e transparência uniforme
- Casos controlados versionados: `caso_00` a `caso_85`, sempre com `.cdr` e
  manifesto `.json`.
- Testes no encerramento: 85 testes passando.

Commits técnicos desta rodada, em ordem:

- `7a9ee5e` — estrutura, metadados, páginas, limites e PowerClip;
- `b18344f` — conteúdo e estilos de texto;
- `e1a490d` — associação de texto aos objetos estruturais;
- `7037b08` — visibilidade, impressão e bloqueio de layers;
- `bb541c8` — propriedades básicas de contorno;
- `c42a620` — contornos avançados e linha fina;
- `aa84523` — segmentos e subcaminhos abertos/fechados.

Para retomar:

```powershell
git clone https://github.com/pedrsilva3515/Estudo-do-CDR.git
cd Estudo-do-CDR
git switch claude/zcf-format-reverse-engineering-hdgcjw
$env:PYTHONPATH = "fase3-parser"
python -m unittest discover -s fase3-parser/tests -v
```

## O que foi fechado nesta rodada

1. Estrutura RIFF, tipos de objeto, matrizes, caixas e associação por página.
2. Tamanhos individuais de página, sangria e objetos fora do corte.
3. Vínculos de PowerClip, inclusive aninhados e em `dataN.dat`.
4. Texto por objeto: conteúdo, artístico/parágrafo, fonte, tamanho e página.
5. Layers: nome, visível, imprimível, editável e propagação em PowerClip.
6. Contornos: presença, largura, linha fina, cor, tracejado, escala, pontas,
   junções, alinhamento, sobreimpressão e especificações de setas.
7. Curvas: pontos, segmentos retos/Bézier, pontos de controle, múltiplos
   subcaminhos e detecção de subcaminhos abertos.
8. Preenchimentos: ausente ou uniforme, cores CMYK/RGB e sobreimpressão;
   transparência uniforme e degradês linear, radial, cônico e quadrado.

Os detalhes e evidências estão separados por assunto em:

- `docs/descobertas-estrutura-root.md`
- `docs/descobertas-paginas-limites.md`
- `docs/descobertas-texto.md`
- `docs/descobertas-layers.md`
- `docs/descobertas-contornos.md`
- `docs/descobertas-geometria-vetorial.md`
- `docs/descobertas-preenchimentos-transparencias.md`

Os geradores dos casos avançados estão em
`ferramentas-estudo/GerarCasosAvancados.ps1`. Eles dependem do CorelDRAW 2025
v26 instalado e geram novos arquivos em uma pasta separada, sem sobrescrever as
fixtures versionadas.

## Resultado do arquivo “Debora ellen fdf.cdr”

O arquivo original não está no repositório, mas os resultados confirmados estão
documentados:

- 13 objetos: 6 bitmaps, 6 curvas e 1 texto;
- todos na página 1 e na layer “Camada 1”;
- layer visível, imprimível e editável;
- texto Arial, aproximadamente 65,05 pt;
- 13 estilos de contorno, todos sem contorno (`width=0`);
- 6 curvas, 2.840 pontos e 12 subcaminhos;
- todos os 12 subcaminhos estão fechados.

## APIs de conferência já disponíveis

```python
with abrir_cdr("arquivo.cdr") as doc:
    doc.metadados()
    doc.bitmaps()
    doc.instancias_bitmaps()
    doc.estrutura()
    doc.paginas_estruturais()
    doc.camadas()
    doc.textos()
    doc.textos_por_objeto()
    doc.conferencia_limites()
    doc.curvas_com_subcaminhos_abertos()
```

Também é possível executar:

```powershell
$env:PYTHONPATH = "fase3-parser"
python -m zcfreader.cli listar "C:\caminho\arquivo.cdr"
```

## Próximo estudo recomendado

Preenchimentos e transparências por objeto:

1. variações de degradê (cores intermediárias, ponto médio e geometria);
2. cor spot;
3. padrão/textura;
4. cor spot requer uma paleta spot instalada neste computador.

Depois disso, as pendências de maior valor são nós cúspide/suave/simétrico,
atributos avançados de setas, contorno caligráfico/variável e gestão de cor ICC.

## Regra de confiabilidade

Não declarar um campo como confirmado a partir de um único arquivo. Criar casos
que mudam uma única propriedade, salvar o `.cdr`, adicionar o manifesto `.json`,
comparar a representação interna, implementar o parser e adicionar teste de
regressão.
