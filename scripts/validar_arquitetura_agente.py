from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import tempfile
from zipfile import ZipFile

from zcfreader.experimento_agente import (
    avaliar_cobertura_geometrica,
    extrair_associacoes_regionais,
    extrair_candidatos_agente,
    gerar_atlas_candidatos,
    gravar_manifesto,
)


def casos_revisados(pasta: Path):
    revisoes = {}
    for zip_path in sorted(pasta.glob("*.zip")):
        with ZipFile(zip_path) as pacote:
            if "diagnostico.json" not in pacote.namelist() or "resultado-correto.json" not in pacote.namelist():
                continue
            diagnostico = json.loads(pacote.read("diagnostico.json"))
            cdr = next((n for n in pacote.namelist() if n.startswith("arquivo-original/") and n.casefold().endswith(".cdr")), None)
            if cdr:
                revisoes[diagnostico["arquivo"]["sha256"]] = (zip_path, cdr, diagnostico)
    return list(revisoes.values())


parser = argparse.ArgumentParser(description="Valida candidatos identificados antes do agente visual")
parser.add_argument("pasta_relatorios", type=Path)
parser.add_argument("pasta_saida", type=Path)
parser.add_argument("--sem-imagens", action="store_true", help="Mede cobertura sem abrir o Corel")
parser.add_argument("--gabaritos", type=Path, help="JSON opcional com correções mais recentes por nome de arquivo")
parser.add_argument("--com-ocr-regional", action="store_true", help="Executa OCR limpo e associa instruções por região")
args = parser.parse_args()
args.pasta_saida.mkdir(parents=True, exist_ok=True)
gabaritos = json.loads(args.gabaritos.read_text(encoding="utf-8")) if args.gabaritos else {}

resumo = []
for indice, (zip_path, membro_cdr, diagnostico) in enumerate(casos_revisados(args.pasta_relatorios), 1):
    with ZipFile(zip_path) as pacote, tempfile.TemporaryDirectory(prefix="cdr-agente-") as temporaria:
        caminho = Path(temporaria) / Path(membro_cdr).name
        caminho.write_bytes(pacote.read(membro_cdr))
        esperado = gabaritos.get(diagnostico["arquivo"]["nome"]) or json.loads(pacote.read("resultado-correto.json"))
        catalogo = extrair_candidatos_agente(caminho)
        hipoteses_mediveis = catalogo["candidatos"] + catalogo.get("blocos_producao", [])
        cobertura = avaliar_cobertura_geometrica(hipoteses_mediveis, esperado)
        if args.com_ocr_regional:
            catalogo["ocr_regional"] = extrair_associacoes_regionais(caminho, catalogo)
        associacoes = catalogo.get("ocr_regional", {}).get("associacoes", [])
        esperado_por_candidato = Counter(
            (detalhe["candidato"], int(item["quantidade"]["valor"]))
            for detalhe, item in zip(cobertura["detalhes"], esperado.get("itens", []))
            if detalhe["encontrado"]
        )
        previsto_por_candidato = Counter(
            (item["candidato_id"], int(item["quantidade"])) for item in associacoes
        )
        associacoes_corretas = sum((esperado_por_candidato & previsto_por_candidato).values())
        pasta_caso = args.pasta_saida / f"{indice:02d}-{diagnostico['arquivo']['sha256'][:8]}"
        pasta_caso.mkdir(parents=True, exist_ok=True)
        gravar_manifesto(catalogo, esperado, cobertura, pasta_caso / "manifesto.json")
        imagens = [] if args.sem_imagens else gerar_atlas_candidatos(caminho, catalogo, pasta_caso)
        resumo.append({
            "arquivo": diagnostico["arquivo"]["nome"],
            "candidatos": len(catalogo["candidatos"]),
            "blocos_producao": len(catalogo.get("blocos_producao", [])),
            "associacoes_regionais": len(catalogo.get("ocr_regional", {}).get("associacoes", [])),
            "associacoes_regionais_corretas": associacoes_corretas,
            "associacoes_regionais_falsas": sum(previsto_por_candidato.values()) - associacoes_corretas,
            "cobertura_geometrica": cobertura,
            "imagens": [str(item) for item in imagens],
        })
        print(f"[{indice}] {diagnostico['arquivo']['nome']}: {cobertura['itens_encontrados']}/{cobertura['itens_esperados']}", flush=True)

total_itens = sum(item["cobertura_geometrica"]["itens_esperados"] for item in resumo)
encontrados = sum(item["cobertura_geometrica"]["itens_encontrados"] for item in resumo)
resultado = {
    "casos": resumo, "total_casos": len(resumo), "itens_esperados": total_itens,
    "itens_com_candidato": encontrados,
    "cobertura_geometrica": encontrados / total_itens if total_itens else 1.0,
    "associacoes_regionais": sum(item["associacoes_regionais"] for item in resumo),
    "associacoes_regionais_corretas": sum(item["associacoes_regionais_corretas"] for item in resumo),
    "associacoes_regionais_falsas": sum(item["associacoes_regionais_falsas"] for item in resumo),
}
(args.pasta_saida / "resumo.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in resultado.items() if k != "casos"}, ensure_ascii=False, indent=2))
