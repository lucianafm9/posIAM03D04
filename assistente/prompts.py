"""Estrutura de contexto: prompt de sistema, formatação dos trechos e montagem das mensagens."""

from .base import Trecho

RECUSA = "Não encontrei essa informação na base de conhecimento. Procure a área responsável pelo assunto."

# Modo sem grounding: o "chatbot genérico" que a empresa teria sem a base
SISTEMA_SEM_CONTEXTO = (
    "Você é o assistente interno do Porto Ventura Terminais, um terminal portuário. "
    "Responda às perguntas dos funcionários em português, de forma objetiva."
)

# Modo com grounding: o modelo só pode usar o que está no CONTEXTO
SISTEMA_COM_CONTEXTO = (
    "Você é o assistente de conhecimento interno do Porto Ventura Terminais. "
    "Responda à PERGUNTA usando somente as informações do CONTEXTO, que traz trechos das políticas internas. "
    "Não use conhecimento externo e não invente prazos, valores ou regras. "
    f'Se a resposta não estiver no CONTEXTO, responda exatamente: "{RECUSA}" '
    "Responda em português, em no máximo 3 frases, e termine com a fonte no formato [Fonte: POL-NN]."
)


def formatar_contexto(trechos: list[Trecho]) -> str:
    if not trechos:
        return "(nenhum trecho encontrado)"
    return "\n\n".join(f"[{t.doc_id} — {t.documento} — {t.secao}]\n{t.texto}" for t in trechos)


def montar_mensagens(pergunta: str, trechos: list[Trecho] | None = None) -> list[dict]:
    """trechos=None → modo sem grounding; lista (mesmo vazia) → modo com grounding."""
    if trechos is None:
        return [
            {"role": "system", "content": SISTEMA_SEM_CONTEXTO},
            {"role": "user", "content": pergunta},
        ]
    return [
        {"role": "system", "content": SISTEMA_COM_CONTEXTO},
        {"role": "user", "content": f"CONTEXTO:\n{formatar_contexto(trechos)}\n\nPERGUNTA: {pergunta}"},
    ]


def resposta_alvo(resposta: str | None, fonte: str | None) -> str:
    """Texto que o modelo deve aprender a gerar no fine-tuning."""
    if fonte is None:
        return RECUSA
    return f"{resposta} [Fonte: {fonte}]"
