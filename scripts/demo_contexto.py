"""Mostra a estrutura de contexto montada para uma pergunta (sem modelo).

Uso:
  python scripts/demo_contexto.py
  python scripts/demo_contexto.py "Qual o free time para contêiner de importação?"
"""

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from assistente.busca import buscar  # noqa: E402
from assistente.dataset import K_TRECHOS  # noqa: E402
from assistente.prompts import montar_mensagens  # noqa: E402

PERGUNTAS_PADRAO = [
    "Meu motorista chegou 40 minutos depois do fim da janela. Ele ainda pode entrar?",
    "Quantos dias de licença-paternidade a empresa concede?",
]


def mostrar(pergunta: str) -> None:
    print("=" * 80)
    print(f"PERGUNTA: {pergunta}\n")
    resultados = buscar(pergunta, K_TRECHOS)
    print("Trechos recuperados (BM25):")
    for trecho, score in resultados:
        print(f"  {score:5.2f}  {trecho.referencia}")
    print("\nMensagens enviadas ao modelo (modo com grounding):")
    for m in montar_mensagens(pergunta, [t for t, _ in resultados]):
        print(f"--- {m['role']} ---\n{m['content']}\n")


if __name__ == "__main__":
    for p in sys.argv[1:] or PERGUNTAS_PADRAO:
        mostrar(p)
