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


def _tokens(texto: str) -> list[str]:
    return [t for t in re.split(r"\W+", _normalizar(texto)) if len(t) > 3]


def _tokens_codigo(codigo: str) -> list[str]:
    """Vocabulário do próprio código namespaced (``trabalho.emprego.saldo_caged`` → trabalho,
    emprego, saldo, caged) — termos do dado que a pergunta livre costuma usar (ex.: 'emprego')."""
    return [t for t in re.split(r"[._]+", _normalizar(codigo)) if len(t) > 3]


def _casa(tok: str, palavras: set[str]) -> bool:
    """Casa por igualdade OU prefixo — tolera flexão/plural: ``emprego`` ~ ``empregos``."""
    return any(tok == w or w.startswith(tok) or tok.startswith(w) for w in palavras)


# Sinônimos do dia a dia → domínio. O léxico do código/nome já cobre os termos técnicos do dado
# ('emprego', 'internacoes', 'matriculas'…); aqui entram as palavras que o cidadão usa e que NÃO
# aparecem no dado. Só termos não-ambíguos (de fora: 'banco', 'receita', 'carteira', 'vaga').
_SINONIMOS: dict[str, str] = {
    "hospital": "saude",
    "doente": "saude",
    "internado": "saude",
    "escola": "educacao",
    "aluno": "educacao",
    "estudante": "educacao",
    "creche": "educacao",
    "repasse": "financas",
    "emprestimo": "credito",
    "financiamento": "credito",
    "licitacao": "compras",
    "fornecedor": "compras",
    "pregao": "compras",
    "desemprego": "trabalho",
    "trabalhador": "trabalho",
}


def identificar_indicador(pergunta: str, catalogo: list[tuple[str, str]]) -> str | None:
    """Casa a pergunta com o catálogo ``[(codigo, nome)]``. Retorna o melhor ou None (abster).

    Conta o NOME e o CÓDIGO namespaced (o dado tem seu próprio léxico: 'emprego', 'credito',
    'internacoes'…) como duas fontes, com casamento por prefixo p/ flexão. Um termo forte aparece
    nas DUAS (emprego/empregos, credito/credito) → score 2; uma palavra genérica só do código
    ('total') casa uma vez → fica abaixo do limiar, sem falso-positivo nem inflar o ruído.

    Acresce um SINÔNIMO do dia a dia (peso 2) quando o cidadão usa uma palavra que não está no dado
    mas aponta o domínio sem ambiguidade ('hospital'→saude, 'escola'→educacao) — recall p/ leigos.
    """
    p = _normalizar(pergunta)
    palavras = set(_tokens(pergunta))
    melhor: str | None = None
    melhor_score = 0
    for codigo, nome in catalogo:
        dominio = _normalizar(codigo).split(".", 1)[0]
        score = 5 if _normalizar(codigo) in p else 0
        score += sum(1 for tok in set(_tokens_codigo(codigo)) if _casa(tok, palavras))
        score += sum(1 for tok in set(_tokens(nome)) if _casa(tok, palavras))
        score += 2 * sum(
            1 for termo, dom in _SINONIMOS.items() if dom == dominio and _casa(termo, palavras)
        )
        if score > melhor_score:
            melhor, melhor_score = codigo, score
    return melhor if melhor_score >= 2 else None


# --- Ancoragem numérica (invariante 3: o narrador NÃO inventa números) -------------------------
_SEP_NUM = re.compile(r"(?<=\d)[.,](?=\d)")  # separador de milhar/decimal entre dígitos
_NUM = re.compile(r"\d{2,}")  # números com 2+ dígitos (onde moram valores que não podem surgir)


def numeros(texto: str) -> set[str]:
    """Números (>= 2 dígitos) do texto, normalizados sem separador (``8.200`` ~ ``8200``)."""
    return set(_NUM.findall(_SEP_NUM.sub("", texto)))


def validar_numeros_ancorados(resposta: str, permitidos: set[str]) -> bool:
    """True se TODO número (>= 2 díg.) da resposta consta do dado recuperado (``permitidos``).

    Trava mecânica do invariante 3: se o LLM cuspir um número que não veio do repositório, reprova
    (e o serviço cai para o narrador determinístico).
    """
    return numeros(resposta) <= permitidos
