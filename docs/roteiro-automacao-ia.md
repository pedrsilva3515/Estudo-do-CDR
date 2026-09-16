# Roteiro para automação e IA

O leitor ZCF deve ser a camada de inspeção independente do CorelDRAW. O ganho
prático vem de combinar essa leitura com automação do CorelDRAW apenas quando
for necessário alterar ou criar arte.

## Etapa 1 — conferência automática

Criar uma saída JSON estável e um relatório legível para cada arquivo CDR.
Ela deve indicar páginas, layers, objetos, textos, cores, preenchimentos,
contornos, imagens, transparências e alertas verificáveis. Isso permite
conferir lotes sem abrir cada documento no CorelDRAW.

Exemplos de regras úteis:

- texto sem fonte disponível ou com tamanho fora do padrão;
- objetos fora do corte ou da sangria;
- RGB em arquivo destinado à impressão CMYK;
- transparência, efeito ou cor spot que exige atenção na produção;
- links de bitmap ausentes, baixa resolução ou excesso de imagens;
- contorno muito fino, sem contorno ou com largura divergente do padrão;
- layers ocultas, bloqueadas ou não imprimíveis.

## Etapa 2 — receitas de alteração

Definir um JSON de instruções de alto nível, por exemplo: alterar tamanho de
página, normalizar layers, substituir fonte, aplicar padrão de contorno ou
exportar PDF. Um executor via automação do CorelDRAW lê a receita e faz a
alteração. Antes e depois, o leitor ZCF confere o resultado.

## Etapa 3 — assistente de IA

A IA recebe a solicitação em linguagem comum, consulta o relatório do arquivo
e produz uma receita limitada às operações conhecidas. Ela não altera o CDR
diretamente: o executor aplica a receita e a conferência mostra as diferenças.
Assim, cada alteração fica reproduzível, auditável e reversível por cópia do
arquivo original.

## Próximo incremento técnico

Depois do caso de textura, priorizar a saída de inspeção em JSON e regras de
preflight. Essa é a parte com maior retorno imediato para produção, pois usa
os campos que já foram confirmados no estudo.
