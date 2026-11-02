"""Recuperação dos trechos relevantes com BM25 (implementação própria, sem dependências)."""

import math
from collections import Counter

from .base import Trecho, carregar_base
from .texto import tokens


class BuscaBM25:
    def __init__(self, trechos: list[Trecho], k1: float = 1.5, b: float = 0.75):
        self.trechos = trechos
        self.k1, self.b = k1, b
        # o título do documento e da seção entram no índice: ajudam perguntas curtas
        self._docs = [Counter(tokens(f"{t.documento} {t.secao} {t.secao} {t.texto}")) for t in trechos]
        self._tam = [sum(d.values()) for d in self._docs]
        self._media = sum(self._tam) / len(self._tam)
        df = Counter(termo for d in self._docs for termo in d)
        n = len(trechos)
        self._idf = {termo: math.log(1 + (n - f + 0.5) / (f + 0.5)) for termo, f in df.items()}

    def _pontuar(self, consulta: list[str], i: int) -> float:
        doc, tam, score = self._docs[i], self._tam[i], 0.0
        for termo in consulta:
            tf = doc.get(termo, 0)
            if tf:
                score += self._idf[termo] * tf * (self.k1 + 1) / (
                    tf + self.k1 * (1 - self.b + self.b * tam / self._media))
        return score

    def buscar(self, pergunta: str, k: int = 3) -> list[tuple[Trecho, float]]:
        consulta = tokens(pergunta)
        pontuados = [(t, self._pontuar(consulta, i)) for i, t in enumerate(self.trechos)]
        pontuados = [p for p in pontuados if p[1] > 0]
        pontuados.sort(key=lambda p: p[1], reverse=True)
        return pontuados[:k]


_busca_padrao: BuscaBM25 | None = None


def buscar(pergunta: str, k: int = 3) -> list[tuple[Trecho, float]]:
    global _busca_padrao
    if _busca_padrao is None:
        _busca_padrao = BuscaBM25(carregar_base())
    return _busca_padrao.buscar(pergunta, k)
