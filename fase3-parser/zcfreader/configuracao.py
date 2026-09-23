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
MODOS = ("estrutural", "local", "automatico", "api", "camadas")
# Fluxo em camadas (sempre pelo OpenRouter): regras → modelo rápido → modelo forte.
MODELO_RAPIDO_PADRAO = "google/gemini-3.1-flash-lite"
MODELO_FORTE_PADRAO = "google/gemini-3.8-flash"
LIMITE_PEDIDO_PADRAO_USD = 0.08
# Servidor local compatível com a API da OpenAI (LM Studio, Ollama). Modelos
# escritos como "local:<nome>" são enviados para ele, sem chave e sem cobrança.
URL_SERVIDOR_LOCAL_PADRAO = "http://localhost:1234/v1"
PREFIXO_LOCAL = "local:"


def caminho_configuracao() -> Path:
    raiz = Path(os.environ.get("APPDATA") or Path.home()) / "LeitorPedidosCDR"
    return raiz / "config.json"


def carregar_configuracao() -> dict:
    padrao = {
        "modo": "estrutural", "provedor": "openai", "modelo": MODELOS_OPENAI[0],
        "modelo_openrouter": MODELOS_OPENROUTER[0],
        "modelo_rapido": MODELO_RAPIDO_PADRAO, "modelo_forte": MODELO_FORTE_PADRAO,
        "limite_pedido_usd": LIMITE_PEDIDO_PADRAO_USD,
        "url_servidor_local": URL_SERVIDOR_LOCAL_PADRAO,
        # O CDR no pacote de revisão permite reprocessar os casos com versões
        # futuras do leitor e, com volume suficiente, treinar um modelo próprio.
        "incluir_cdr_diagnostico": True,
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
    def id_modelo(chave: str) -> str:
        valor = dados.get(chave)
        valido = isinstance(valor, str) and ("/" in valor or valor.startswith(PREFIXO_LOCAL))
        return valor.strip() if valido else padrao[chave]

    try:
        limite = float(dados.get("limite_pedido_usd", padrao["limite_pedido_usd"]))
    except (TypeError, ValueError):
        limite = padrao["limite_pedido_usd"]
    return {
        "modo": modo, "provedor": provedor, "modelo": modelo,
        "modelo_openrouter": modelo_openrouter.strip(),
        "modelo_rapido": id_modelo("modelo_rapido"), "modelo_forte": id_modelo("modelo_forte"),
        "url_servidor_local": str(dados.get("url_servidor_local") or padrao["url_servidor_local"]).strip(),
        "incluir_cdr_diagnostico": dados.get("incluir_cdr_diagnostico", True) is not False,
        "limite_pedido_usd": limite if 0 < limite <= 1 else padrao["limite_pedido_usd"],
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
        "modelo_rapido": str(configuracao.get("modelo_rapido") or MODELO_RAPIDO_PADRAO).strip(),
        "modelo_forte": str(configuracao.get("modelo_forte") or MODELO_FORTE_PADRAO).strip(),
        "limite_pedido_usd": float(configuracao.get("limite_pedido_usd") or LIMITE_PEDIDO_PADRAO_USD),
        "url_servidor_local": str(configuracao.get("url_servidor_local") or URL_SERVIDOR_LOCAL_PADRAO).strip(),
        "incluir_cdr_diagnostico": configuracao.get("incluir_cdr_diagnostico", True) is not False,
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
