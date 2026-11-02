"""Gera data/treino.jsonl e data/teste.jsonl. Uso: python scripts/gerar_dataset.py"""

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from assistente.dataset import gerar  # noqa: E402

if __name__ == "__main__":
    n_treino, n_teste = gerar()
    print(f"data/treino.jsonl: {n_treino} exemplos | data/teste.jsonl: {n_teste} casos")
