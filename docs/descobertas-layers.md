# Descobertas — layers, visibilidade e impressão

Fonte: `caso_09`, quatro casos controlados novos (`caso_45` a `caso_48`)
e um documento real externo. Cada variante altera somente uma propriedade
da layer pelo CorelDRAW 26.0.

## Y1. Estrutura

Layers são `LIST/layr` dentro do `LIST/gobj` de uma página. Seus objetos são
descendentes da própria layer. A folha `loda` aponta para um bloco no membro
da página; quando o nome não é herdado de uma layer de sistema, o último
campo desse bloco é uma string UTF-16LE terminada em zero.

Isso permite associar cada objeto estrutural à sua layer sem usar a busca
heurística de nomes de `pageN.dat`. Conteúdo dentro de PowerClip herda a
layer do recipiente durante a mesma propagação já usada para a página.

## Y2. Flags confirmadas

A folha imediata `flgs` da layer padrão controlada contém `0x98000000`.
Alterações isoladas produziram:

| Propriedade no Corel | XOR contra padrão | Interpretação |
|---|---:|---|
| `Printable = False` | `0x08` | não imprimível |
| `Editable = False` | `0x10` | bloqueada/não editável |
| `Visible = False` | `0x140` | oculta |

O parser expõe os booleanos `visivel`, `imprimivel` e `editavel`, além do
valor bruto para auditoria. Layers especiais do Corel, como linhas-guia,
desktop e grade, reutilizam alguns desses bits e aparecem normalmente como
não imprimíveis.

## Y3. Resultado no documento real

Os 13 objetos foram associados à `Camada 1`, inclusive os dez objetos que
ficam em `data1.dat` por causa de PowerClips. A layer está visível,
imprimível e editável. As layers de sistema foram identificadas à parte.

## Implementação e limites

- `doc.camadas()` devolve página, membro, nome, flags e propriedades.
- `objeto.camada` informa a layer, inclusive após propagação por PowerClip.
- A contagem da layer representa objetos estruturais diretamente descendentes;
  conteúdos de PowerClip continuam associados à layer, mas não aumentam essa
  contagem direta.
- Ainda faltam master layers criadas pelo usuário, layers compartilhadas entre
  páginas e confirmação dos mesmos bits em versões antigas do CorelDRAW.
