"""Parser (parcial) de content/data/page*.dat.

Diferente do Bitmaps.dat, page*.dat NAO tem uma estrutura TLV totalmente
mapeada ainda — e uma arvore de "chunks" binarios (um cabecalho recorrente
de tamanho+contagem+tabela-de-offsets aparece varias vezes, mas a semantica
completa da arvore ainda nao foi decodificada, ver docs/descobertas-fase3-page1.md).

O que ESTA confirmado e implementado aqui e mais restrito, mas ja util:

  - Nomes de layers e objetos (shapes) sao gravados em UTF-16LE, terminados
    em dois bytes zero, cada um precedido por um GUID de 16 bytes.
  - As propriedades de preenchimento/contorno/transparencia de um objeto
    sao gravadas como uma STRING JSON EM TEXTO PURO (nao binaria), logo
    apos o nome do objeto, com um prefixo de 4 bytes (uint32 LE) contendo
    o tamanho exato da string em bytes.

Este modulo faz uma varredura heuristica (nao uma decodificacao completa da
arvore de chunks) para extrair esses dois elementos e parea-los pela ordem
em que aparecem no arquivo: cada nome "pertence" ao proximo bloco JSON que
aparecer antes do nome seguinte (ou None, se nao houver JSON antes do
proximo nome — layers, por exemplo, nao tem esse bloco).

Limitacoes conhecidas (ver README da Fase 3):
  - Nao diferencia layer de shape — ambos usam o mesmo padrao de nome.
  - Documentos com texto artistico podem ter dados binarios (kerning,
    curvas de glifo) que colidem com o padrao de nome; um filtro heuristico
    (proporcao de letras) reduz mas nao elimina falsos positivos.
  - Nenhuma geometria (posicao, tamanho, curvas) e extraida ainda.
  - **O pareamento nome->estilo so e confiavel quando TODO objeto tem
    nome.** Em documentos reais a maioria dos objetos nao e nomeada pelo
    usuario (o CorelDRAW nao exige nome para desenhar) — nesse caso o
    bloco JSON de um objeto sem nome fica "solto" e pode ser atribuido
    erradamente ao nome mais proximo. Verificado no arquivo de exemplo
    `helo.cdr`: 24 blocos de estilo (compare com a contagem de "24
    bitmaps" da interface do CorelDRAW — mesmo numero, reforcando a
    hipotese de que sao os mesmos 24 objetos/instancias) mas so 2 nomes
    (`Linhas-guia`, `Camada 1`). Use `parse_estilos()` para obter TODOS
    os blocos de estilo do arquivo, sem depender de nome.
"""
from __future__ import annotations

import json
import re
import struct
from dataclasses import dataclass

_JSON_MARCADOR = re.compile(rb'\{(?="(?:fill|StackedBitmapEffects)")')
_PROPORCAO_MINIMA_LETRAS = 0.6
_TAMANHO_MINIMO_NOME = 3


@dataclass
class ItemNomeado:
    """Um nome encontrado em page*.dat (layer ou objeto — nao diferenciados
    ainda) e, se houver, o bloco de estilo JSON associado."""

    offset: int
    nome: str
    estilo: dict | None = None

    @property
    def estilo_tipado(self) -> "EstiloObjeto | None":
        """Converte o JSON de estilo deste item em campos de leitura."""
        return parse_estilo_objeto(self.estilo) if self.estilo is not None else None


@dataclass(frozen=True)
class CorObjeto:
    """Cor serializada pelo CorelDRAW em ``primaryColor``/``secondaryColor``."""

    modelo: str
    paleta: str | None
    componentes: tuple[int, ...]
    opacidade: int | None
    identificador: str | None
    bruto: str


@dataclass(frozen=True)
class PreenchimentoObjeto:
    tipo: str
    codigo_tipo: int | None
    tipo_degrade: str | None
    cor_primaria: CorObjeto | None
    cor_secundaria: CorObjeto | None
    sobreimpressao: bool | None
    angulo: float | None
    passos: int | None
    ponto_medio: float | None
    id_padrao: int | None
    largura_repeticao: int | None
    altura_repeticao: int | None
    cores_intermediarias: tuple["ParadaDegrade", ...]
    escala_x: float | None
    escala_y: float | None


@dataclass(frozen=True)
class ParadaDegrade:
    posicao: float | None
    cor: CorObjeto | None
    opacidade: int | None
    modo_mistura: int | None
    ponto_medio: float | None


@dataclass(frozen=True)
class TransparenciaObjeto:
    tipo: str
    tipo_degrade: str | None
    uniforme: float | None
    inicio: float | None
    fim: float | None
    aplica_a: int | None
    modo: int | None
    angulo: float | None
    passos: int | None
    ponto_medio: float | None


@dataclass(frozen=True)
class EstiloObjeto:
    preenchimento: PreenchimentoObjeto | None
    transparencia: TransparenciaObjeto | None


def _inteiro(valor) -> int | None:
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _real(valor) -> float | None:
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def parse_cor_objeto(valor: object) -> CorObjeto | None:
    """Decodifica uma cor textual observada nos estilos de ``pageN.dat``.

    Os casos controlados confirmam CMYK (quatro componentes) e RGB255 (três).
    Modelos ainda nao estudados preservam a cadeia original sem inventar uma
    quantidade de componentes.
    """
    if not isinstance(valor, str) or not valor:
        return None
    partes = valor.split(",")
    modelo = partes[0]
    quantidade = {"CMYK": 4, "RGB255": 3}.get(modelo, 0)
    componentes = tuple(
        numero for parte in partes[2:2 + quantidade]
        if (numero := _inteiro(parte)) is not None
    )
    return CorObjeto(
        modelo=modelo,
        paleta=partes[1] if len(partes) > 1 else None,
        componentes=componentes,
        opacidade=_inteiro(partes[2 + quantidade]) if quantidade and len(partes) > 2 + quantidade else None,
        identificador=partes[3 + quantidade] if quantidade and len(partes) > 3 + quantidade else None,
        bruto=valor,
    )


def _parse_parada_degrade(valor: object) -> ParadaDegrade | None:
    if not isinstance(valor, str):
        return None
    partes = valor.split(":", 4)
    if len(partes) != 5:
        return None
    return ParadaDegrade(
        posicao=_real(partes[0]),
        cor=parse_cor_objeto(partes[1]),
        opacidade=_inteiro(partes[2]),
        modo_mistura=_inteiro(partes[3]),
        ponto_medio=_real(partes[4]),
    )


def parse_estilo_objeto(estilo: dict | None) -> EstiloObjeto:
    """Converte o JSON de estilo encontrado em ``pageN.dat`` em dados tipados."""
    fill = estilo.get("fill") if isinstance(estilo, dict) else None
    transparencia = estilo.get("transparency") if isinstance(estilo, dict) else None
    codigo_tipo = _inteiro(fill.get("type")) if isinstance(fill, dict) else None
    preenchimento = None
    if isinstance(fill, dict):
        cores_intermediarias = tuple(
            parada for valor in fill.get("intermediateColors", [])
            if (parada := _parse_parada_degrade(valor)) is not None
        )
        preenchimento = PreenchimentoObjeto(
            tipo={0: "nenhum", 1: "uniforme", 2: "degrade", 8: "padrao"}.get(codigo_tipo, "desconhecido"),
            codigo_tipo=codigo_tipo,
            tipo_degrade={1: "linear", 2: "radial", 3: "conico", 4: "quadrado"}.get(
                _inteiro(fill.get("fountainType"))
            ),
            cor_primaria=parse_cor_objeto(fill.get("primaryColor")),
            cor_secundaria=parse_cor_objeto(fill.get("secondaryColor")),
            sobreimpressao={"0": False, "1": True}.get(str(fill.get("overprint"))),
            angulo=_real(fill.get("angle")),
            passos=_inteiro(fill.get("numSteps")),
            ponto_medio=_real(fill.get("rateValue")),
            id_padrao=_inteiro(fill.get("patternId")),
            largura_repeticao=_inteiro(fill.get("tilingWidth")),
            altura_repeticao=_inteiro(fill.get("tilingHeight")),
            cores_intermediarias=cores_intermediarias,
            escala_x=_real(fill.get("xScale")),
            escala_y=_real(fill.get("yScale")),
        )
    transparencia_tipado = None
    if isinstance(transparencia, dict) and transparencia:
        fill_transparencia = transparencia.get("fill")
        codigo_fill = _inteiro(fill_transparencia.get("type")) if isinstance(fill_transparencia, dict) else None
        transparencia_tipado = TransparenciaObjeto(
            tipo="degrade" if codigo_fill == 2 else "uniforme",
            tipo_degrade={1: "linear", 2: "radial", 3: "conico", 4: "quadrado"}.get(
                _inteiro(fill_transparencia.get("fountainType"))
            ) if isinstance(fill_transparencia, dict) else None,
            uniforme=_real(transparencia.get("uniformTransparency")),
            inicio=_real(transparencia.get("startTransparency")),
            fim=_real(transparencia.get("endTransparency")),
            aplica_a=_inteiro(transparencia.get("appliesTo")),
            modo=_inteiro(transparencia.get("mode")),
            angulo=_real(fill_transparencia.get("angle")) if isinstance(fill_transparencia, dict) else None,
            passos=_inteiro(fill_transparencia.get("numSteps")) if isinstance(fill_transparencia, dict) else None,
            ponto_medio=_real(fill_transparencia.get("rateValue")) if isinstance(fill_transparencia, dict) else None,
        )
    return EstiloObjeto(preenchimento=preenchimento, transparencia=transparencia_tipado)


def _encontrar_nomes(data: bytes) -> list[tuple[int, str]]:
    """Varre `data` em busca de strings UTF-16LE terminadas em dois bytes
    zero, filtrando ruido binario que coincide com o padrao (comum em
    documentos com texto artistico — ver limitacoes no topo do modulo)."""
    achados: list[tuple[int, str]] = []
    i = 0
    limite = len(data) - 4
    while i < limite:
        j = i
        letras: list[str] = []
        while j + 1 < len(data) and 32 <= data[j] < 127 and data[j + 1] == 0:
            letras.append(chr(data[j]))
            j += 2
        if (
            len(letras) >= _TAMANHO_MINIMO_NOME
            and j + 1 < len(data)
            and data[j] == 0
            and data[j + 1] == 0
        ):
            nome = "".join(letras)
            proporcao = sum(c.isalpha() for c in nome) / len(nome)
            if proporcao >= _PROPORCAO_MINIMA_LETRAS:
                achados.append((i, nome))
            i = j + 2
        else:
            i += 1
    return achados


def _encontrar_jsons(data: bytes) -> list[tuple[int, dict]]:
    """Varre `data` em busca de blocos JSON de estilo (fill/outline/
    transparency), usando o prefixo de 4 bytes como tamanho exato."""
    achados: list[tuple[int, dict]] = []
    for m in _JSON_MARCADOR.finditer(data):
        inicio = m.start()
        if inicio < 4:
            continue
        tamanho = struct.unpack_from("<I", data, inicio - 4)[0]
        bruto = data[inicio:inicio + tamanho]
        try:
            estilo = json.loads(bruto)
        except (json.JSONDecodeError, UnicodeDecodeError):
            continue
        achados.append((inicio, estilo))
    return achados


def parse_estilos(data: bytes) -> list[tuple[int, dict]]:
    """Devolve TODOS os blocos de estilo (fill/outline/transparency) de
    page*.dat, com seu offset, independente de haver um nome associado.
    Mais confiavel que `parse_page()` quando o documento tem objetos sem
    nome (o caso comum em arquivos reais) — ver limitacoes no topo do
    modulo."""
    return _encontrar_jsons(data)


def parse_page(data: bytes) -> list[ItemNomeado]:
    """Extrai nomes (layers/objetos) e seus blocos de estilo, se houver.

    Nao decodifica geometria — ver docstring do modulo.
    """
    nomes = _encontrar_nomes(data)
    jsons = _encontrar_jsons(data)

    itens: list[ItemNomeado] = []
    for idx, (offset, nome) in enumerate(nomes):
        fim_do_escopo = nomes[idx + 1][0] if idx + 1 < len(nomes) else len(data)
        estilo = next(
            (j for (joff, j) in jsons if offset < joff < fim_do_escopo), None
        )
        itens.append(ItemNomeado(offset=offset, nome=nome, estilo=estilo))
    return itens
