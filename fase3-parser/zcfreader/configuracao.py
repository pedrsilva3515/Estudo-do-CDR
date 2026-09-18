"""Configuração local e armazenamento seguro de credenciais da interface."""
from __future__ import annotations

import json
import os
from pathlib import Path


SERVICO_CREDENCIAL = "LeitorPedidosCDR"
USUARIO_OPENAI = "openai_api_key"
MODELOS_OPENAI = ("gpt-5.6-luna", "gpt-5.6-terra", "gpt-5.6-sol")
MODOS = ("estrutural", "local", "automatico", "api")


def caminho_configuracao() -> Path:
    raiz = Path(os.environ.get("APPDATA") or Path.home()) / "LeitorPedidosCDR"
    return raiz / "config.json"


def carregar_configuracao() -> dict:
    padrao = {"modo": "estrutural", "provedor": "openai", "modelo": MODELOS_OPENAI[0]}
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
    return {"modo": modo, "provedor": "openai", "modelo": modelo}


def salvar_configuracao(configuracao: dict) -> None:
    caminho = caminho_configuracao()
    caminho.parent.mkdir(parents=True, exist_ok=True)
    publico = {
        "versao_config": 2,
        "modo": configuracao.get("modo", "estrutural"),
        "provedor": "openai",
        "modelo": configuracao.get("modelo", MODELOS_OPENAI[0]),
    }
    caminho.write_text(json.dumps(publico, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def obter_chave_openai() -> str | None:
    try:
        import keyring
        return keyring.get_password(SERVICO_CREDENCIAL, USUARIO_OPENAI)
    except Exception:
        return os.environ.get("OPENAI_API_KEY")


def salvar_chave_openai(chave: str) -> None:
    import keyring
    if chave.strip():
        keyring.set_password(SERVICO_CREDENCIAL, USUARIO_OPENAI, chave.strip())
    else:
        try:
            keyring.delete_password(SERVICO_CREDENCIAL, USUARIO_OPENAI)
        except keyring.errors.PasswordDeleteError:
            pass
