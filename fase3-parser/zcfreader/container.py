"""Abre um `.cdr` no formato ZCF (ZIP Container Format) e expoe seus
membros internos. O `.cdr` moderno do CorelDRAW e, na pratica, um ZIP
comum contendo `mimetype`, `content/root.dat`, `content/data/*.dat`,
XMLs de metadados e previews PNG — ver docs/evidencias-amostra-helo.md.
"""
from __future__ import annotations

import zipfile
import re
import struct
from dataclasses import replace
from pathlib import Path

MIMETYPE_ESPERADO = b"application/x-vnd.corel.zcf.draw.document+zip"


class ZcfContainer:
    """Wrapper fino sobre o ZIP interno de um `.cdr` ZCF."""

    def __init__(self, caminho):
        self.caminho = Path(caminho)
        self._zip = zipfile.ZipFile(self.caminho)

    def close(self) -> None:
        self._zip.close()

    def __enter__(self) -> "ZcfContainer":
        return self

    def __exit__(self, *exc) -> None:
        self.close()

    def read(self, membro: str) -> bytes:
        return self._zip.read(membro)

    def namelist(self) -> list[str]:
        return self._zip.namelist()

    def tem_membro(self, membro: str) -> bool:
        return membro in self._zip.namelist()

    @property
    def arquivos_de_dados(self) -> list[str]:
        """Nomes listados em content/dataFileList.dat (relativos a
        content/data/), na ordem em que aparecem no indice."""
        if not self.tem_membro("content/dataFileList.dat"):
            return []
        bruto = self.read("content/dataFileList.dat").decode("ascii", errors="replace")
        return [linha.strip() for linha in bruto.splitlines() if linha.strip()]

    def bitmaps(self):
        """Decodifica content/data/Bitmaps.dat, se presente no documento.
        Devolve None se o documento nao tiver nenhum bitmap."""
        if not self.tem_membro("content/data/Bitmaps.dat"):
            return None
        from .bitmaps import parse_bitmaps
        return parse_bitmaps(self.read("content/data/Bitmaps.dat"))

    def instancias_bitmaps(self, bitmaps=None):
        """Localiza cada uso dos bitmaps unicos dentro do documento.

        Devolve uma lista vazia quando nao ha ``Bitmaps.dat``. As referencias
        podem estar em ``pageN.dat`` ou ``dataN.dat`` (por exemplo, conteudo
        interno de PowerClip).
        """
        if bitmaps is None:
            bitmaps = self.bitmaps()
        if bitmaps is None:
            return []
        from .references import parse_instancias_bitmap

        padrao = re.compile(r"^content/data/(?:page\d+|data\d+|masterPage)\.dat$")
        instancias = []
        for membro in self.namelist():
            if padrao.match(membro):
                instancias.extend(
                    parse_instancias_bitmap(self.read(membro), membro, bitmaps)
                )
        objetos = self.estrutura()
        enriquecidas = []
        for instancia in instancias:
            candidatos = [
                objeto
                for objeto in objetos
                if objeto.membro == instancia.membro
                and objeto.offset_dados is not None
                and objeto.tamanho_dados is not None
                and objeto.offset_dados <= instancia.offset
                < objeto.offset_dados + objeto.tamanho_dados
            ]
            # Em caso de aninhamento/intervalos sobrepostos, o menor blob e o
            # dono mais especifico da instancia.
            objeto = min(candidatos, key=lambda o: o.tamanho_dados) if candidatos else None
            enriquecidas.append(replace(instancia, objeto=objeto))
        return enriquecidas

    def estrutura(self):
        """Decodifica a arvore RIFF de ``content/root.dat``."""
        if not self.tem_membro("content/root.dat"):
            return []
        from .structure import parse_estrutura

        return parse_estrutura(self.read("content/root.dat"), self._streams_estrutura())

    def _streams_estrutura(self):
        # Os IDs usados por root.dat sao os indices zero-based de
        # dataFileList.dat. Bitmaps.dat ocupa um indice quando aparece na
        # lista, embora suas imagens usem um indice interno proprio.
        streams = {}
        for indice, nome in enumerate(self.arquivos_de_dados):
            if nome == "Bitmaps.dat":
                continue
            membro = f"content/data/{nome}"
            if self.tem_membro(membro):
                streams[indice] = (membro, self.read(membro))
        return streams

    def paginas_estruturais(self):
        """Tamanhos individuais e sangria das paginas do documento."""
        if not self.tem_membro("content/root.dat"):
            return []
        from .structure import parse_paginas

        largura = altura = sangria = 0
        if self.tem_membro("content/data/data1.dat"):
            data1 = self.read("content/data/data1.dat")
            if len(data1) >= 46:
                largura, altura = struct.unpack_from("<II", data1, 12)
                sangria = struct.unpack_from("<I", data1, 42)[0]
        if largura <= 0 or altura <= 0:
            metadata = self.metadados()
            largura = metadata.largura_pagina_unidades if metadata else 0
            altura = metadata.altura_pagina_unidades if metadata else 0
        if not largura or not altura:
            return []
        return parse_paginas(
            self.read("content/root.dat"),
            self._streams_estrutura(),
            largura,
            altura,
            sangria,
        )

    def camadas(self):
        """Layers, propriedades de visibilidade/impressão e contagem de objetos."""
        if not self.tem_membro("content/root.dat"):
            return []
        from .structure import parse_camadas

        return parse_camadas(self.read("content/root.dat"), self._streams_estrutura())

    def conferencia_limites(self, tolerancia_mm: float = 0.1):
        """Lista objetos que excedem os limites nominais da pagina.

        O formato usa coordenadas locais aproximadamente centradas em zero.
        A tolerancia padrao de 0,1 mm absorve os pequenos deslocamentos de
        arredondamento observados nos casos controlados.
        """
        from .structure import OcorrenciaLimitePagina

        paginas = {pagina.indice: pagina for pagina in self.paginas_estruturais()}
        tolerancia = tolerancia_mm * 10_000.0
        ocorrencias = []
        for objeto in self.estrutura():
            if objeto.tipo != "obj" or objeto.caixa is None or objeto.pagina not in paginas:
                continue
            pagina = paginas[objeto.pagina]
            caixa = objeto.caixa
            esquerda = max(0.0, pagina.limite_esquerdo_nominal - caixa.esquerda)
            direita = max(0.0, caixa.direita - pagina.limite_direito_nominal)
            topo = max(0.0, caixa.topo - pagina.limite_superior_nominal)
            base = max(0.0, pagina.limite_inferior_nominal - caixa.base)
            if any(valor > tolerancia for valor in (esquerda, direita, topo, base)):
                ultrapassa_sangria = any(
                    valor > pagina.sangria_unidades + tolerancia
                    for valor in (esquerda, direita, topo, base)
                )
                ocorrencias.append(
                    OcorrenciaLimitePagina(
                        objeto=objeto,
                        pagina=pagina,
                        excede_esquerda_mm=esquerda / 10_000.0,
                        excede_direita_mm=direita / 10_000.0,
                        excede_topo_mm=topo / 10_000.0,
                        excede_base_mm=base / 10_000.0,
                        ultrapassa_sangria=ultrapassa_sangria,
                    )
                )
        return ocorrencias

    def curvas_com_subcaminhos_abertos(self):
        """Lista objetos curva que possuem ao menos um subcaminho aberto."""
        return [
            objeto for objeto in self.estrutura()
            if objeto.tipo == "obj"
            and objeto.geometria_curva is not None
            and objeto.geometria_curva.possui_subcaminho_aberto
        ]

    def metadados(self):
        """Le o resumo XMP de ``META-INF/metadata.xml``.

        Inclui tamanho nominal da pagina, contagens de paginas/layers/
        objetos, fontes usadas e versao do CorelDRAW. Devolve ``None`` em
        contêineres ZCF que nao tenham esse membro.
        """
        if not self.tem_membro("META-INF/metadata.xml"):
            return None
        from .metadata import parse_metadata
        return parse_metadata(self.read("META-INF/metadata.xml"))

    def textos(self):
        """Conteúdo textual agregado de ``META-INF/textinfo.xml``.

        Devolve os fluxos na ordem do XML. Fonte e tamanho por objeto ficam
        disponíveis em ``objeto.estilos_texto`` na árvore estrutural.
        """
        if not self.tem_membro("META-INF/textinfo.xml"):
            return ()
        from .text import parse_textinfo

        return parse_textinfo(self.read("META-INF/textinfo.xml"))

    def textos_por_objeto(self):
        """Associa cada fluxo ao objeto textual na ordem estrutural.

        Devolve ``None`` quando as contagens divergem, evitando uma associação
        parcial ou adivinhada em variantes ainda não estudadas do formato.
        """
        from .text import TextoEstruturado

        fluxos = self.textos()
        objetos = tuple(
            objeto for objeto in self.estrutura()
            if objeto.tipo == "obj" and objeto.tipo_objeto == "texto"
        )
        if len(fluxos) != len(objetos):
            return None
        return tuple(
            TextoEstruturado(objeto=objeto, fluxo=fluxo)
            for objeto, fluxo in zip(objetos, fluxos)
        )

    def pagina(self, indice: int = 1):
        """Extrai nomes e estilos (fill/outline/transparency) de
        content/data/page{indice}.dat — ver zcfreader.page para o que e
        extraido e as limitacoes (nao ha parser de geometria ainda, e o
        pareamento nome->estilo so e confiavel se todo objeto tem nome).
        Devolve None se a pagina nao existir."""
        membro = f"content/data/page{indice}.dat"
        if not self.tem_membro(membro):
            return None
        from .page import parse_page
        return parse_page(self.read(membro))

    def estilos_da_pagina(self, indice: int = 1):
        """Devolve TODOS os blocos de estilo (fill/outline/transparency)
        de content/data/page{indice}.dat, com offset, sem depender de o
        objeto ter nome — mais confiavel que `.pagina()` em documentos
        reais, onde a maioria dos objetos nao e nomeada. Devolve None se
        a pagina nao existir."""
        membro = f"content/data/page{indice}.dat"
        if not self.tem_membro(membro):
            return None
        from .page import parse_estilos
        return parse_estilos(self.read(membro))


def abrir_cdr(caminho) -> ZcfContainer:
    """Abre um arquivo `.cdr` (ou `.zip` equivalente) para leitura."""
    return ZcfContainer(caminho)
