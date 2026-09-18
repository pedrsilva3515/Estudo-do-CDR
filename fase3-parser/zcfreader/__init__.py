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
from .color import ContextoCorDocumento, parse_contexto_cor
from .metadata import FormatoMetadadosInvalido, MetadadosDocumento
from .page import (
    CorObjeto,
    EstiloObjeto,
    ItemNomeado,
    ParadaDegrade,
    PreenchimentoObjeto,
    TransparenciaObjeto,
    parse_cor_objeto,
    parse_estilo_objeto,
)
from .references import InstanciaBitmap, MatrizAfim
from .structure import (
    CaixaObjeto,
    CamadaEstrutural,
    ContornoObjeto,
    OpcoesSeta,
    FormatoEstruturaInvalido,
    GeometriaCurva,
    ObjetoEstrutural,
    OcorrenciaLimitePagina,
    NoLarguraVariavel,
    PaginaEstrutural,
    PontoCurva,
    SubcaminhoCurva,
)
from .text import EstiloTexto, FluxoTexto, FormatoTextoInvalido, TextoEstruturado, TrechoTexto
from .pedido import interpretar_nome_arquivo, interpretar_pedido, parse_dimensoes, parse_material, parse_quantidade

__all__ = [
    "abrir_cdr",
    "ZcfContainer",
    "ContextoCorDocumento",
    "parse_contexto_cor",
    "ArquivoBitmaps",
    "RegistroBitmap",
    "ImagemBruta",
    "FormatoBitmapsInvalido",
    "MetadadosDocumento",
    "FormatoMetadadosInvalido",
    "ItemNomeado",
    "CorObjeto",
    "ParadaDegrade",
    "PreenchimentoObjeto",
    "TransparenciaObjeto",
    "EstiloObjeto",
    "parse_cor_objeto",
    "parse_estilo_objeto",
    "InstanciaBitmap",
    "MatrizAfim",
    "ObjetoEstrutural",
    "CaixaObjeto",
    "CamadaEstrutural",
    "ContornoObjeto",
    "OpcoesSeta",
    "NoLarguraVariavel",
    "FormatoEstruturaInvalido",
    "GeometriaCurva",
    "PontoCurva",
    "SubcaminhoCurva",
    "PaginaEstrutural",
    "OcorrenciaLimitePagina",
    "EstiloTexto",
    "FluxoTexto",
    "TrechoTexto",
    "FormatoTextoInvalido",
    "TextoEstruturado",
    "interpretar_pedido",
    "interpretar_nome_arquivo",
    "parse_material",
    "parse_dimensoes",
    "parse_quantidade",
]
