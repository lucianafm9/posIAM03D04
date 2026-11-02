"""Gera a tabela comparativa (markdown) a partir dos resultados salvos pelo notebook."""

import json
from pathlib import Path

PASTA_RESULTS = Path(__file__).resolve().parent.parent / "results"

MODOS = {
    "base_sem_contexto": "A. Base sem contexto",
    "base_com_contexto": "B. Base com contexto (grounding)",
    "lora_sem_contexto": "C. LoRA sem contexto",
    "lora_com_contexto": "D. LoRA com contexto",
}

METRICAS = [
    ("acerto_geral", "Acerto geral"),
    ("acerto_na_base", "Acerto (perguntas na base)"),
    ("fatos_cobertos", "Fatos cobertos"),
    ("recusa_correta_fora_base", "Recusa correta (fora da base)"),
    ("taxa_alucinacao", "Taxa de alucinação"),
    ("cita_fonte", "Cita a fonte"),
]


def tabela(metricas: dict) -> str:
    modos = [m for m in MODOS if m in metricas]
    linhas = ["| Métrica | " + " | ".join(MODOS[m] for m in modos) + " |",
              "|---|" + "---:|" * len(modos)]
    for chave, nome in METRICAS:
        linhas.append(f"| {nome} | " + " | ".join(f"{metricas[m][chave]:.1f}%" for m in modos) + " |")
    return "\n".join(linhas)


def exemplos(respostas: dict, ids: list[str]) -> str:
    blocos = []
    for caso_id in ids:
        linhas = []
        for modo, nome in MODOS.items():
            item = next((r for r in respostas.get(modo, []) if r["id"] == caso_id), None)
            if item:
                if not linhas:
                    linhas.append(f"### {caso_id} — {item['pergunta']}\n")
                resposta = item["resposta"].replace("\n", " ")
                linhas.append(f"- **{nome}** ({item['avaliacao']['categoria']}): {resposta}")
        blocos.append("\n".join(linhas))
    return "\n\n".join(blocos)


def gerar_relatorio(pasta: Path = PASTA_RESULTS, ids_exemplo: list[str] | None = None) -> str:
    metricas = json.loads((pasta / "metricas.json").read_text(encoding="utf-8"))
    respostas = json.loads((pasta / "respostas.json").read_text(encoding="utf-8"))
    ids_exemplo = ids_exemplo or ["A01", "A03", "A09", "A14", "A15", "A18"]
    texto = (
        "# Resultado da avaliação\n\n"
        "Gerado automaticamente pelo notebook a partir de `results/metricas.json` e `results/respostas.json`.\n\n"
        "## Métricas por modo\n\n" + tabela(metricas) + "\n\n"
        "## Exemplos de respostas\n\n" + exemplos(respostas, ids_exemplo) + "\n"
    )
    (pasta / "relatorio.md").write_text(texto, encoding="utf-8")
    return texto
