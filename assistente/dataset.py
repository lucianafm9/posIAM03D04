"""Monta os conjuntos de treino (formato chat da aula) e de teste a partir de data/perguntas.json."""

import json
from pathlib import Path

from .busca import buscar
from .prompts import montar_mensagens, resposta_alvo

PASTA_DATA = Path(__file__).resolve().parent.parent / "data"
K_TRECHOS = 3


def carregar_perguntas(caminho: Path = PASTA_DATA / "perguntas.json") -> list[dict]:
    return json.loads(caminho.read_text(encoding="utf-8"))


def exemplo_treino(caso: dict, k: int = K_TRECHOS) -> dict:
    # o contexto do treino vem da mesma busca usada na inferência,
    # para o modelo aprender a lidar com trechos irrelevantes (perguntas fora da base)
    trechos = [t for t, _ in buscar(caso["pergunta"], k)]
    mensagens = montar_mensagens(caso["pergunta"], trechos)
    mensagens.append({"role": "assistant", "content": resposta_alvo(caso["resposta"], caso["fonte"])})
    return {"id": caso["id"], "messages": mensagens}


def gerar(saida: Path = PASTA_DATA) -> tuple[int, int]:
    perguntas = carregar_perguntas()
    treino = [exemplo_treino(c) for c in perguntas if c["split"] == "treino"]
    teste = [c for c in perguntas if c["split"] == "teste"]
    with open(saida / "treino.jsonl", "w", encoding="utf-8") as f:
        for ex in treino:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    with open(saida / "teste.jsonl", "w", encoding="utf-8") as f:
        for c in teste:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    return len(treino), len(teste)
