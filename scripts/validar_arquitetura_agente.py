from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import tempfile
import unicodedata
from zipfile import ZipFile

from zcfreader.experimento_agente import (
    avaliar_cobertura_geometrica,
    associar_materiais_acabamentos,
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


def texto_canonico(valor) -> str:
    texto = "".join(
        caractere for caractere in unicodedata.normalize("NFKD", str(valor or "").casefold())
        if not unicodedata.combining(caractere)
    )
    return " ".join(texto.split())


def material_canonico(valor) -> str:
    texto = texto_canonico(valor)
    if texto in {"banner", "lona"}:
        return "lona"
    return texto


def materiais_compativeis(previsto, esperado) -> bool:
    previsto_canonico = material_canonico(previsto)
    esperado_canonico = material_canonico(esperado)
    if previsto_canonico == esperado_canonico:
        return True
    return esperado_canonico == "adesivo" and previsto_canonico.startswith("adesivo ")


def acabamento_canonico(valor) -> str:
    texto = texto_canonico(valor)
    especiais = []
    if "frente e verso" in texto:
        especiais.append("frente e verso")
    if "ilho" in texto:
        especiais.append("ilhos")
    if "verniz" in texto:
        especiais.append("verniz")
    return " + ".join(especiais) if especiais else texto


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
            catalogo["materiais_regionais"] = associar_materiais_acabamentos(catalogo)
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
        materiais_por_candidato = {
            item["candidato_id"]: item for item in catalogo.get("materiais_regionais", [])
        }
        materiais_avaliados = materiais_corretos = 0
        acabamentos_avaliados = acabamentos_corretos = 0
        materiais_esperados = acabamentos_esperados = 0
        ids_com_material_esperado = set()
        ids_com_acabamento_esperado = set()
        for detalhe, item_esperado in zip(cobertura["detalhes"], esperado.get("itens", [])):
            candidato_id = detalhe.get("candidato")
            previsto = materiais_por_candidato.get(candidato_id)
            material_esperado = (item_esperado.get("material") or {}).get("valor")
            acabamento_esperado = (item_esperado.get("acabamento") or {}).get("valor")
            if material_esperado:
                materiais_esperados += 1
                if candidato_id:
                    ids_com_material_esperado.add(candidato_id)
                if previsto and previsto.get("material"):
                    materiais_avaliados += 1
                    materiais_corretos += materiais_compativeis(previsto.get("material"), material_esperado)
            if acabamento_esperado:
                acabamentos_esperados += 1
                if candidato_id:
                    ids_com_acabamento_esperado.add(candidato_id)
                if previsto and previsto.get("acabamento"):
                    acabamentos_avaliados += 1
                    acabamentos_corretos += acabamento_canonico(previsto.get("acabamento")) == acabamento_canonico(acabamento_esperado)
        ids_materiais_emitidos = {
            candidato_id for candidato_id, previsto in materiais_por_candidato.items()
            if previsto.get("material")
        }
        ids_acabamentos_emitidos = {
            candidato_id for candidato_id, previsto in materiais_por_candidato.items()
            if previsto.get("acabamento")
        }
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
            "associacoes_com_area": sum(item.get("area_m2") is not None for item in associacoes),
            "associacoes_area_confirmada": sum(item.get("area_confere_quantidade") is True for item in associacoes),
            "associacoes_requer_confirmacao": sum(item.get("requer_confirmacao_semantica") is True for item in associacoes),
            "materiais_emitidos": len(materiais_por_candidato),
            "materiais_esperados": materiais_esperados,
            "materiais_avaliados": materiais_avaliados,
            "materiais_corretos": materiais_corretos,
            "materiais_incorretos": materiais_avaliados - materiais_corretos,
            "materiais_abstencoes": materiais_esperados - materiais_avaliados,
            "materiais_emissoes_sem_gabarito": len(ids_materiais_emitidos - ids_com_material_esperado),
            "acabamentos_esperados": acabamentos_esperados,
            "acabamentos_avaliados": acabamentos_avaliados,
            "acabamentos_corretos": acabamentos_corretos,
            "acabamentos_incorretos": acabamentos_avaliados - acabamentos_corretos,
            "acabamentos_abstencoes": acabamentos_esperados - acabamentos_avaliados,
            "acabamentos_emissoes_sem_gabarito": len(ids_acabamentos_emitidos - ids_com_acabamento_esperado),
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
    "associacoes_com_area": sum(item["associacoes_com_area"] for item in resumo),
    "associacoes_area_confirmada": sum(item["associacoes_area_confirmada"] for item in resumo),
    "associacoes_requer_confirmacao": sum(item["associacoes_requer_confirmacao"] for item in resumo),
    "materiais_emitidos": sum(item["materiais_emitidos"] for item in resumo),
    "materiais_esperados": sum(item["materiais_esperados"] for item in resumo),
    "materiais_avaliados": sum(item["materiais_avaliados"] for item in resumo),
    "materiais_corretos": sum(item["materiais_corretos"] for item in resumo),
    "materiais_incorretos": sum(item["materiais_incorretos"] for item in resumo),
    "materiais_abstencoes": sum(item["materiais_abstencoes"] for item in resumo),
    "materiais_emissoes_sem_gabarito": sum(item["materiais_emissoes_sem_gabarito"] for item in resumo),
    "acabamentos_esperados": sum(item["acabamentos_esperados"] for item in resumo),
    "acabamentos_avaliados": sum(item["acabamentos_avaliados"] for item in resumo),
    "acabamentos_corretos": sum(item["acabamentos_corretos"] for item in resumo),
    "acabamentos_incorretos": sum(item["acabamentos_incorretos"] for item in resumo),
    "acabamentos_abstencoes": sum(item["acabamentos_abstencoes"] for item in resumo),
    "acabamentos_emissoes_sem_gabarito": sum(item["acabamentos_emissoes_sem_gabarito"] for item in resumo),
}
(args.pasta_saida / "resumo.json").write_text(json.dumps(resultado, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(json.dumps({k: v for k, v in resultado.items() if k != "casos"}, ensure_ascii=False, indent=2))
