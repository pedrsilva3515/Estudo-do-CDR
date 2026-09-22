"""Configuração local e armazenamento seguro de credenciais da interface."""
from __future__ import annotations

import json
import os
from pathlib import Path


SERVICO_CREDENCIAL = "LeitorPedidosCDR"
USUARIO_OPENAI = "openai_api_key"
USUARIO_OPENROUTER = "openrouter_api_key"
MODELOS_OPENAI = ("gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.6-sol")
# Sugestões com entrada de imagem no OpenRouter; o campo aceita qualquer ID
# de https://openrouter.ai/models.
MODELOS_OPENROUTER = (
    "anthropic/claude-sonnet-5",
    "anthropic/claude-opus-5",
    "openai/gpt-5.6-sol",
    "google/gemini-3.5-flash",
    "qwen/qwen3.8-max-0902",
)
PROVEDORES = ("openai", "openrouter")
MODOS = ("estrutural", "local", "automatico", "api")


def caminho_configuracao() -> Path:
    raiz = Path(os.environ.get("APPDATA") or Path.home()) / "LeitorPedidosCDR"
    return raiz / "config.json"


def carregar_configuracao() -> dict:
    padrao = {
        "modo": "estrutural", "provedor": "openai", "modelo": MODELOS_OPENAI[0],
        "modelo_openrouter": MODELOS_OPENROUTER[0],
        "arquitetura_regional_experimental": False,
    }
    caminho = caminho_configuracao()
    if not caminho.is_file():
        return padrao
    try:
        dados = json.loads(caminho.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return padrao
    modo = dados.get("modo") if dados.get("modo") in MODOS else padrao["modo"]
    # Na v0.4, "local" significava somente regras estruturais. Preserve esse
    # comportamento ao migrar; na v0.5 o nome passa a significar IA local real.
    if dados.get("versao_config", 1) < 2 and modo == "local":
        modo = "estrutural"
    modelo = dados.get("modelo") if dados.get("modelo") in MODELOS_OPENAI else padrao["modelo"]
    provedor = dados.get("provedor") if dados.get("provedor") in PROVEDORES else padrao["provedor"]
    modelo_openrouter = dados.get("modelo_openrouter")
    if not isinstance(modelo_openrouter, str) or "/" not in modelo_openrouter.strip():
        modelo_openrouter = padrao["modelo_openrouter"]
    return {
        "modo": modo, "provedor": provedor, "modelo": modelo,
        "modelo_openrouter": modelo_openrouter.strip(),
        "arquitetura_regional_experimental": dados.get("arquitetura_regional_experimental") is True,
    }


def salvar_configuracao(configuracao: dict) -> None:
    caminho = caminho_configuracao()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    publico = {
        "versao_config": 4,
        "modo": configuracao.get("modo", "estrutural"),
        "provedor": configuracao.get("provedor") if configuracao.get("provedor") in PROVEDORES else "openai",
        "modelo": configuracao.get("modelo", MODELOS_OPENAI[0]),
        "modelo_openrouter": str(configuracao.get("modelo_openrouter") or MODELOS_OPENROUTER[0]).strip(),
        "arquitetura_regional_experimental": configuracao.get("arquitetura_regional_experimental") is True,
    }
    caminho.write_text(json.dumps(publico, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


_CREDENCIAIS = {
    "openai": (USUARIO_OPENAI, "OPENAI_API_KEY"),
    "openrouter": (USUARIO_OPENROUTER, "OPENROUTER_API_KEY"),
}


def modelo_do_provedor(configuracao: dict) -> str:
    if configuracao.get("provedor") == "openrouter":
        return configuracao.get("modelo_openrouter") or MODELOS_OPENROUTER[0]
    return configuracao.get("modelo") or MODELOS_OPENAI[0]


def obter_chave(provedor: str) -> str | None:
    usuario, variavel = _CREDENCIAIS[provedor]
    try:
        import keyring
        chave = keyring.get_password(SERVICO_CREDENCIAL, usuario)
    except Exception:
        chave = None
    return chave or os.environ.get(variavel)


def salvar_chave(provedor: str, chave: str) -> None:
    import keyring
    usuario, _ = _CREDENCIAIS[provedor]
    if chave.strip():
        keyring.set_password(SERVICO_CREDENCIAL, usuario, chave.strip())
    else:
        try:
            keyring.delete_password(SERVICO_CREDENCIAL, usuario)
        except keyring.errors.PasswordDeleteError:
            pass


def obter_chave_openai() -> str | None:
    return obter_chave("openai")


def salvar_chave_openai(chave: str) -> None:
    salvar_chave("openai", chave)
