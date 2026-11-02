"""Avalia só a recuperação (sem modelo, roda em qualquer máquina).

Para cada pergunta que está na base, verifica se algum dos 3 trechos recuperados vem
do documento correto (recall@3) e se o primeiro trecho já é do documento correto (acerto@1).
Uso: python scripts/avaliar_busca.py
"""

import json
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(RAIZ))

from assistente.busca import buscar  # noqa: E402
from assistente.dataset import K_TRECHOS, carregar_perguntas  # noqa: E402


def main() -> None:
    linhas, resultado = [], {}
    for split in ("treino", "teste"):
        casos = [c for c in carregar_perguntas() if c["split"] == split and c["fonte"]]
        top1 = recall = 0
        for c in casos:
            docs = [t.doc_id for t, _ in buscar(c["pergunta"], K_TRECHOS)]
            top1 += bool(docs) and docs[0] == c["fonte"]
            recall += c["fonte"] in docs
            if c["fonte"] not in docs:
                linhas.append(f"  falhou {c['id']}: {c['pergunta']} -> {docs}")
        resultado[split] = {"perguntas": len(casos),
                            "acerto_top1": round(100 * top1 / len(casos), 1),
                            f"recall_top{K_TRECHOS}": round(100 * recall / len(casos), 1)}
        print(f"{split}: {resultado[split]}")
    print("\n".join(linhas) or "  nenhuma falha de recuperação")
    (RAIZ / "results" / "avaliacao_busca.json").write_text(
        json.dumps(resultado, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
