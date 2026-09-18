"""OCR local em CPU com caixas espaciais para textos convertidos em curvas."""
from __future__ import annotations

from functools import lru_cache


@lru_cache(maxsize=1)
def _motor():
    from rapidocr_onnxruntime import RapidOCR
    return RapidOCR()


def executar_ocr(imagem: bytes, confianca_minima: float = 0.55) -> list[dict]:
    """Retorna texto, confiança e polígono; falha opcionalmente sem derrubar a análise."""
    try:
        import cv2
        import numpy as np
        matriz = cv2.imdecode(np.frombuffer(imagem, dtype=np.uint8), cv2.IMREAD_COLOR)
        resultado, _ = _motor()(matriz)
    except Exception:
        return []
    linhas = []
    for poligono, texto, confianca in resultado or []:
        if float(confianca) < confianca_minima or not str(texto).strip():
            continue
        linhas.append({
            "texto": str(texto).strip(), "confianca": round(float(confianca), 3),
            "poligono_px": [[round(float(x), 1), round(float(y), 1)] for x, y in poligono],
        })
    return linhas
