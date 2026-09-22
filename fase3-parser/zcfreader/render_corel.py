"""Renderização opcional em alta resolução usando uma instalação local do CorelDRAW."""
from __future__ import annotations

import csv
import io
import os
from pathlib import Path
import subprocess
import tempfile
import threading

# O CorelDRAW pode parar em um diálogo invisível (licença, fonte ausente,
# atualização) e a chamada COM nunca retorna. Sem prazo, a análise trava.
TEMPO_LIMITE_PADRAO_S = float(os.environ.get("CDR_PEDIDO_TEMPO_LIMITE_COREL", "90"))

_cache: dict[tuple, bytes | None] = {}
_cache_lock = threading.Lock()


def _pids_corel() -> set[int]:
    try:
        saida = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq CorelDRW.exe", "/FO", "CSV", "/NH"],
            capture_output=True, text=True, timeout=15,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return set()
    pids = set()
    for linha in csv.reader(io.StringIO(saida)):
        if len(linha) >= 2 and linha[1].isdigit():
            pids.add(int(linha[1]))
    return pids


def _encerrar(pids: set[int]) -> None:
    for pid in pids:
        try:
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/T", "/F"], capture_output=True, timeout=15,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
        except (OSError, subprocess.SubprocessError):
            pass


def _renderizar(caminho: Path, largura_px: int) -> bytes | None:
    try:
        import pythoncom
        import win32com.client
    except ImportError:
        return None

    pythoncom.CoInitialize()
    app = documento = None
    try:
        app = win32com.client.DispatchEx("CorelDRAW.Application")
        app.Visible = False
        documento = app.OpenDocument(str(Path(caminho).resolve()))
        formas = documento.ActivePage.Shapes.All()
        if formas.Count:
            formas.CreateSelection()
            intervalo = 2  # cdrSelection
        else:
            intervalo = 1  # cdrCurrentPage
        opcoes = app.CreateStructExportOptions()
        opcoes.ImageType = 4  # cdrRGBColorImage
        opcoes.SizeX = int(largura_px)
        opcoes.SizeY = int(largura_px)
        opcoes.MaintainAspect = True
        opcoes.ResolutionX = 150
        opcoes.ResolutionY = 150
        opcoes.AntiAliasingType = 1  # cdrNormalAntiAliasing
        opcoes.Overwrite = True
        paleta = app.CreateStructPaletteOptions()
        with tempfile.TemporaryDirectory(prefix="cdr-render-") as pasta:
            saida = Path(pasta) / "pagina.png"
            documento.Export(str(saida), 802, intervalo, opcoes, paleta)  # cdrPNG
            if saida.is_file() and saida.stat().st_size:
                return saida.read_bytes()
    except Exception:
        return None
    finally:
        if documento is not None:
            try:
                documento.Close()
            except Exception:
                pass
        if app is not None:
            try:
                app.Quit()
            except Exception:
                pass
        pythoncom.CoUninitialize()
    return None


def renderizar_com_corel(
    caminho: Path, largura_px: int = 2400, tempo_limite_s: float | None = None,
) -> bytes | None:
    """Exporta os objetos da página sem alterar o CDR.

    Retorna None se o CorelDRAW não estiver disponível ou não responder no prazo;
    nesse caso encerra somente as instâncias que surgiram durante esta chamada.
    O resultado é memorizado por arquivo para que uma análise não abra o
    CorelDRAW várias vezes.
    """
    caminho = Path(caminho)
    try:
        estado = caminho.stat()
        chave = (str(caminho.resolve()), estado.st_size, estado.st_mtime_ns, largura_px)
    except OSError:
        return None
    with _cache_lock:
        if chave in _cache:
            return _cache[chave]

    prazo = TEMPO_LIMITE_PADRAO_S if tempo_limite_s is None else tempo_limite_s
    antes = _pids_corel()
    resultado: list[bytes | None] = [None]
    tarefa = threading.Thread(
        target=lambda: resultado.__setitem__(0, _renderizar(caminho, largura_px)), daemon=True,
    )
    tarefa.start()
    tarefa.join(prazo)
    if tarefa.is_alive():
        _encerrar(_pids_corel() - antes)
        tarefa.join(10)
        render = None
    else:
        render = resultado[0]
    with _cache_lock:
        _cache[chave] = render
        while len(_cache) > 4:
            del _cache[next(iter(_cache))]
    return render
