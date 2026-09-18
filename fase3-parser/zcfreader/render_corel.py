"""Renderização opcional em alta resolução usando uma instalação local do CorelDRAW."""
from __future__ import annotations

from pathlib import Path
import tempfile


def renderizar_com_corel(caminho: Path, largura_px: int = 2400) -> bytes | None:
    """Exporta os objetos da página sem alterar o CDR; retorna None se Corel não estiver disponível."""
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
