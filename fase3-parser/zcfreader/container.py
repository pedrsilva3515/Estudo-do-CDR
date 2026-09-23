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

    def _primeiro_membro(self, *candidatos: str) -> str | None:
        """Resolve variantes de caminho observadas entre versões do CorelDRAW."""
        nomes = set(self._zip.namelist())
        return next((nome for nome in candidatos if nome in nomes), None)

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

    def recipientes_powerclip(self, estrutura=None) -> dict:
        """Mapa (membro, offset_root) do objeto contido -> objeto recipiente do PowerClip.

        O conteúdo de um PowerClip fica num grupo de topo de ``dataN.dat`` cujo
        ``id_estrutural`` é apontado por ``grupo_powerclip`` do recipiente. Os
        objetos seguintes com ancestrais pertencem a esse grupo.
        """
        estrutura = list(self.estrutura() if estrutura is None else estrutura)
        recipientes = {
            objeto.grupo_powerclip: objeto for objeto in estrutura
            if objeto.grupo_powerclip is not None and objeto.caixa is not None
        }
        mapa = {}
        atual = None
        for objeto in estrutura:
            if not objeto.ancestrais:
                atual = recipientes.get(objeto.id_estrutural) if objeto.tipo == "grp" else None
            if atual is not None and objeto is not atual:
                mapa[(objeto.membro, objeto.offset_root)] = atual
        return mapa

    def cadeias_powerclip(self, estrutura=None) -> dict:
        """Mapa objeto -> todos os recipientes que o recortam, do mais próximo ao mais externo.

        PowerClips podem ser aninhados: o recipiente de uma foto pode estar,
        ele mesmo, dentro do conteúdo de outro PowerClip. Só aparece o que está
        dentro de todas as máscaras da cadeia.
        """
        estrutura = list(self.estrutura() if estrutura is None else estrutura)
        imediatos = self.recipientes_powerclip(estrutura)
        cadeias = {}
        for chave, recipiente in imediatos.items():
            cadeia, vistos = [], set()
            atual = recipiente
            while atual is not None and (atual.membro, atual.offset_root) not in vistos:
                vistos.add((atual.membro, atual.offset_root))
                cadeia.append(atual)
                atual = imediatos.get((atual.membro, atual.offset_root))
            cadeias[chave] = cadeia
        return cadeias

    def limites_conteudo(self, estrutura_visivel=None):
        """Caixa (unidades do CDR) que envolve o que aparece na montagem.

        Referência única para converter centímetros em pixels: o desenho da
        página, o OCR, a prévia e a escolha da peça precisam usar a mesma.
        Usa as caixas visíveis (conteúdo de PowerClip recortado pela máscara).
        """
        from .structure import CaixaObjeto

        estrutura = list(self.estrutura_visivel() if estrutura_visivel is None else estrutura_visivel)
        caixas = [
            objeto.caixa for objeto in estrutura
            if objeto.caixa is not None and not objeto.ancestrais and objeto.tipo in {"obj", "grp"}
        ]
        if not caixas:
            return None
        return CaixaObjeto(
            esquerda=min(c.esquerda for c in caixas), topo=max(c.topo for c in caixas),
            direita=max(c.direita for c in caixas), base=min(c.base for c in caixas),
        )

    def estrutura_visivel(self):
        """Estrutura com a caixa do conteúdo de PowerClip recortada pela máscara.

        Só a parte dentro do recipiente é impressa; a caixa integral do conteúdo
        (por exemplo, uma foto maior que o círculo que a recorta) não é a medida
        do produto.
        """
        from dataclasses import replace

        from .structure import CaixaObjeto

        estrutura = list(self.estrutura())
        cadeias = self.cadeias_powerclip(estrutura)
        visivel = []
        for objeto in estrutura:
            cadeia = cadeias.get((objeto.membro, objeto.offset_root))
            if cadeia and objeto.caixa is not None:
                esquerda, direita = objeto.caixa.esquerda, objeto.caixa.direita
                base, topo = objeto.caixa.base, objeto.caixa.topo
                for recipiente in cadeia:  # recorta por todas as máscaras aninhadas
                    b = recipiente.caixa
                    esquerda, direita = max(esquerda, b.esquerda), min(direita, b.direita)
                    base, topo = max(base, b.base), min(topo, b.topo)
                caixa = CaixaObjeto(esquerda=esquerda, topo=topo, direita=direita, base=base) \
                    if esquerda < direita and base < topo else None
                objeto = replace(objeto, caixa=caixa)
            visivel.append(objeto)
        return visivel

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
        membro = self._primeiro_membro(
            "META-INF/metadata.xml",
            "metadata/metadata.xml",
        )
        if membro is None:
            return None
        from .metadata import parse_metadata
        return parse_metadata(self.read(membro))

    def contexto_cor(self):
        """Lê o modelo e o intento ICC em ``color/color.xml``."""
        if not self.tem_membro("color/color.xml"):
            return None
        from .color import parse_contexto_cor
        return parse_contexto_cor(self.read("color/color.xml"))

    def textos(self):
        """Conteúdo textual agregado de ``META-INF/textinfo.xml``.

        Devolve os fluxos na ordem do XML. Fonte e tamanho por objeto ficam
        disponíveis em ``objeto.estilos_texto`` na árvore estrutural.
        """
        membro = self._primeiro_membro(
            "META-INF/textinfo.xml",
            "metadata/textinfo.xml",
        )
        if membro is None:
            return ()
        from .text import parse_textinfo

        return parse_textinfo(self.read(membro))

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
        atribuicao = self._associar_textos_por_conteudo(objetos, fluxos)
        # O que não for achado pelo conteúdo segue a ordem, entre os que sobraram.
        livres = iter(j for j in range(len(fluxos)) if j not in set(atribuicao.values()))
        return tuple(
            TextoEstruturado(objeto=objeto, fluxo=fluxos[atribuicao[i] if i in atribuicao else next(livres)])
            for i, objeto in enumerate(objetos)
        )

    def _associar_textos_por_conteudo(self, objetos, fluxos) -> dict[int, int]:
        """Índice do objeto -> índice do fluxo, pelo texto gravado após o objeto.

        textinfo.xml não referencia objetos, e sua ordem difere da estrutural
        quando há texto dentro de PowerClip (a página vem antes do conteúdo em
        dataN.dat). O conteúdo de cada texto fica gravado logo depois do bloco
        do objeto, em cp1252 com prefixo de tamanho, antes do próximo objeto de
        texto do mesmo membro.
        """
        dados_membro: dict[str, bytes] = {}
        ordenados = sorted(
            (i for i, o in enumerate(objetos) if o.membro and o.offset_dados is not None),
            key=lambda i: (objetos[i].membro, objetos[i].offset_dados),
        )
        janelas: dict[int, bytes] = {}
        for posicao, i in enumerate(ordenados):
            objeto = objetos[i]
            if objeto.membro not in dados_membro:
                dados_membro[objeto.membro] = self.read(objeto.membro)
            dados = dados_membro[objeto.membro]
            proximo = next(
                (objetos[k].offset_dados for k in ordenados[posicao + 1:] if objetos[k].membro == objeto.membro),
                len(dados),
            )
            janelas[i] = dados[objeto.offset_dados:proximo]

        def chaves(texto: str) -> list[bytes]:
            linha = next((l.strip() for l in texto.splitlines() if l.strip()), "")[:24]
            if not linha:
                return []
            resultado = []
            for codificacao in ("cp1252", "utf-16-le", "utf-8"):
                try:
                    resultado.append(linha.encode(codificacao))
                except UnicodeEncodeError:
                    continue
            return resultado

        chaves_fluxo = [chaves(f.texto) for f in fluxos]
        candidatos = {
            i: [j for j, alternativas in enumerate(chaves_fluxo) if any(c in janela for c in alternativas)]
            for i, janela in janelas.items()
        }
        atribuicao: dict[int, int] = {}
        usados: set[int] = set()
        for i in sorted(candidatos, key=lambda i: (len(candidatos[i]), i)):
            j = next((j for j in candidatos[i] if j not in usados), None)
            if j is not None:
                atribuicao[i] = j
                usados.add(j)
        return atribuicao

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

    def estilos_tipados_da_pagina(self, indice: int = 1):
        """Devolve os estilos da página em campos tipados, com seus offsets.

        A lista conserva todos os objetos, inclusive os sem nome, como
        ``estilos_da_pagina()``. A leitura confirmada por enquanto cobre
        preenchimento uniforme/ausente, cores CMYK/RGB e transparência uniforme.
        """
        estilos = self.estilos_da_pagina(indice)
        if estilos is None:
            return None
        from .page import parse_estilo_objeto
        return [(offset, parse_estilo_objeto(estilo)) for offset, estilo in estilos]


def abrir_cdr(caminho) -> ZcfContainer:
    """Abre um arquivo `.cdr` (ou `.zip` equivalente) para leitura."""
    return ZcfContainer(caminho)
