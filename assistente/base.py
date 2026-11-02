"""Carrega a base de conhecimento e divide cada documento em trechos (uma seção = um trecho)."""

import re
from dataclasses import dataclass
from pathlib import Path

PASTA_BASE = Path(__file__).resolve().parent.parent / "base_conhecimento"


@dataclass(frozen=True)
class Trecho:
    doc_id: str      # ex.: "POL-01"
    documento: str   # título do documento
    secao: str       # título da seção (## ...)
    texto: str

    @property
    def referencia(self) -> str:
        return f"{self.doc_id} | {self.secao}"


def _ler_documento(caminho: Path) -> list[Trecho]:
    linhas = caminho.read_text(encoding="utf-8").splitlines()
    titulo = linhas[0].lstrip("# ").strip()
    m = re.match(r"(POL-\d{2})\s*[—-]\s*(.+)", titulo)
    if not m:
        raise ValueError(f"{caminho.name}: título fora do padrão 'POL-NN — Nome'")
    doc_id, documento = m.group(1), m.group(2)

    trechos, secao, corpo = [], None, []
    for linha in linhas[1:] + ["## <fim>"]:
        if linha.startswith("## "):
            if secao and secao != "Objetivo":
                texto = "\n".join(corpo).strip()
                if texto:
                    trechos.append(Trecho(doc_id, documento, secao, texto))
            secao, corpo = linha[3:].strip(), []
        elif secao:
            corpo.append(linha)
    return trechos


def carregar_base(pasta: Path = PASTA_BASE) -> list[Trecho]:
    trechos = []
    for caminho in sorted(pasta.glob("POL-*.md")):
        trechos.extend(_ler_documento(caminho))
    return trechos


def texto_documento(doc_id: str, pasta: Path = PASTA_BASE) -> str:
    """Texto completo de um documento (usado nos testes para conferir o gabarito)."""
    caminho = next(pasta.glob(f"{doc_id}_*.md"))
    return caminho.read_text(encoding="utf-8")
