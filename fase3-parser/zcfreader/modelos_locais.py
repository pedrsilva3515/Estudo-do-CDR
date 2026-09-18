"""Download, instalação e execução do modelo visual local em CPU."""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import Callable
from urllib.request import Request, urlopen
from zipfile import ZipFile

from .visao_api import _schema_resposta, extrair_preview


NOME_MODELO = "Qwen2.5-VL 3B (Q4_K_M)"
ARQUIVO_MODELO = "Qwen2.5-VL-3B-Instruct-Q4_K_M.gguf"
ARQUIVO_MMPROJ = "mmproj-Qwen2.5-VL-3B-Instruct-Q8_0.gguf"
TAMANHO_MODELO = 1_929_901_056
TAMANHO_MMPROJ = 844_757_728
TAMANHO_TOTAL_MODELOS = TAMANHO_MODELO + TAMANHO_MMPROJ
URL_BASE = "https://huggingface.co/ggml-org/Qwen2.5-VL-3B-Instruct-GGUF/resolve/main"
URL_MODELO = f"{URL_BASE}/{ARQUIVO_MODELO}?download=true"
URL_MMPROJ = f"{URL_BASE}/{ARQUIVO_MMPROJ}?download=true"
API_RELEASES_LLAMA = "https://api.github.com/repos/ggml-org/llama.cpp/releases?per_page=10"
ProgressCallback = Callable[[str, int, int], None]


def diretorio_modelos() -> Path:
    raiz = Path(os.environ.get("LOCALAPPDATA") or Path.home()) / "LeitorPedidosCDR"
    return raiz / "modelos" / "qwen25-vl-3b"


def caminhos_instalacao() -> dict[str, Path]:
    raiz = diretorio_modelos()
    return {
        "modelo": raiz / ARQUIVO_MODELO,
        "mmproj": raiz / ARQUIVO_MMPROJ,
        "executavel": raiz / "runtime" / "llama-mtmd-cli.exe",
    }


def modelo_instalado() -> bool:
    caminhos = caminhos_instalacao()
    return (
        caminhos["modelo"].is_file()
        and caminhos["modelo"].stat().st_size == TAMANHO_MODELO
        and caminhos["mmproj"].is_file()
        and caminhos["mmproj"].stat().st_size == TAMANHO_MMPROJ
        and caminhos["executavel"].is_file()
    )


def _baixar(url: str, destino: Path, etapa: str, progresso: ProgressCallback | None = None) -> None:
    destino.parent.mkdir(parents=True, exist_ok=True)
    parcial = destino.with_suffix(destino.suffix + ".part")
    inicio = parcial.stat().st_size if parcial.exists() else 0
    cabecalhos = {"User-Agent": "LeitorPedidosCDR/0.5"}
    if inicio:
        cabecalhos["Range"] = f"bytes={inicio}-"
    resposta = urlopen(Request(url, headers=cabecalhos), timeout=60)
    if inicio and getattr(resposta, "status", 200) != 206:
        inicio = 0
        parcial.unlink(missing_ok=True)
    restante = int(resposta.headers.get("Content-Length", "0"))
    total = inicio + restante
    modo = "ab" if inicio else "wb"
    recebido = inicio
    with resposta, parcial.open(modo) as saida:
        while True:
            bloco = resposta.read(1024 * 1024)
            if not bloco:
                break
            saida.write(bloco)
            recebido += len(bloco)
            if progresso:
                progresso(etapa, recebido, total)
    parcial.replace(destino)


def _asset_runtime() -> tuple[str, str]:
    requisicao = Request(API_RELEASES_LLAMA, headers={"User-Agent": "LeitorPedidosCDR/0.5"})
    with urlopen(requisicao, timeout=30) as resposta:
        releases = json.load(resposta)
    padrao = re.compile(r"^llama-.+-bin-win-cpu-x64\.zip$", re.IGNORECASE)
    for release in releases:
        for asset in release.get("assets", []):
            if padrao.match(asset.get("name", "")):
                return asset["browser_download_url"], asset["name"]
    raise RuntimeError("Não foi possível localizar o runtime CPU do llama.cpp para Windows x64.")


def _extrair_runtime(zip_path: Path, destino: Path) -> None:
    temporario = destino.parent / "runtime-novo"
    if temporario.exists():
        shutil.rmtree(temporario)
    temporario.mkdir(parents=True)
    with ZipFile(zip_path) as arquivo:
        raiz_resolvida = temporario.resolve()
        for membro in arquivo.infolist():
            alvo = (temporario / membro.filename).resolve()
            if raiz_resolvida not in alvo.parents and alvo != raiz_resolvida:
                raise RuntimeError("Pacote de runtime inválido.")
        arquivo.extractall(temporario)
    executavel = next(temporario.rglob("llama-mtmd-cli.exe"), None)
    if executavel is None:
        raise RuntimeError("O runtime baixado não contém llama-mtmd-cli.exe.")
    if destino.exists():
        shutil.rmtree(destino)
    temporario.replace(destino)


def instalar_modelo(progresso: ProgressCallback | None = None) -> None:
    """Instala os dois GGUF e o runtime CPU; downloads interrompidos são retomados."""
    caminhos = caminhos_instalacao()
    raiz = diretorio_modelos()
    raiz.mkdir(parents=True, exist_ok=True)
    livres = shutil.disk_usage(raiz).free
    faltante = sum(
        tamanho for chave, tamanho in (("modelo", TAMANHO_MODELO), ("mmproj", TAMANHO_MMPROJ))
        if not caminhos[chave].exists() or caminhos[chave].stat().st_size != tamanho
    )
    if livres < faltante + 500_000_000:
        raise RuntimeError("Espaço insuficiente. Libere pelo menos 3,3 GB no disco e tente novamente.")

    for chave, url, tamanho, etapa in (
        ("modelo", URL_MODELO, TAMANHO_MODELO, "Modelo visual"),
        ("mmproj", URL_MMPROJ, TAMANHO_MMPROJ, "Componente de visão"),
    ):
        destino = caminhos[chave]
        if destino.exists() and destino.stat().st_size == tamanho:
            if progresso:
                progresso(etapa, tamanho, tamanho)
            continue
        _baixar(url, destino, etapa, progresso)
        if destino.stat().st_size != tamanho:
            destino.unlink(missing_ok=True)
            raise RuntimeError(f"O download de {etapa.lower()} ficou incompleto. Tente novamente.")

    if not caminhos["executavel"].is_file():
        url_runtime, nome_zip = _asset_runtime()
        zip_path = raiz / nome_zip
        _baixar(url_runtime, zip_path, "Runtime CPU", progresso)
        _extrair_runtime(zip_path, caminhos["executavel"].parent)
        zip_path.unlink(missing_ok=True)
    if not modelo_instalado():
        raise RuntimeError("A instalação terminou, mas os arquivos não passaram pela verificação.")


def _extrair_json(texto: str) -> dict:
    decodificador = json.JSONDecoder()
    candidatos: list[dict] = []
    for posicao, caractere in enumerate(texto):
        if caractere != "{":
            continue
        try:
            valor, _ = decodificador.raw_decode(texto[posicao:])
        except json.JSONDecodeError:
            continue
        if isinstance(valor, dict):
            candidatos.append(valor)
    if not candidatos:
        raise RuntimeError("O modelo local não devolveu um resultado JSON válido.")
    return candidatos[-1]


def analisar_com_modelo_local(caminho: Path, resultado_estrutural: dict) -> dict:
    if not modelo_instalado():
        raise RuntimeError("O modelo local ainda não foi baixado. Abra 'Configurar IA' para instalá-lo.")
    preview = extrair_preview(caminho)
    if preview is None:
        raise RuntimeError("O CDR não contém um preview PNG utilizável pela análise visual local.")
    bytes_imagem, _ = preview
    caminhos = caminhos_instalacao()
    evidencias = json.dumps(resultado_estrutural, ensure_ascii=False, separators=(",", ":"))
    prompt = (
        "Interprete este pedido de gráfica em português. Leia textos visíveis, inclusive texto convertido "
        "em curvas. Associe quantidade, material e acabamento a cada item detectado no JSON estrutural. "
        "Não recalcule dimensões pela imagem e não invente informação ilegível; use null. Responda apenas "
        "com o JSON solicitado. Evidências estruturais: " + evidencias
    )
    with tempfile.TemporaryDirectory(prefix="cdr-pedido-") as pasta:
        imagem = Path(pasta) / "preview.png"
        imagem.write_bytes(bytes_imagem)
        prompt_path = Path(pasta) / "prompt.txt"
        prompt_path.write_text(prompt, encoding="utf-8")
        schema_path = Path(pasta) / "schema.json"
        schema_path.write_text(json.dumps(_schema_resposta(), ensure_ascii=False), encoding="utf-8")
        comando = [
            str(caminhos["executavel"]), "-m", str(caminhos["modelo"]),
            "--mmproj", str(caminhos["mmproj"]), "--image", str(imagem),
            "--no-mmproj-offload", "--device", "none", "--ctx-size", "8192",
            "--image-max-tokens", "1024", "--temp", "0", "--seed", "1",
            "--predict", "1400", "--json-schema-file", str(schema_path),
            "--log-disable", "--file", str(prompt_path),
        ]
        flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
        processo = subprocess.run(
            comando, capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=900, creationflags=flags,
        )
    if processo.returncode != 0:
        detalhe = (processo.stderr or processo.stdout).strip()[-1200:]
        raise RuntimeError("Falha ao executar o modelo local. " + detalhe)
    return _extrair_json(processo.stdout)
