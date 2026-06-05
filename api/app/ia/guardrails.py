"""Guardrails da IA (§9): sanitiza entrada não confiável e resolve o escopo (qual indicador).

Não há acesso ao schema ``app`` (a IA roda como ``role_analitica``). A pergunta é tratada como
entrada não confiável: sanitizada e usada só para casar com o catálogo — nunca executada.
"""

from __future__ import annotations

import re
import unicodedata

LIMITE = 1000
_CONTROLE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f]")


def sanitizar(texto: str) -> str:
    return _CONTROLE.sub(" ", texto.strip()[:LIMITE])


def _normalizar(texto: str) -> str:
    nfkd = unicodedata.normalize("NFKD", texto.lower())
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def _tokens(nome: str) -> list[str]:
    return [t for t in re.split(r"\W+", _normalizar(nome)) if len(t) > 3]


def identificar_indicador(pergunta: str, catalogo: list[tuple[str, str]]) -> str | None:
    """Casa a pergunta com o catálogo ``[(codigo, nome)]``. Retorna o melhor ou None (abster)."""
    p = _normalizar(pergunta)
    melhor: str | None = None
    melhor_score = 0
    for codigo, nome in catalogo:
        score = 5 if codigo.lower() in p else 0
        score += sum(1 for tok in _tokens(nome) if tok in p)
        if score > melhor_score:
            melhor, melhor_score = codigo, score
    return melhor if melhor_score >= 2 else None
