"""zcfreader — leitor independente do formato ZCF (`.cdr` moderno do
CorelDRAW), sem depender do CorelDRAW instalado.

Biblioteca construida por engenharia reversa incremental, documentada em
docs/ no repositorio do projeto (nivel de confianca explicito por achado).
Cobre leitura; a escrita/edicao continua sendo tarefa do CorelDRAW/VBA.

Nesta fase, cobre `content/data/Bitmaps.dat` (extracao de imagens), uma
extracao parcial de `content/data/page*.dat` (nomes e estilos) e a arvore
RIFF de `root.dat`, com hierarquia, tipos, bbox, matriz e pontos de curvas.
Veja os documentos de descobertas em `docs/` para evidencias e limitacoes.

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
from .metadata import FormatoMetadadosInvalido, MetadadosDocumento
from .page import ItemNomeado
from .references import InstanciaBitmap, MatrizAfim
from .structure import (
    CaixaObjeto,
    FormatoEstruturaInvalido,
    GeometriaCurva,
    ObjetoEstrutural,
    OcorrenciaLimitePagina,
    PaginaEstrutural,
    PontoCurva,
)
from .text import EstiloTexto, FluxoTexto, FormatoTextoInvalido, TrechoTexto

__all__ = [
    "abrir_cdr",
    "ZcfContainer",
    "ArquivoBitmaps",
    "RegistroBitmap",
    "ImagemBruta",
    "FormatoBitmapsInvalido",
    "MetadadosDocumento",
    "FormatoMetadadosInvalido",
    "ItemNomeado",
    "InstanciaBitmap",
    "MatrizAfim",
    "ObjetoEstrutural",
    "CaixaObjeto",
    "FormatoEstruturaInvalido",
    "GeometriaCurva",
    "PontoCurva",
    "PaginaEstrutural",
    "OcorrenciaLimitePagina",
    "EstiloTexto",
    "FluxoTexto",
    "TrechoTexto",
    "FormatoTextoInvalido",
]
