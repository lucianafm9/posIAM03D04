"""Reavalia as respostas geradas no Colab com o avaliador atual, sem rodar o modelo de novo.

Lê results/respostas.json, recalcula a categoria de cada resposta e regrava
results/respostas.json, results/metricas.json e results/relatorio.md.
Uso: python scripts/reavaliar.py
"""

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(RAIZ))

from assistente.avaliacao import avaliar, resumir  # noqa: E402
from assistente.dataset import carregar_perguntas  # noqa: E402
from assistente.relatorio import PASTA_RESULTS, gerar_relatorio  # noqa: E402


def main() -> None:
    casos = {c["id"]: c for c in carregar_perguntas() if c["split"] == "teste"}
    respostas = json.loads((PASTA_RESULTS / "respostas.json").read_text(encoding="utf-8"))
    metricas, mudancas = {}, []
    for modo, itens in respostas.items():
        for item in itens:
            nova = avaliar(item["resposta"], casos[item["id"]])
            if nova["categoria"] != item["avaliacao"]["categoria"]:
                mudancas.append(f"  {modo:18} {item['id']}: {item['avaliacao']['categoria']} -> {nova['categoria']}")
            item["avaliacao"] = nova
        metricas[modo] = resumir([i["avaliacao"] for i in itens], [casos[i["id"]] for i in itens])
        print(modo, {k: metricas[modo][k] for k in ("acerto_geral", "taxa_alucinacao", "recusa_correta_fora_base")})

    print("\nCategorias alteradas:\n" + ("\n".join(mudancas) or "  nenhuma"))
    (PASTA_RESULTS / "respostas.json").write_text(json.dumps(respostas, ensure_ascii=False, indent=2), encoding="utf-8")
    (PASTA_RESULTS / "metricas.json").write_text(json.dumps(metricas, ensure_ascii=False, indent=2), encoding="utf-8")
    gerar_relatorio()


if __name__ == "__main__":
    main()
