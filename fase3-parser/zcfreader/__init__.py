"""zcfreader — leitor independente do formato ZCF (`.cdr` moderno do
CorelDRAW), sem depender do CorelDRAW instalado.

Biblioteca construida por engenharia reversa incremental, documentada em
docs/ no repositorio do projeto (nivel de confianca explicito por achado).
Cobre leitura; a escrita/edicao continua sendo tarefa do CorelDRAW/VBA.

Nesta fase, cobre `content/data/Bitmaps.dat` (extracao de imagens) e uma
extracao parcial de `content/data/page*.dat` (nomes de layers/objetos e
seus estilos de preenchimento/contorno — sem geometria ainda). `root.dat`
ainda nao tem parser — ver docs/descobertas-fase2.md e
docs/descobertas-fase3-page1.md para o que ja se sabe sobre eles.

Uso basico:

    from zcfreader import abrir_cdr

    with abrir_cdr("arquivo.cdr") as doc:
        bitmaps = doc.bitmaps()
        if bitmaps:
            for registro in bitmaps:
                print(registro.indice, registro.imagem.largura, registro.imagem.altura)
                registro.salvar_png(f"imagem_{registro.indice}.png")

        for item in doc.pagina(1) or []:
            print(item.nome, item.estilo)
"""
from .bitmaps import ArquivoBitmaps, FormatoBitmapsInvalido, ImagemBruta, RegistroBitmap
from .container import ZcfContainer, abrir_cdr
from .page import ItemNomeado

__all__ = [
    "abrir_cdr",
    "ZcfContainer",
    "ArquivoBitmaps",
    "RegistroBitmap",
    "ImagemBruta",
    "FormatoBitmapsInvalido",
    "ItemNomeado",
]
