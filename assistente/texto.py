"""Normalização de texto usada pela busca e pela avaliação."""

import re
import unicodedata

STOPWORDS = set("""
a o as os um uma uns umas de do da dos das em no na nos nas por pelo pela pelos pelas
para pra com sem sob sobre e ou que se qual quais quanto quantos quanta quantas quando
como onde ao aos à às é são ser foi está estão tem têm ter há eu meu minha meus minhas
seu sua seus suas nosso nossa me te lhe posso pode podem preciso precisa devo deve
isso esse essa este esta aquele aquela mais menos muito já não sim após antes depois
""".split())


def sem_acentos(texto: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", texto) if unicodedata.category(c) != "Mn")


def normalizar(texto: str) -> str:
    texto = sem_acentos(texto.lower())
    texto = re.sub(r"[^\w$,%]+", " ", texto)
    return re.sub(r"\s+", " ", texto).strip()


def _radical(token: str) -> str:
    # radical simples: tira plural e algumas terminações comuns do português
    for sufixo in ("coes", "oes", "aes", "es", "s"):
        if token.endswith(sufixo) and len(token) - len(sufixo) >= 4:
            return token[: -len(sufixo)]
    return token


_STOPWORDS_NORM = {sem_acentos(s) for s in STOPWORDS}


def tokens(texto: str) -> list[str]:
    return [_radical(t) for t in normalizar(texto).replace(",", " ").split()
            if t not in _STOPWORDS_NORM and len(t) > 1]
