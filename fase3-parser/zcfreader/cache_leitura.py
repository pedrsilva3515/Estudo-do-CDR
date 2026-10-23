"""Cache em disco das etapas lentas da leitura de um CDR, para a régua.

Ler as peças, desenhar a página e passar o OCR levam de segundos a minutos por
pedido; as regras que vêm depois levam milissegundos. Nas rodadas da régua em
que só as regras mudam, essas três etapas dão sempre o mesmo resultado.

A chave de cada resultado é o conteúdo da entrada (bytes do CDR ou da imagem)
mais uma "versão" calculada do código-fonte do módulo e de todos os módulos do
zcfreader que ele importa: mudou o código que produz o resultado, o cache antigo
deixa de ser usado sozinho. Nada disso é ativado na macro nem no aplicativo,
só por quem chama ``ativar``.
"""
from __future__ import annotations

import ast
import hashlib
import pickle
from functools import lru_cache, wraps
from pathlib import Path

PACOTE = Path(__file__).resolve().parent


@lru_cache(maxsize=None)
def _imports_locais(modulo: str) -> frozenset[str]:
    arvore = ast.parse((PACOTE / f"{modulo}.py").read_text(encoding="utf-8"))
    nomes = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.ImportFrom) and no.level == 1:
            if no.module:
                nomes.add(no.module.split(".")[0])
            else:
                nomes.update(alias.name for alias in no.names)
    return frozenset(n for n in nomes if (PACOTE / f"{n}.py").is_file())


@lru_cache(maxsize=None)
def versao_codigo(modulo: str) -> str:
    """Hash do código do módulo e de tudo o que ele importa do zcfreader, transitivamente."""
    vistos, pendentes = set(), [modulo]
    while pendentes:
        atual = pendentes.pop()
        if atual in vistos:
            continue
        vistos.add(atual)
        pendentes.extend(_imports_locais(atual))
    soma = hashlib.sha256()
    for nome in sorted(vistos):
        soma.update(nome.encode())
        soma.update((PACOTE / f"{nome}.py").read_bytes())
    return soma.hexdigest()[:16]


def _guardado(pasta: Path, etapa: str, modulo: str, funcao):
    """Embrulha ``funcao(entrada, *args)``: entrada é um caminho de arquivo ou bytes."""
    @wraps(funcao)
    def embrulho(entrada, *args, **kwargs):
        dados = entrada if isinstance(entrada, (bytes, bytearray)) else Path(entrada).read_bytes()
        chave = hashlib.sha256(dados).hexdigest()
        extra = hashlib.sha256(repr((args, sorted(kwargs.items()))).encode()).hexdigest()[:8]
        arquivo = pasta / etapa / f"{chave}-{versao_codigo(modulo)}-{extra}.pkl"
        if arquivo.is_file():
            try:
                return pickle.loads(arquivo.read_bytes())
            except Exception:  # arquivo truncado por uma rodada interrompida
                pass
        resultado = funcao(entrada, *args, **kwargs)
        arquivo.parent.mkdir(parents=True, exist_ok=True)
        temporario = arquivo.with_suffix(".tmp")
        temporario.write_bytes(pickle.dumps(resultado))
        temporario.replace(arquivo)
        return resultado
    return embrulho


def ativar(pasta: Path) -> None:
    """Liga o cache de: peças do CDR, desenho da página e OCR."""
    from . import agente, experimento_agente, modelos_locais, ocr, render_proprio, visao_api

    pasta = Path(pasta)
    render_proprio.renderizar_pagina = _guardado(pasta, "pagina", "render_proprio", render_proprio.renderizar_pagina)
    ocr_guardado = _guardado(pasta, "ocr", "ocr", ocr.executar_ocr)
    # Quem fez "from .ocr import executar_ocr" guardou a função original no próprio módulo.
    for modulo in (ocr, experimento_agente, modelos_locais, visao_api):
        modulo.executar_ocr = ocr_guardado
    candidatos = _guardado(pasta, "pecas", "experimento_agente", experimento_agente.extrair_candidatos_agente)
    for modulo in (experimento_agente, agente):
        modulo.extrair_candidatos_agente = candidatos
