"""Gera results/relatorio.md: matriz critério × modo, revisão manual, matriz por pergunta e transições.

Entradas (em results/):
  respostas.json       respostas dos 4 modos com a avaliação automática (gerado pelo notebook)
  metricas.json        métricas automáticas por modo
  revisao_manual.json  rótulo manual de cada resposta (opcional; só vale para as respostas revisadas)
  interpretacao.md     texto de análise escrito à mão (opcional)
"""

import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from .avaliacao import e_recusa
from .busca import buscar
from .dataset import K_TRECHOS, carregar_perguntas

PASTA_RESULTS = Path(__file__).resolve().parent.parent / "results"

MODOS = {
    "base_sem_contexto": "A. Base sem contexto",
    "base_com_contexto": "B. Base com contexto",
    "lora_sem_contexto": "C. LoRA sem contexto",
    "lora_com_contexto": "D. LoRA com contexto",
}
LETRA = {m: MODOS[m][0] for m in MODOS}

ROTULOS = {
    "correta": "correta",
    "correta_equivalente": "correta com outras palavras",
    "parcial": "conclusão certa sem a regra",
    "vaga": "vaga (sem fato concreto)",
    "inventou": "inventou informação",
    "contexto_mal_usado": "usou mal o contexto",
    "recusa_indevida": "recusa indevida",
    "recusa_correta": "recusa correta",
}
UTIL = {"correta", "correta_equivalente", "recusa_correta"}

SIGLA_AUTO = {"correta": "✅ correta", "incompleta": "🟡 incompleta", "incorreta": "❌ incorreta",
              "recusa_indevida": "⛔ recusa indevida", "recusa_correta": "✅ recusa", "alucinacao": "❌ alucinação"}

_ID_FONTE = re.compile(r"\b[A-Z]{2,4}-(?:\d{2}|XX)\b")


def _pct(n: int, total: int) -> str:
    return f"{n}/{total} ({100 * n / total:.0f}%)" if total else "—"


def _carregar_revisao(pasta: Path, respostas: dict) -> dict | None:
    """Só usa a revisão manual se ela foi feita sobre exatamente estas respostas."""
    caminho = pasta / "revisao_manual.json"
    if not caminho.exists():
        return None
    revisao = json.loads(caminho.read_text(encoding="utf-8"))
    for modo, itens in respostas.items():
        for item in itens:
            rev = revisao.get(modo, {}).get(item["id"])
            if not rev or rev["sha1_resposta"] != hashlib.sha1(item["resposta"].encode("utf-8")).hexdigest():
                return None
    return revisao


def _citacao(item: dict) -> str:
    """certa | errada | ausente | espuria (fonte anexada a uma recusa)"""
    ids = _ID_FONTE.findall(item["resposta"])
    if e_recusa(item["resposta"]):
        return "espuria" if ids else "recusa_sem_fonte"
    if not ids:
        return "ausente"
    return "certa" if item["fonte"] in ids else "errada"


def matriz_criterios(respostas: dict, revisao: dict | None) -> str:
    casos = {c["id"]: c for c in carregar_perguntas() if c["split"] == "teste"}
    linhas = {}

    def linha(chave, criterio, nome, valores):
        linhas.setdefault(criterio, []).append((nome, valores))

    for modo, itens in respostas.items():
        na_base = [i for i in itens if i["fonte"]]
        fora = [i for i in itens if not i["fonte"]]
        cat = Counter(i["avaliacao"]["categoria"] for i in itens)
        cit = Counter(_citacao(i) for i in itens)
        respondidas_base = [i for i in na_base if not e_recusa(i["resposta"])]
        recusas = [i for i in itens if e_recusa(i["resposta"])]
        fatos_ok = sum(i["avaliacao"]["fatos_ok"] for i in na_base)
        fatos_tot = sum(len(casos[i["id"]]["fatos"]) for i in na_base)
        palavras = sum(len(i["resposta"].split()) for i in itens) / len(itens)
        rot = Counter(revisao[modo][i["id"]]["rotulo"] for i in itens) if revisao else None
        rot_base = Counter(revisao[modo][i["id"]]["rotulo"] for i in na_base) if revisao else None

        v = {}
        v["fonte_certa"] = _pct(sum(_citacao(i) == "certa" for i in na_base), len(na_base))
        v["fonte_errada"] = _pct(sum(_citacao(i) == "errada" for i in na_base), len(na_base))
        v["fonte_ausente"] = _pct(sum(_citacao(i) == "ausente" for i in respondidas_base), len(respondidas_base))
        v["fonte_espuria"] = _pct(cit["espuria"], len(recusas))
        v["aluc_auto"] = _pct(cat["alucinacao"] + cat["incorreta"], len(itens))
        v["aluc_fora"] = _pct(cat["alucinacao"], len(fora))
        v["acerto_auto"] = _pct(cat["correta"], len(na_base))
        v["fatos"] = _pct(fatos_ok, fatos_tot)
        v["recusa_ok"] = _pct(cat["recusa_correta"], len(fora))
        v["recusa_indevida"] = _pct(cat["recusa_indevida"], len(na_base))
        v["acerto_geral"] = _pct(cat["correta"] + cat["recusa_correta"], len(itens))
        v["palavras"] = f"{palavras:.0f}"
        if revisao:
            v["inventou"] = _pct(rot["inventou"], len(itens))
            v["mal_usado"] = _pct(rot["contexto_mal_usado"], len(itens))
            v["acerto_manual"] = _pct(rot_base["correta"] + rot_base["correta_equivalente"], len(na_base))
            v["vaga"] = _pct(rot["vaga"] + rot["parcial"], len(itens))
            v["util"] = _pct(sum(rot[r] for r in UTIL), len(itens))
        linhas[modo] = v

    estrutura = [
        ("1. Respostas baseadas na fonte", [
            ("fonte_certa", "Cita a fonte certa (perguntas na base)"),
            ("fonte_errada", "Cita uma fonte errada"),
            ("fonte_ausente", "Responde sem citar fonte (das que responderam)"),
            ("fonte_espuria", "Recusa com fonte espúria anexada"),
        ]),
        ("2. Redução de alucinação", [
            ("aluc_auto", "Taxa de alucinação (automática)"),
            ("inventou", "Inventou informação que não existe na base (manual)"),
            ("mal_usado", "Usou mal o contexto: trecho da base que não responde (manual)"),
            ("aluc_fora", "Respondeu pergunta fora da base (automática)"),
        ]),
        ("3. Relevância e precisão", [
            ("acerto_auto", "Acerto nas perguntas da base (automático)"),
            ("acerto_manual", "Acerto nas perguntas da base (manual)"),
            ("fatos", "Fatos do gabarito cobertos"),
            ("vaga", "Respostas vagas ou sem a regra (manual)"),
        ]),
        ("4. Uso correto do contexto", [
            ("recusa_ok", "Recusa correta (perguntas fora da base)"),
            ("recusa_indevida", "Recusa indevida (perguntas na base)"),
            ("acerto_geral", "Acerto geral (automático)"),
            ("util", "Respostas úteis: corretas + recusas corretas (manual)"),
        ]),
        ("Comportamento", [("palavras", "Tamanho médio da resposta (palavras)")]),
    ]
    modos = list(respostas)
    out = ["| Critério / métrica | " + " | ".join(MODOS[m] for m in modos) + " |",
           "|---|" + "---:|" * len(modos)]
    for criterio, metricas in estrutura:
        out.append(f"| **{criterio}** |" + " |" * len(modos))
        for chave, nome in metricas:
            if chave in linhas[modos[0]]:
                out.append(f"| {nome} | " + " | ".join(linhas[m][chave] for m in modos) + " |")
    return "\n".join(out)


def matriz_perguntas(respostas: dict, revisao: dict | None) -> str:
    casos = [c for c in carregar_perguntas() if c["split"] == "teste"]
    modos = list(respostas)
    por_id = {m: {i["id"]: i for i in respostas[m]} for m in modos}
    out = ["| ID | Pergunta | Fonte | " + " | ".join(LETRA[m] for m in modos) + " |",
           "|---|---|---|" + "---|" * len(modos)]
    for c in casos:
        celulas = []
        for m in modos:
            texto = SIGLA_AUTO[por_id[m][c["id"]]["avaliacao"]["categoria"]]
            if revisao:
                rot = revisao[m][c["id"]]["rotulo"]
                if rot != por_id[m][c["id"]]["avaliacao"]["categoria"]:
                    texto += f"<br>*{ROTULOS[rot]}*"
            celulas.append(texto)
        out.append(f"| {c['id']} | {c['pergunta']} | {c['fonte'] or 'fora da base'} | " + " | ".join(celulas) + " |")
    return "\n".join(out)


def transicoes(respostas: dict, revisao: dict) -> str:
    pares = [("base_sem_contexto", "base_com_contexto", "A → B: efeito do grounding"),
             ("base_com_contexto", "lora_com_contexto", "B → D: efeito do LoRA com grounding"),
             ("base_sem_contexto", "lora_sem_contexto", "A → C: efeito do LoRA sem grounding")]
    out = ["| Comparação | Passou a acertar | Deixou de acertar | Saldo |", "|---|---|---|---:|"]
    for de, para, nome in pares:
        ids = [i["id"] for i in respostas[de]]
        ok = lambda m, i: revisao[m][i]["rotulo"] in UTIL
        ganhou = [i for i in ids if ok(para, i) and not ok(de, i)]
        perdeu = [i for i in ids if ok(de, i) and not ok(para, i)]
        out.append(f"| {nome} | {', '.join(ganhou) or '—'} | {', '.join(perdeu) or '—'} | {len(ganhou) - len(perdeu):+d} |")
    return "\n".join(out)


def busca_fora_da_base(respostas: dict, revisao: dict | None) -> str:
    out = ["| ID | Pergunta | 1º trecho recuperado | Pontuação BM25 | B | D |", "|---|---|---|---:|---|---|"]
    for c in (c for c in carregar_perguntas() if c["split"] == "teste" and c["fonte"] is None):
        topo = buscar(c["pergunta"], K_TRECHOS)
        trecho, score = (topo[0][0].referencia.replace(" | ", " — "), f"{topo[0][1]:.1f}") if topo else ("—", "0")
        cel = []
        for m in ("base_com_contexto", "lora_com_contexto"):
            item = next(i for i in respostas[m] if i["id"] == c["id"])
            cel.append(ROTULOS[revisao[m][c["id"]]["rotulo"]] if revisao else item["avaliacao"]["categoria"])
        out.append(f"| {c['id']} | {c['pergunta']} | {trecho} | {score} | {cel[0]} | {cel[1]} |")
    return "\n".join(out)


def auto_x_manual(respostas: dict, revisao: dict) -> str:
    concorda = {"correta": {"correta"}, "recusa_correta": {"recusa_correta"}, "recusa_indevida": {"recusa_indevida"},
                "incorreta": {"inventou", "vaga", "contexto_mal_usado", "parcial"},
                "incompleta": {"inventou", "vaga", "parcial"}, "alucinacao": {"inventou", "vaga", "contexto_mal_usado"}}
    out = ["| Modo | Concordância | Divergências |", "|---|---:|---|"]
    for m, itens in respostas.items():
        div = [f"{i['id']} ({i['avaliacao']['categoria']} → {ROTULOS[revisao[m][i['id']]['rotulo']]})"
               for i in itens if revisao[m][i["id"]]["rotulo"] not in concorda[i["avaliacao"]["categoria"]]]
        out.append(f"| {MODOS[m]} | {len(itens) - len(div)}/{len(itens)} | {'; '.join(div) or '—'} |")
    return "\n".join(out)


def exemplos(respostas: dict, ids: list[str], revisao: dict | None) -> str:
    blocos = []
    for caso_id in ids:
        linhas = []
        for modo, nome in MODOS.items():
            item = next((r for r in respostas.get(modo, []) if r["id"] == caso_id), None)
            if item:
                if not linhas:
                    linhas.append(f"### {caso_id} — {item['pergunta']}\n")
                resposta = item["resposta"].replace("\n", " ")
                rotulo = ROTULOS[revisao[modo][caso_id]["rotulo"]] if revisao else item["avaliacao"]["categoria"]
                linhas.append(f"- **{nome}** ({rotulo}): {resposta}")
        blocos.append("\n".join(linhas))
    return "\n\n".join(blocos)


def gerar_relatorio(pasta: Path = PASTA_RESULTS, ids_exemplo: list[str] | None = None) -> str:
    respostas = json.loads((pasta / "respostas.json").read_text(encoding="utf-8"))
    revisao = _carregar_revisao(pasta, respostas)
    interpretacao = pasta / "interpretacao.md"
    ids_exemplo = ids_exemplo or ["A01", "A07", "A09", "A14", "A18", "A19"]

    partes = [
        "# Relatório de avaliação — Assistente de Conhecimento Interno (Porto Ventura Terminais)\n",
        "Gerado por `assistente/relatorio.py` a partir de `results/respostas.json`"
        + (" e `results/revisao_manual.json`." if revisao else ".")
        + " Conjunto de teste: 20 perguntas, sendo 14 com resposta na base e 6 fora da base. "
        "Cada célula mostra *acertos/total (%)*; o total muda conforme o critério (14 perguntas na base, "
        "6 fora da base, 20 no geral ou só as recusas).\n",
        "## 1. Matriz critério × modo\n",
        "Os quatro critérios de aceitação do projeto, cada um medido por métricas automáticas "
        "(calculadas pelo avaliador contra o gabarito) e manuais (revisão de cada resposta, "
        "em `results/revisao_manual.json`).\n",
        matriz_criterios(respostas, revisao),
    ]
    if interpretacao.exists():
        partes.append("\n" + interpretacao.read_text(encoding="utf-8").strip())
    partes += ["\n## 3. Resultado por pergunta\n",
               "Categoria automática em cada célula; quando a revisão manual discorda ou detalha o erro, "
               "o rótulo manual aparece em itálico.\n",
               matriz_perguntas(respostas, revisao)]
    if revisao:
        partes += ["\n## 4. O que mudou entre os modos (revisão manual)\n",
                   "Perguntas que passaram a ter (ou deixaram de ter) resposta útil — correta, correta com "
                   "outras palavras ou recusa correta — de um modo para outro.\n",
                   transicoes(respostas, revisao)]
    partes += ["\n## 5. Por que as perguntas fora da base são difíceis para a busca\n",
               "A busca sempre devolve os trechos mais parecidos, mesmo quando nenhum responde. "
               "A tabela mostra o 1º trecho entregue ao modelo nas 6 perguntas fora da base.\n",
               busca_fora_da_base(respostas, revisao)]
    if revisao:
        partes += ["\n## 6. Avaliação automática × revisão manual\n",
                   auto_x_manual(respostas, revisao)]
    partes += ["\n## 7. Exemplos de respostas\n", exemplos(respostas, ids_exemplo, revisao)]

    texto = "\n".join(partes) + "\n"
    (pasta / "relatorio.md").write_text(texto, encoding="utf-8")
    return texto
