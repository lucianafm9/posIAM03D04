"""Avaliação automática das respostas contra o gabarito (fatos esperados ou recusa)."""

import re

from .texto import normalizar

CATEGORIAS = ["correta", "incompleta", "incorreta", "recusa_indevida", "recusa_correta", "alucinacao"]


def e_recusa(resposta: str) -> bool:
    r = normalizar(resposta)
    return any(p in r for p in ("nao encontrei essa informacao", "nao encontrei a informacao",
                                "nao consta na base", "nao esta no contexto"))


def fato_presente(fato: str, resposta_norm: str) -> bool:
    """Um fato pode ter variações separadas por '|', ex.: '30 minutos|meia hora'."""
    return any(normalizar(v) in resposta_norm for v in fato.split("|"))


def cita_fonte(resposta: str, fonte: str) -> bool:
    return re.search(rf"\b{fonte}\b", resposta) is not None


def avaliar(resposta: str, caso: dict) -> dict:
    """caso: {'fonte': 'POL-01' ou None, 'fatos': [...]}"""
    resposta_norm = normalizar(resposta)
    recusou = e_recusa(resposta)

    if caso["fonte"] is None:  # pergunta fora da base: o certo é recusar
        categoria = "recusa_correta" if recusou else "alucinacao"
        return {"categoria": categoria, "fatos_ok": 0, "fatos_total": 0, "cita_fonte": None}

    ok = sum(fato_presente(f, resposta_norm) for f in caso["fatos"])
    total = len(caso["fatos"])
    if recusou:
        categoria = "recusa_indevida"
    elif ok == total:
        categoria = "correta"
    elif ok > 0:
        categoria = "incompleta"
    else:
        categoria = "incorreta"  # respondeu sem nenhum fato da base: provável alucinação
    return {"categoria": categoria, "fatos_ok": ok, "fatos_total": total,
            "cita_fonte": cita_fonte(resposta, caso["fonte"])}


def resumir(avaliacoes: list[dict], casos: list[dict]) -> dict:
    n = len(casos)
    na_base = [a for a, c in zip(avaliacoes, casos) if c["fonte"] is not None]
    fora = [a for a, c in zip(avaliacoes, casos) if c["fonte"] is None]
    cont = {cat: sum(a["categoria"] == cat for a in avaliacoes) for cat in CATEGORIAS}
    pct = lambda x, total: round(100 * x / total, 1) if total else 0.0
    return {
        "total": n,
        "contagem": cont,
        # acerto geral: respondeu certo o que está na base e recusou o que não está
        "acerto_geral": pct(cont["correta"] + cont["recusa_correta"], n),
        "acerto_na_base": pct(cont["correta"], len(na_base)),
        "fatos_cobertos": pct(sum(a["fatos_ok"] for a in na_base), sum(a["fatos_total"] for a in na_base)),
        "recusa_correta_fora_base": pct(cont["recusa_correta"], len(fora)),
        # alucinação: inventou resposta para pergunta fora da base ou respondeu sem nenhum fato correto
        "taxa_alucinacao": pct(cont["alucinacao"] + cont["incorreta"], n),
        "cita_fonte": pct(sum(bool(a["cita_fonte"]) for a in na_base), len(na_base)),
    }
