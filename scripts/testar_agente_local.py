"""Executa o Qwen local sobre pranchas de candidatos, sem alterar o aplicativo."""
from __future__ import annotations

import argparse
from collections import Counter
import ctypes
from ctypes import wintypes
import json
from pathlib import Path
import subprocess
import tempfile
import threading
import time

from zcfreader.modelos_locais import caminhos_instalacao, modelo_instalado


def extrair_json(texto: str) -> dict:
    decodificador = json.JSONDecoder()
    respostas = []
    for posicao, caractere in enumerate(texto):
        if caractere != "{":
            continue
        try:
            valor, _ = decodificador.raw_decode(texto[posicao:])
        except json.JSONDecodeError:
            continue
        if isinstance(valor, dict) and isinstance(valor.get("produtos"), list):
            respostas.append(valor)
    if not respostas:
        raise RuntimeError("O modelo não devolveu o envelope JSON do experimento.")
    return respostas[-1]


def schema(ids: list[str]) -> dict:
    return {
        "type": "object", "additionalProperties": False,
        "properties": {
            "produtos": {
                "type": "array", "maxItems": 20,
                "items": {
                    "type": "object", "additionalProperties": False,
                    "properties": {
                        "candidato_id": {"type": "string", "enum": ids},
                        "quantidade": {"type": "integer", "minimum": 1, "maximum": 10000},
                        "material": {"type": "string", "maxLength": 80},
                        "acabamento": {"type": "string", "maxLength": 80},
                        "confianca": {"type": "integer", "minimum": 0, "maximum": 100},
                    },
                    "required": ["candidato_id", "quantidade", "material", "acabamento", "confianca"],
                },
            },
            "precisa_detalhes": {
                "type": "array", "maxItems": 10, "uniqueItems": True,
                "items": {"type": "string", "enum": ids},
            },
            "itens_sem_candidato": {
                "type": "array", "maxItems": 10,
                "items": {"type": "string", "maxLength": 120},
            },
            "observacoes": {
                "type": "array", "maxItems": 3,
                "items": {"type": "string", "maxLength": 120},
            },
        },
        "required": ["produtos", "precisa_detalhes", "itens_sem_candidato", "observacoes"],
    }


def prompt(manifesto: dict) -> str:
    catalogo = manifesto["catalogo"]
    principais = [item for item in catalogo["candidatos"] if item["visivel_inicialmente"]]
    lista = [
        {
            "id": item["id"], "quantidade_geometrica": item["quantidade_geometrica"],
            "largura_cm": round(item["largura_cm"], 2), "altura_cm": round(item["altura_cm"], 2),
            "tem_detalhes": bool(item["filhos_ids"]),
        }
        for item in principais
    ]
    return (
        "Você é um agente de pré-produção de uma gráfica. A imagem mostra a montagem inteira recebida do cliente. "
        "As caixas vermelhas e a legenda identificam hipóteses geométricas medidas diretamente no CDR. "
        "Escolha apenas hipóteses que sejam produtos finais a imprimir, não logotipos, fotografias, textos, fundos ou partes internas. "
        "A quantidade_geometrica conta ocorrências desenhadas e NÃO é necessariamente a quantidade pedida. "
        "Leia as instruções visíveis, inclusive texto convertido em curvas. Um mesmo candidato_id pode aparecer em duas linhas se houver "
        "dois pedidos visíveis do mesmo tamanho com quantidades diferentes. Nunca invente uma medida: o programa usará a medida exata do candidato. "
        "Se um produto real estiver dentro de uma composição mas não tiver candidato visível, coloque o candidato externo em precisa_detalhes. "
        "Se a quantidade não estiver escrita ou inequívoca, use a contagem visual e reduza a confiança. Material pode vir do nome do arquivo. "
        f"Nome do arquivo: {catalogo['arquivo']}. Candidatos desta rodada: {json.dumps(lista, ensure_ascii=False)}. "
        f"Textos nativos extraídos: {json.dumps(catalogo.get('evidencias_textuais', [])[:30], ensure_ascii=False)}. "
        "Responda somente com o JSON solicitado, de forma concisa."
    )


def memoria_processo_bytes(pid: int) -> int:
    if not hasattr(ctypes, "windll"):
        return 0
    class Contadores(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD),
            ("PeakWorkingSetSize", ctypes.c_size_t), ("WorkingSetSize", ctypes.c_size_t),
            ("QuotaPeakPagedPoolUsage", ctypes.c_size_t), ("QuotaPagedPoolUsage", ctypes.c_size_t),
            ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t), ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
            ("PagefileUsage", ctypes.c_size_t), ("PeakPagefileUsage", ctypes.c_size_t),
        ]
    handle = ctypes.windll.kernel32.OpenProcess(0x0410, False, pid)
    if not handle:
        return 0
    try:
        dados = Contadores()
        dados.cb = ctypes.sizeof(dados)
        if ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(dados), dados.cb):
            return int(dados.WorkingSetSize)
        return 0
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def executar(caso: Path) -> dict:
    manifesto = json.loads((caso / "manifesto.json").read_text(encoding="utf-8"))
    ids = [item["id"] for item in manifesto["catalogo"]["candidatos"] if item["visivel_inicialmente"]]
    caminhos = caminhos_instalacao()
    with tempfile.TemporaryDirectory(prefix="cdr-agente-local-") as temporaria:
        pasta = Path(temporaria)
        prompt_path = pasta / "prompt.txt"
        schema_path = pasta / "schema.json"
        prompt_path.write_text(prompt(manifesto), encoding="utf-8")
        schema_path.write_text(json.dumps(schema(ids), ensure_ascii=False), encoding="utf-8")
        comando = [
            str(caminhos["executavel"]), "-m", str(caminhos["modelo"]),
            "--mmproj", str(caminhos["mmproj"]), "--image", str(caso / "entrada-agente.png"),
            "--no-mmproj-offload", "--device", "none", "--ctx-size", "6144",
            "--image-min-tokens", "1024", "--image-max-tokens", "1536",
            "--temp", "0", "--seed", "1", "--repeat-penalty", "1.12",
            "--repeat-last-n", "128", "--predict", "850",
            "--json-schema-file", str(schema_path), "--file", str(prompt_path),
        ]
        inicio = time.perf_counter()
        processo = subprocess.Popen(
            comando, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            encoding="utf-8", errors="replace", creationflags=subprocess.CREATE_NO_WINDOW,
        )
        pico = 0
        while processo.poll() is None:
            pico = max(pico, memoria_processo_bytes(processo.pid))
            time.sleep(0.2)
        stdout, stderr = processo.communicate()
        duracao = time.perf_counter() - inicio
    if processo.returncode:
        raise RuntimeError((stderr or stdout)[-2000:])
    resposta = extrair_json(stdout)
    esperado = Counter(
        (detalhe["candidato"], int(item["quantidade"]["valor"]))
        for detalhe, item in zip(manifesto["cobertura_geometrica"]["detalhes"], manifesto["esperado"]["itens"])
        if detalhe["encontrado"] and detalhe["candidato"] in ids
    )
    obtido = Counter((item["candidato_id"], int(item["quantidade"])) for item in resposta["produtos"])
    acertos = sum((esperado & obtido).values())
    return {
        "arquivo": manifesto["catalogo"]["arquivo"], "duracao_segundos": round(duracao, 2),
        "pico_memoria_processo_mb": round(pico / 1024 / 1024, 1),
        "candidatos_totais": len(manifesto["catalogo"]["candidatos"]),
        "candidatos_expostos": len(ids), "resposta": resposta,
        "linhas_esperadas_com_candidato_exposto": sum(esperado.values()),
        "linhas_exatas": acertos, "selecao_exata": esperado == obtido,
        "esperado": [{"candidato_id": chave[0], "quantidade": chave[1], "vezes": vezes} for chave, vezes in esperado.items()],
    }


parser = argparse.ArgumentParser(description="Testa a seleção visual do agente no modelo local")
parser.add_argument("pasta_validacao", type=Path)
parser.add_argument("casos", nargs="+", help="Prefixos das pastas de caso, por exemplo 03 06")
parser.add_argument("--saida", type=Path)
args = parser.parse_args()
if not modelo_instalado():
    raise SystemExit("Modelo local não está instalado.")

resultados = []
for prefixo in args.casos:
    encontrados = list(args.pasta_validacao.glob(f"{prefixo}-*"))
    if len(encontrados) != 1:
        raise SystemExit(f"Caso {prefixo!r} não é único: {encontrados}")
    print(f"Testando {encontrados[0].name}...", flush=True)
    resultado = executar(encontrados[0])
    resultados.append(resultado)
    print(json.dumps({k: v for k, v in resultado.items() if k != "resposta"}, ensure_ascii=False), flush=True)

resumo = {
    "casos": resultados,
    "duracao_total_segundos": round(sum(item["duracao_segundos"] for item in resultados), 2),
    "pico_memoria_mb": max((item["pico_memoria_processo_mb"] for item in resultados), default=0),
    "linhas_exatas": sum(item["linhas_exatas"] for item in resultados),
    "linhas_avaliadas": sum(item["linhas_esperadas_com_candidato_exposto"] for item in resultados),
}
destino = args.saida or (args.pasta_validacao / "resultado-modelo-local.json")
destino.write_text(json.dumps(resumo, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Resultado gravado em {destino}")
