"""zcfreader — leitor independente do formato ZCF (`.cdr` moderno do
CorelDRAW), sem depender do CorelDRAW instalado.

Biblioteca construida por engenharia reversa incremental, documentada em
docs/ no repositorio do projeto (nivel de confianca explicito por achado).
Cobre leitura; a escrita/edicao continua sendo tarefa do CorelDRAW/VBA.

Nesta fase, cobre apenas `content/data/Bitmaps.dat` (extracao de imagens).
Objetos vetoriais, texto e paginas (`root.dat`, `page*.dat`) ainda nao tem
parser — ver docs/descobertas-fase2.md para o que ja se sabe sobre eles.

Uso basico:

    from zcfreader import abrir_cdr

    with abrir_cdr("arquivo.cdr") as doc:
        bitmaps = doc.bitmaps()
        if bitmaps:
            for registro in bitmaps:
                print(registro.indice, registro.imagem.largura, registro.imagem.altura)
                registro.salvar_png(f"imagem_{registro.indice}.png")
"""
from .bitmaps import ArquivoBitmaps, FormatoBitmapsInvalido, ImagemBruta, RegistroBitmap
from .container import ZcfContainer, abrir_cdr

__all__ = [
    "abrir_cdr",
    "ZcfContainer",
    "ArquivoBitmaps",
    "RegistroBitmap",
    "ImagemBruta",
    "FormatoBitmapsInvalido",
]
