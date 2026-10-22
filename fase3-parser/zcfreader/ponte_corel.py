"""Ponte entre a macro do CorelDRAW e a análise.

A macro chama:
    python -m zcfreader.ponte_corel <arquivo.cdr> <saida.txt> <regras|ia>

e lê o resultado em texto simples (Windows-1252, separado por TAB), que o VBA
lê sem bibliotecas extras. Uma linha por registro:

    INFO      camada   duracao_s   custo_usd
    ITEM      n  quantidade  largura_cm  altura_cm  material  acabamento  esquerda  direita  base  topo  situacao  origem_material  origem_quantidade
    PERGUNTA  texto
    ERRO      mensagem

As coordenadas (cm) são as do arquivo, com origem no centro da página; a macro
converte para as do CorelDRAW. O resultado completo também é gravado em JSON ao
lado (<saida>.json), para a correção pelo Corel usar depois.

Modos:
- regras: sem IA e sem custo. Se as regras resolvem, é a resposta delas; se não,
  mostra os produtos prováveis das regras, marcados "a confirmar".
- ia: o mesmo fluxo em camadas do aplicativo (regras, depois a IA configurada).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from time import perf_counter


LADO_MINIMO_SEM_TEXTO_CM = 3.0


def _caixa_do_item(item: dict, candidatos: dict) -> dict | None:
    if item.get("caixa_cm"):
        return item["caixa_cm"]
    caixas = [candidatos[i]["caixa_cm"] for i in item.get("candidatos") or [] if i in candidatos]
    caixas += [
        {chave: valor / 10 for chave, valor in componente["caixa_mm"].items()}
        for componente in item.get("componentes") or [] if componente.get("caixa_mm")
    ]
    if not caixas:
        return None
    return {
        "esquerda": min(c["esquerda"] for c in caixas), "direita": max(c["direita"] for c in caixas),
        "base": min(c["base"] for c in caixas), "topo": max(c["topo"] for c in caixas),
    }


def separar_ocorrencias(resultado: dict, candidatos: dict, auditoria: dict | None = None) -> dict:
    """Ajusta itens cuja peça tem várias ocorrências desenhadas da mesma medida.

    - Artes diferentes (bitmaps diferentes) com quantidade igual ao número de
      ocorrências: um item de 1 unidade por arte, cada um com a sua caixa.
    - Cópias da mesma arte: a caixa passa a ser a de uma ocorrência, para exportar
      uma peça com a quantidade, e não todas juntas.
    - "N de cada" com K peças desenhadas (quantidade N × K): K itens de N unidades,
      seja qual for a arte, porque "de cada" já diz que cada peça é um produto.
    - Sem como saber (arte só em vetor) ou quantidade diferente: marca para conferir.
    """
    from copy import deepcopy
    from .agente import _quantidade_de_cada
    from .experimento_agente import caixas_das_ocorrencias

    # Quantidade por peça das instruções "N DE CADA" ligadas a cada candidata.
    por_ocorrencia = {}
    for regra in (auditoria or {}).get("itens") or []:
        for evidencia in regra.get("evidencias") or []:
            por_peca = _quantidade_de_cada(evidencia.get("texto"))
            if por_peca:
                por_ocorrencia.setdefault(regra["candidato_id"], por_peca)

    itens = []
    for item in resultado.get("itens") or []:
        ids = item.get("candidatos") or []
        candidato = candidatos.get(ids[0]) if len(ids) == 1 else None
        caixas = caixas_das_ocorrencias(candidato) if candidato else []
        if len(caixas) <= 1:
            itens.append(item)
            continue
        artes = candidato.get("artes")
        quantidade = (item.get("quantidade") or {}).get("valor") or 0
        por_peca = por_ocorrencia.get(ids[0])
        if por_peca and por_peca * len(caixas) == quantidade:
            # "N de cada" com K peças desenhadas: K itens de N unidades, cada um com a sua caixa.
            for caixa in caixas:
                novo = deepcopy(item)
                novo["quantidade"] = {**(novo.get("quantidade") or {}), "valor": por_peca}
                novo["caixa_cm"] = caixa
                novo["situacao"] = (novo.get("situacao") or "").replace(" - conferir artes", "")
                itens.append(novo)
            continue
        if artes == "distintas" and quantidade == len(caixas):
            for caixa in caixas:
                novo = deepcopy(item)
                novo["quantidade"] = {**(novo.get("quantidade") or {}), "valor": 1}
                novo["caixa_cm"] = caixa
                itens.append(novo)
            continue
        if artes == "iguais":
            item["caixa_cm"] = caixas[0]
        else:
            situacao = item.get("situacao") or ""
            item["situacao"] = f"{situacao} - conferir artes" if situacao else "conferir artes"
        itens.append(item)
    for indice, item in enumerate(itens, 1):
        item["indice"] = indice
    resultado["itens"] = itens
    return resultado


def _material_do_nome_arquivo(caminho: Path | None, itens: list[dict]) -> None:
    """Preenche material e acabamento vazios pelo nome do arquivo, como faz o leitor estrutural."""
    from .pedido import interpretar_nome_arquivo, _aplicar_nome_arquivo

    if caminho is None or not itens:
        return
    evidencia = interpretar_nome_arquivo(caminho.name)
    # Só material e acabamento: medida e quantidade continuam vindo do desenho.
    _aplicar_nome_arquivo(itens, {"texto": evidencia["texto"], "material": evidencia["material"]})


def _analisar_regras(caminho: Path, fatos: dict) -> dict:
    from .camadas import regras_resolvem, resultado_das_regras

    auditoria = fatos["auditoria_regional"]
    if regras_resolvem(auditoria):
        resultado = resultado_das_regras(auditoria)
        for item in resultado["itens"]:
            item["situacao"] = "regras"
        _material_do_nome_arquivo(caminho, resultado["itens"])
        return {"itens": resultado["itens"], "perguntas_operador": [], "processamento": {"fluxo": "macro_corel", "camada_final": "regras"}}
    itens = []
    for regra in auditoria.get("itens") or []:
        produto = regra.get("papel") in {"produto_confirmado", "produto_plausivel"}
        # Peças que o programa enxerga mas sem texto que as explique. Nas correções pela
        # macro, adicionar peça dá muito mais trabalho que remover; simulação nos 68
        # pedidos revisados: faltando 31 -> 8 linhas, com ~44 a mais para remover.
        sem_texto = (regra.get("papel") == "sem_classificacao"
                     and min(regra["largura_cm"], regra["altura_cm"]) >= LADO_MINIMO_SEM_TEXTO_CM)
        if not (produto or sem_texto):
            continue
        itens.append({
            "indice": len(itens) + 1,
            "quantidade": {"valor": int(regra.get("quantidade_pedido") or regra.get("quantidade_desenhada") or 1)},
            "dimensoes": {"largura_mm": regra["largura_cm"] * 10, "altura_mm": regra["altura_cm"] * 10},
            "material": {"valor": regra.get("material")},
            "acabamento": {"valor": regra.get("acabamento")},
            "candidatos": [regra["candidato_id"]],
            "situacao": "a confirmar" if produto else "sem texto - confirmar",
        })
    # Peça sem texto que está dentro de outra peça da lista é parte dela (ex.: o bitmap
    # dentro do grupo com fundo), não um item a mais.
    candidatos = fatos.get("candidatos") or {}
    listados = {item["candidatos"][0] for item in itens}

    from .experimento_agente import caixas_das_ocorrencias

    def dentro_de_ocorrencia(caixa: dict, pai: dict) -> bool:
        # A caixa de uma peça repetida cobre todas as cópias e o espaço entre elas:
        # só conta como "dentro" o que cabe numa das ocorrências.
        ocorrencias = caixas_das_ocorrencias(pai) or [pai["caixa_cm"]]
        return any(
            o["esquerda"] - 0.3 <= caixa["esquerda"] and caixa["direita"] <= o["direita"] + 0.3
            and o["base"] - 0.3 <= caixa["base"] and caixa["topo"] <= o["topo"] + 0.3
            for o in ocorrencias
        )

    def dentro_de_listado(candidato_id: str) -> bool:
        vistos = set()
        caixa = (candidatos.get(candidato_id) or {}).get("caixa_cm")
        pai = (candidatos.get(candidato_id) or {}).get("pai_id")
        while caixa and pai and pai not in vistos:
            if pai in listados and dentro_de_ocorrencia(caixa, candidatos[pai]):
                return True
            vistos.add(pai)
            pai = (candidatos.get(pai) or {}).get("pai_id")
        return False

    itens = [
        item for item in itens
        if item["situacao"] != "sem texto - confirmar" or not dentro_de_listado(item["candidatos"][0])
    ]
    for indice, item in enumerate(itens, 1):
        item["indice"] = indice
    _material_do_nome_arquivo(caminho, itens)
    return {"itens": itens, "perguntas_operador": [], "processamento": {"fluxo": "macro_corel", "camada_final": "regras (a confirmar)"}}


def _analisar_ia(caminho: Path, fatos: dict) -> dict:
    from .camadas import interpretar_em_camadas
    from .configuracao import carregar_configuracao, obter_chave
    from .pedido import interpretar_pedido

    configuracao = carregar_configuracao()
    return interpretar_em_camadas(
        caminho, obter_chave("openrouter"), interpretar_pedido(caminho), fatos=fatos,
        modelo_rapido=configuracao["modelo_rapido"], modelo_forte=configuracao["modelo_forte"],
        custo_maximo_usd=configuracao["limite_pedido_usd"], url_servidor_local=configuracao["url_servidor_local"],
    )


def aplicar_catalogo(resultado: dict) -> dict:
    """Troca material e acabamento pelos nomes do Portal Flow, guardando o texto lido.

    O material que vem só do padrão da gráfica (o pedido dizia apenas "adesivo")
    fica marcado em ``origem_campos`` para aparecer como "(padrão)" na macro.
    """
    from .catalogo_portal import acabamentos_portal, material_portal

    for item in resultado.get("itens") or []:
        material = (item.get("material") or {}).get("valor")
        acabamento = (item.get("acabamento") or {}).get("valor")
        nome, origem = material_portal(material, acabamento)
        if nome:
            item["material"] = {**(item.get("material") or {}), "valor": nome, "texto_lido": material}
            if origem == "padrao_grafica":
                item["origem_campos"] = {**(item.get("origem_campos") or {}), "material": "padrao_grafica"}
        acabamentos = acabamentos_portal(material, acabamento)
        if acabamentos:
            item["acabamento"] = {**(item.get("acabamento") or {}), "valor": " + ".join(acabamentos),
                                  "texto_lido": acabamento}
    return resultado


def _campo(valor) -> str:
    texto = "" if valor is None else str(valor)
    return " ".join(texto.replace("\t", " ").split())


def _numero(valor) -> str:
    return f"{float(valor):.3f}"


def linhas_de_saida(resultado: dict, candidatos: dict, duracao_s: float) -> list[str]:
    processamento = resultado.get("processamento") or {}
    linhas = ["\t".join(["INFO", _campo(processamento.get("camada_final")), f"{duracao_s:.1f}",
                         f"{float(processamento.get('custo_usd') or 0):.4f}"])]
    for n, item in enumerate(resultado.get("itens") or [], 1):
        dimensoes = item.get("dimensoes") or {}
        caixa = _caixa_do_item(item, candidatos)
        coordenadas = [_numero(caixa[c]) for c in ("esquerda", "direita", "base", "topo")] if caixa else ["", "", "", ""]
        linhas.append("\t".join([
            "ITEM", str(n), _campo((item.get("quantidade") or {}).get("valor")),
            _numero((dimensoes.get("largura_mm") or 0) / 10), _numero((dimensoes.get("altura_mm") or 0) / 10),
            _campo((item.get("material") or {}).get("valor")), _campo((item.get("acabamento") or {}).get("valor")),
            *coordenadas, _campo(item.get("situacao") or ""),
            _campo((item.get("origem_campos") or {}).get("material") or "arquivo"),
            _campo((item.get("origem_campos") or {}).get("quantidade") or "arquivo"),
        ]))
    for pergunta in resultado.get("perguntas_operador") or []:
        linhas.append("\t".join(["PERGUNTA", _campo(pergunta.get("pergunta") if isinstance(pergunta, dict) else pergunta)]))
    return linhas


_ORIGENS_VALIDAS = {"arquivo", "padrao_grafica", "faltou_no_pedido"}


def _numero_ou_none(texto: str) -> float | None:
    try:
        return float(texto.replace(",", "."))
    except (AttributeError, ValueError):
        return None


def resultado_corrigido(original: dict, linhas: list[str]) -> tuple[dict, str]:
    """Monta o resultado correto a partir do arquivo de correção escrito pela macro.

    Linhas (TAB):
        OBS   texto
        ITEM  n_original  quantidade  largura_cm  altura_cm  material  acabamento
              origem_quantidade  origem_material  origem_acabamento  peca  esquerda  direita  base  topo
              motivo  objetos
    ``n_original`` 0 = item novo; ``peca`` "corel" = peça escolhida selecionando no CorelDRAW.
    """
    from copy import deepcopy

    from .origem_campos import definir_origens

    originais = original.get("itens") or []
    itens, observacao = [], ""
    for linha in linhas:
        campos = linha.rstrip("\r\n").split("\t")
        if campos[0] == "OBS" and len(campos) > 1:
            observacao = campos[1].strip()
        if campos[0] != "ITEM" or len(campos) < 17:
            continue
        indice_original = int(campos[1] or 0)
        base = deepcopy(originais[indice_original - 1]) if 0 < indice_original <= len(originais) else {}
        item = base
        quantidade = int(float(campos[2] or 0) or 1)
        largura, altura = _numero_ou_none(campos[3]) or 0.0, _numero_ou_none(campos[4]) or 0.0
        antes_dim = base.get("dimensoes") or {}

        if (base.get("quantidade") or {}).get("valor") != quantidade:
            item["quantidade"] = {"valor": quantidade, "unidade": "unidade", "fonte": "correcao_operador", "confianca": 1.0}
        for campo, valor in (("material", campos[5]), ("acabamento", campos[6])):
            valor = valor.strip() or None
            if (base.get(campo) or {}).get("valor") != valor:
                item[campo] = {"valor": valor, "fonte": "correcao_operador", "confianca": 1.0}

        if campos[10] == "corel" or not antes_dim:
            item["dimensoes"] = {
                "largura_mm": round(largura * 10, 3), "altura_mm": round(altura * 10, 3),
                "tipo": "peca_indicada_pelo_operador", "fonte": "correcao_operador", "confianca": 1.0,
            }
        caixa = [_numero_ou_none(c) for c in campos[11:15]]
        if all(v is not None for v in caixa):
            item["caixa_cm"] = dict(zip(("esquerda", "direita", "base", "topo"), caixa))
        if campos[10] == "corel":
            item["peca_correta"] = {
                "origem": "selecao_corel", "largura_cm": largura, "altura_cm": altura,
                "objetos_corel": [o for o in campos[16].split(";") if o],
            }
            if base:
                item["peca_correta"]["antes"] = {
                    "ids": list(base.get("candidatos") or []),
                    "largura_cm": round((antes_dim.get("largura_mm") or 0) / 10, 3),
                    "altura_cm": round((antes_dim.get("altura_mm") or 0) / 10, 3),
                }
        if campos[15].strip():
            item["observacao_operador"] = campos[15].strip()
        origens = {
            campo: codigo for campo, codigo in zip(("quantidade", "material", "acabamento"), campos[7:10])
            if codigo in _ORIGENS_VALIDAS
        }
        itens.append(definir_origens(item, origens))
    correto = {k: v for k, v in original.items() if k != "itens"}
    correto["itens"] = itens
    return correto, observacao


def salvar_correcao(caminho: Path, arquivo_correcao: Path) -> Path:
    from .configuracao import carregar_configuracao
    from .relatorios import classificar_diferencas, gerar_pacote_diagnostico

    linhas = arquivo_correcao.read_text(encoding="cp1252").splitlines()
    original_json = next((l.split("\t", 1)[1] for l in linhas if l.startswith("ORIGINAL\t")), None)
    if not original_json or not Path(original_json).exists():
        raise FileNotFoundError("Resultado da análise não encontrado; analise o arquivo de novo antes de salvar.")
    dados = json.loads(Path(original_json).read_text(encoding="utf-8"))
    if Path(dados["arquivo"]).resolve() != Path(caminho).resolve():
        raise ValueError("A análise guardada é de outro arquivo; analise este arquivo de novo antes de salvar.")
    original = dados["resultado"]
    correto, observacao = resultado_corrigido(original, linhas)
    situacao = "corrigido" if classificar_diferencas(original, correto) else "confirmado"
    configuracao = carregar_configuracao()
    return gerar_pacote_diagnostico(
        Path(caminho), original, correto, situacao=situacao, observacao_operador=observacao,
        incluir_cdr=bool(configuracao.get("incluir_cdr_diagnostico", True)),
    )


def main(argumentos: list[str]) -> int:
    caminho, saida, modo = Path(argumentos[0]), Path(argumentos[1]), (argumentos[2] if len(argumentos) > 2 else "regras")
    if modo == "salvar":
        # Aqui "saida" é o arquivo de correção escrito pela macro; a resposta vai para <correcao>.ok
        try:
            linhas = ["\t".join(["OK", str(salvar_correcao(caminho, saida))])]
        except Exception as erro:
            linhas = ["\t".join(["ERRO", _campo(f"{type(erro).__name__}: {erro}")])]
        Path(str(saida) + ".ok").write_text("\r\n".join(linhas) + "\r\n", encoding="cp1252", errors="replace", newline="")
        return 0
    inicio = perf_counter()
    try:
        # O CorelDRAW aberto nunca é usado pela análise: o desenho vem do próprio arquivo.
        import zcfreader.visao_api as visao_api
        visao_api.renderizar_com_corel = lambda *a, **k: None
        from .agente import extrair_fatos

        fatos = extrair_fatos(caminho)
        resultado = _analisar_ia(caminho, fatos) if modo == "ia" else _analisar_regras(caminho, fatos)
        separar_ocorrencias(resultado, fatos.get("candidatos") or {}, fatos.get("auditoria_regional"))
        aplicar_catalogo(resultado)
        linhas = linhas_de_saida(resultado, fatos.get("candidatos") or {}, perf_counter() - inicio)
        Path(str(saida) + ".json").write_text(
            json.dumps({"arquivo": str(caminho), "modo": modo, "resultado": resultado}, ensure_ascii=False,
                       indent=2, default=str),
            encoding="utf-8",
        )
    except Exception as erro:  # a macro mostra a mensagem ao operador
        linhas = ["\t".join(["ERRO", _campo(f"{type(erro).__name__}: {erro}")])]
    saida.write_text("\r\n".join(linhas) + "\r\n", encoding="cp1252", errors="replace", newline="")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
