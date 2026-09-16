"""Parser da arvore RIFF de ``content/root.dat``.

``root.dat`` funciona como um indice estrutural: LISTs ``page``, ``layr``,
``grp ``, ``obj `` e ``lnkg`` descrevem a hierarquia, enquanto folhas de
16 bytes apontam para um membro de dados, tamanho e offset. Isso permite
associar os blobs encontrados em ``pageN.dat``/``dataN.dat`` ao objeto dono.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
import math
import re
import struct

from .references import MatrizAfim
from .text import EstiloTexto, parse_estilos_texto


class FormatoEstruturaInvalido(ValueError):
    """Levantado quando a arvore RIFF de root.dat esta inconsistente."""


@dataclass
class _Chunk:
    tag: str
    tipo: str | None
    offset: int
    tamanho: int
    payload: bytes = b""
    filhos: list["_Chunk"] = field(default_factory=list)


@dataclass(frozen=True)
class CaixaObjeto:
    esquerda: int
    topo: int
    direita: int
    base: int

    @property
    def largura_mm(self) -> float:
        return abs(self.direita - self.esquerda) / 10_000.0

    @property
    def altura_mm(self) -> float:
        return abs(self.topo - self.base) / 10_000.0


@dataclass(frozen=True)
class PontoCurva:
    x: int
    y: int
    flag: int


@dataclass(frozen=True)
class GeometriaCurva:
    indice_logico: int
    pontos: tuple[PontoCurva, ...]

    @property
    def numero_pontos(self) -> int:
        return len(self.pontos)


@dataclass(frozen=True)
class PaginaEstrutural:
    indice: int
    membro: str
    largura_unidades: int
    altura_unidades: int
    sangria_unidades: int = 0
    tamanho_personalizado: bool = False

    @property
    def largura_mm(self) -> float:
        return self.largura_unidades / 10_000.0

    @property
    def altura_mm(self) -> float:
        return self.altura_unidades / 10_000.0

    @property
    def sangria_mm(self) -> float:
        return self.sangria_unidades / 10_000.0

    @property
    def limite_esquerdo_nominal(self) -> float:
        return -self.largura_unidades / 2.0

    @property
    def limite_direito_nominal(self) -> float:
        return self.largura_unidades / 2.0

    @property
    def limite_superior_nominal(self) -> float:
        return self.altura_unidades / 2.0

    @property
    def limite_inferior_nominal(self) -> float:
        return -self.altura_unidades / 2.0


@dataclass(frozen=True)
class OcorrenciaLimitePagina:
    objeto: "ObjetoEstrutural"
    pagina: PaginaEstrutural
    excede_esquerda_mm: float = 0.0
    excede_direita_mm: float = 0.0
    excede_topo_mm: float = 0.0
    excede_base_mm: float = 0.0
    ultrapassa_sangria: bool = False


@dataclass(frozen=True)
class ObjetoEstrutural:
    tipo: str
    offset_root: int
    ancestrais: tuple[str, ...]
    membro: str | None
    offset_dados: int | None
    tamanho_dados: int | None
    caixa: CaixaObjeto | None
    matriz: MatrizAfim | None
    codigo_tipo_objeto: int | None = None
    tipo_objeto: str | None = None
    pagina: int | None = None
    geometria_curva: GeometriaCurva | None = None
    id_estrutural: int | None = None
    grupo_powerclip: int | None = None
    tipo_texto: str | None = None
    estilos_texto: tuple[EstiloTexto, ...] = ()

    @property
    def pontos_curva_absolutos(self) -> tuple[tuple[float, float, int], ...] | None:
        """Aplica a matriz do objeto aos pontos locais da curva."""
        if self.geometria_curva is None or self.matriz is None:
            return None
        m = self.matriz
        return tuple(
            (
                m.a * ponto.x + m.b * ponto.y + m.tx,
                m.c * ponto.x + m.d * ponto.y + m.ty,
                ponto.flag,
            )
            for ponto in self.geometria_curva.pontos
        )


TIPOS_OBJETO = {
    1: "retangulo",
    2: "elipse",
    3: "curva",
    4: "texto",
    5: "bitmap",
    6: "texto",
}


def _parse_geometria_curva(data: bytes) -> GeometriaCurva | None:
    """Le o vetor compacto de um objeto tipo 3, com validacao estrutural.

    O bloco guarda primeiro todos os pares ``int32 x,y`` e depois um byte de
    flag para cada ponto. A tabela no inicio de ``loda`` delimita o bloco.
    """
    if len(data) < 40 or struct.unpack_from("<I", data, 16)[0] != 3:
        return None
    quantidade_campos = struct.unpack_from("<I", data, 4)[0]
    quantidade_offsets = quantidade_campos + 4
    fim_tabela = 8 + 4 * quantidade_offsets
    if quantidade_campos > 10_000 or fim_tabela > len(data):
        return None
    offsets = struct.unpack_from(f"<{quantidade_offsets}I", data, 8)
    inicio, inicio_contagem, fim_geometria, penultimo, fim = offsets[-5:]
    if not (
        inicio_contagem == inicio + 4
        and fim_geometria == len(data) - 8
        and penultimo == len(data) - 4
        and fim == len(data)
        and inicio + 8 <= fim_geometria
    ):
        return None
    indice_logico, numero_pontos = struct.unpack_from("<II", data, inicio)
    if inicio + 8 + 9 * numero_pontos != fim_geometria:
        return None
    inicio_flags = inicio + 8 + 8 * numero_pontos
    pontos = tuple(
        PontoCurva(
            *struct.unpack_from("<ii", data, inicio + 8 + 8 * indice),
            data[inicio_flags + indice],
        )
        for indice in range(numero_pontos)
    )
    return GeometriaCurva(indice_logico=indice_logico, pontos=pontos)


def _valor_imediato(no: _Chunk | None) -> int | None:
    """Le folhas RIFF que guardam um ``uint32`` diretamente no root.dat."""
    if no is None or len(no.payload) != 16:
        return None
    arquivo, tamanho, valor, reservado = struct.unpack("<IIII", no.payload)
    if arquivo == 0xFFFFFFFF and tamanho == 4 and reservado == 0:
        return valor
    return None


def _candidatos_grupo_powerclip(data: bytes) -> tuple[int, ...]:
    """Localiza IDs de conteudo de PowerClip em um bloco ``loda``.

    Nos casos controlados, o recipiente possui um campo independente de
    16 bytes ``(spnd_do_grupo, 1, 0, flag)``; ``flag`` apareceu como 0 nos
    retangulos simples e 1 nas curvas do documento real. Exigir que comece em um
    offset declarado pela tabela do proprio ``loda`` evita procurar essa
    assinatura por acaso dentro de geometria, texto ou JSON de estilo.
    """
    if len(data) < 24:
        return ()
    quantidade_campos = struct.unpack_from("<I", data, 4)[0]
    quantidade_offsets = quantidade_campos + 4
    fim_tabela = 8 + 4 * quantidade_offsets
    if quantidade_campos > 10_000 or fim_tabela > len(data):
        return ()
    tabela = struct.unpack_from(f"<{quantidade_offsets}I", data, 8)
    candidatos = []
    for offset in tabela:
        if fim_tabela <= offset <= len(data) - 16:
            identificador, um, zero, um_final = struct.unpack_from("<4I", data, offset)
            if identificador and (um, zero) == (1, 0) and um_final in (0, 1):
                candidatos.append(identificador)
    return tuple(dict.fromkeys(candidatos))


def parse_paginas(
    root_data: bytes,
    streams: dict[int, tuple[str, bytes]],
    largura_padrao: int,
    altura_padrao: int,
    sangria: int = 0,
) -> list[PaginaEstrutural]:
    """Extrai tamanho individual de cada pagina da arvore RIFF."""
    raiz = _parse_chunks(root_data, 0, len(root_data))
    if len(raiz) != 1 or raiz[0].tag != "RIFF":
        raise FormatoEstruturaInvalido("root.dat nao contem um unico RIFF raiz")

    paginas: list[PaginaEstrutural] = []
    for no in raiz[0].filhos:
        if no.tipo != "page":
            continue
        ref_pagina = _referencia(_filho(no, tag="bbox"))
        if ref_pagina is None or ref_pagina[0] not in streams:
            continue
        membro = streams[ref_pagina[0]][0]
        match = re.search(r"/page(\d+)\.dat$", membro)
        if match is None:
            continue

        largura = largura_padrao
        altura = altura_padrao
        personalizado = False
        lgob_pagina = _filho(no, tag="LIST", tipo="lgob")
        loda_pagina = _filho(lgob_pagina, tag="loda") if lgob_pagina else None
        bruto = _ler_referencia(_referencia(loda_pagina), streams)
        if bruto is not None and len(bruto[1]) == 68:
            cabecalho = struct.unpack_from("<8I", bruto[1])
            if cabecalho == (68, 2, 20, 32, 0, 40, 52, 68):
                candidata_largura, candidata_altura = struct.unpack_from("<II", bruto[1], 52)
                if candidata_largura > 0 and candidata_altura > 0:
                    largura = candidata_largura
                    altura = candidata_altura
                    personalizado = True

        paginas.append(
            PaginaEstrutural(
                indice=int(match.group(1)),
                membro=membro,
                largura_unidades=largura,
                altura_unidades=altura,
                sangria_unidades=sangria,
                tamanho_personalizado=personalizado,
            )
        )
    return paginas


def _parse_chunks(data: bytes, inicio: int, fim: int) -> list[_Chunk]:
    chunks: list[_Chunk] = []
    offset = inicio
    while offset + 8 <= fim:
        tag_bruta = data[offset:offset + 4]
        tamanho = struct.unpack_from("<I", data, offset + 4)[0]
        fim_payload = offset + 8 + tamanho
        if fim_payload > fim or fim_payload > len(data):
            raise FormatoEstruturaInvalido(
                f"chunk {tag_bruta!r} no offset {offset} ultrapassa o escopo"
            )
        tag = tag_bruta.decode("latin1")
        if tag in ("RIFF", "LIST"):
            if tamanho < 4:
                raise FormatoEstruturaInvalido(f"{tag} curto no offset {offset}")
            tipo = data[offset + 8:offset + 12].decode("latin1")
            filhos = _parse_chunks(data, offset + 12, fim_payload)
            chunk = _Chunk(tag, tipo, offset, tamanho, filhos=filhos)
        else:
            chunk = _Chunk(
                tag,
                None,
                offset,
                tamanho,
                payload=data[offset + 8:fim_payload],
            )
        chunks.append(chunk)
        offset = fim_payload + (tamanho & 1)
    return chunks


def _filho(no: _Chunk, *, tag: str | None = None, tipo: str | None = None) -> _Chunk | None:
    return next(
        (
            filho
            for filho in no.filhos
            if (tag is None or filho.tag == tag) and (tipo is None or filho.tipo == tipo)
        ),
        None,
    )


def _referencia(no: _Chunk | None) -> tuple[int, int, int] | None:
    if no is None or len(no.payload) != 16:
        return None
    arquivo, tamanho, offset, _ = struct.unpack("<IIII", no.payload)
    if arquivo == 0xFFFFFFFF:
        return None
    return arquivo, tamanho, offset


def _ler_referencia(
    ref: tuple[int, int, int] | None,
    streams: dict[int, tuple[str, bytes]],
) -> tuple[str, bytes] | None:
    if ref is None or ref[0] not in streams:
        return None
    membro, data = streams[ref[0]]
    _, tamanho, offset = ref
    if offset + tamanho > len(data):
        raise FormatoEstruturaInvalido(
            f"referencia em {membro} ({offset}+{tamanho}) ultrapassa o arquivo"
        )
    return membro, data[offset:offset + tamanho]


def parse_estrutura(
    root_data: bytes,
    streams: dict[int, tuple[str, bytes]],
) -> list[ObjetoEstrutural]:
    """Extrai objetos, hierarquia, bbox e matriz a partir de ``root.dat``."""
    raiz = _parse_chunks(root_data, 0, len(root_data))
    if len(raiz) != 1 or raiz[0].tag != "RIFF":
        raise FormatoEstruturaInvalido("root.dat nao contem um unico RIFF raiz")

    objetos: list[ObjetoEstrutural] = []
    pais_estruturais: list[int | None] = []
    candidatos_powerclip: list[tuple[int, ...]] = []
    objetos_clpt_por_id: dict[int, list[int]] = {}
    tipos_estruturais = {"obj ", "grp ", "lnkg"}

    def visitar(
        no: _Chunk,
        ancestrais: tuple[str, ...],
        pagina: int | None,
        pai_estrutural: int | None,
        em_clpt: bool,
    ) -> None:
        proximos_ancestrais = ancestrais
        proxima_pagina = pagina
        proximo_pai = pai_estrutural
        dentro_clpt = em_clpt or no.tipo == "clpt"
        if no.tipo == "page":
            ref_pagina = _referencia(_filho(no, tag="bbox"))
            if ref_pagina is not None and ref_pagina[0] in streams:
                membro_pagina = streams[ref_pagina[0]][0]
                match = re.search(r"/page(\d+)\.dat$", membro_pagina)
                proxima_pagina = int(match.group(1)) if match else None

        if no.tipo in tipos_estruturais:
            lgob = _filho(no, tag="LIST", tipo="lgob")
            loda = _filho(lgob, tag="loda") if lgob else None
            trfl = _filho(lgob, tag="LIST", tipo="trfl") if lgob else None
            trfd = _filho(trfl, tag="trfd") if trfl else None

            ref_loda = _referencia(loda)
            membro = None
            offset_dados = None
            tamanho_dados = None
            bruto_loda = _ler_referencia(ref_loda, streams)
            if ref_loda is not None and bruto_loda is not None:
                membro = bruto_loda[0]
                _, tamanho_dados, offset_dados = ref_loda

            codigo_tipo_objeto = None
            tipo_objeto = None
            geometria_curva = None
            tipo_texto = None
            estilos_texto: tuple[EstiloTexto, ...] = ()
            if no.tipo == "obj " and bruto_loda is not None and len(bruto_loda[1]) >= 20:
                codigo_tipo_objeto = struct.unpack_from("<I", bruto_loda[1], 16)[0]
                tipo_objeto = TIPOS_OBJETO.get(codigo_tipo_objeto, "desconhecido")
                if codigo_tipo_objeto == 3:
                    geometria_curva = _parse_geometria_curva(bruto_loda[1])
                elif codigo_tipo_objeto in (4, 6):
                    tipo_texto = "artistico" if codigo_tipo_objeto == 4 else "paragrafo"
                    bruto_txsm = _ler_referencia(
                        _referencia(_filho(no, tag="txsm")),
                        streams,
                    )
                    if bruto_txsm is not None:
                        estilos_texto = parse_estilos_texto(bruto_txsm[1])

            id_estrutural = _valor_imediato(_filho(no, tag="spnd"))
            candidatos = (
                _candidatos_grupo_powerclip(bruto_loda[1])
                if bruto_loda is not None
                else ()
            )

            caixa = None
            bruto_bbox = _ler_referencia(_referencia(_filho(no, tag="bbox")), streams)
            if bruto_bbox is not None and len(bruto_bbox[1]) >= 16:
                caixa = CaixaObjeto(*struct.unpack_from("<4i", bruto_bbox[1]))

            matriz = None
            bruto_trfd = _ler_referencia(_referencia(trfd), streams)
            if bruto_trfd is not None and len(bruto_trfd[1]) >= 88:
                valores = struct.unpack_from("<6d", bruto_trfd[1], 40)
                if all(math.isfinite(v) for v in valores):
                    candidata = MatrizAfim(*valores)
                    if candidata.escala_x > 0 and candidata.escala_y > 0:
                        matriz = candidata

            indice_objeto = len(objetos)
            objetos.append(
                ObjetoEstrutural(
                    tipo=no.tipo.strip(),
                    offset_root=no.offset,
                    ancestrais=ancestrais,
                    membro=membro,
                    offset_dados=offset_dados,
                    tamanho_dados=tamanho_dados,
                    caixa=caixa,
                    matriz=matriz,
                    codigo_tipo_objeto=codigo_tipo_objeto,
                    tipo_objeto=tipo_objeto,
                    pagina=proxima_pagina,
                    geometria_curva=geometria_curva,
                    id_estrutural=id_estrutural,
                    tipo_texto=tipo_texto,
                    estilos_texto=estilos_texto,
                )
            )
            pais_estruturais.append(pai_estrutural)
            candidatos_powerclip.append(candidatos)
            if dentro_clpt and id_estrutural is not None and no.tipo in {"grp ", "lnkg"}:
                objetos_clpt_por_id.setdefault(id_estrutural, []).append(indice_objeto)
            proximos_ancestrais = ancestrais + (no.tipo.strip(),)
            proximo_pai = indice_objeto

        for filho in no.filhos:
            visitar(filho, proximos_ancestrais, proxima_pagina, proximo_pai, dentro_clpt)

    visitar(raiz[0], (), None, None, False)

    # Propaga a pagina atraves da hierarquia normal e dos vinculos de
    # PowerClip. A iteracao e necessaria para recipientes aninhados: primeiro
    # o grupo externo recebe a pagina, depois um objeto dentro dele pode
    # apontar para outro grupo ``clpt``.
    alterou = True
    while alterou:
        alterou = False
        for indice, objeto in enumerate(objetos):
            pagina_objeto = objeto.pagina
            pai = pais_estruturais[indice]
            if pagina_objeto is None and pai is not None and objetos[pai].pagina is not None:
                pagina_objeto = objetos[pai].pagina
                objetos[indice] = replace(objeto, pagina=pagina_objeto)
                objeto = objetos[indice]
                alterou = True
            if pagina_objeto is None:
                continue
            destinos = {
                destino
                for candidato in candidatos_powerclip[indice]
                for destino in objetos_clpt_por_id.get(candidato, ())
                if len(objetos_clpt_por_id.get(candidato, ())) == 1
            }
            if len(destinos) != 1:
                continue
            destino = destinos.pop()
            if objetos[destino].pagina is None:
                grupo_id = objetos[destino].id_estrutural
                objetos[indice] = replace(objeto, grupo_powerclip=grupo_id)
                objetos[destino] = replace(objetos[destino], pagina=pagina_objeto)
                alterou = True
            elif objetos[indice].grupo_powerclip is None:
                objetos[indice] = replace(
                    objeto,
                    grupo_powerclip=objetos[destino].id_estrutural,
                )
    return objetos
