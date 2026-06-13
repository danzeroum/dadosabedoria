"""Funções estatísticas puras para analytics inferencial.

Sem side-effects — usadas pelos endpoints de distribuição e perfil orçamentário.
"""

from __future__ import annotations

import math


def percentil_rank(valor: float, distribuicao: list[float]) -> float:
    """Percentil (0.0–100.0) de ``valor`` na ``distribuicao``.

    Usa a definição sem interpolação: fração de valores estritamente menores
    que ``valor``. Adequada para dados discretos e comparações municipais.
    """
    if not distribuicao:
        return 0.0
    n = len(distribuicao)
    below = sum(1 for v in distribuicao if v < valor)
    return round((below / n) * 100.0, 1)


def z_score(valor: float, media: float, desvio: float) -> float | None:
    """Z-score padronizado; ``None`` quando desvio ≤ 0 (todos os valores iguais)."""
    if desvio <= 0:
        return None
    return round((valor - media) / desvio, 3)


def p_valor_bilateral(z: float) -> float:
    """P-valor bilateral; aprox. via complemento da CDF normal padrão."""
    return 2.0 * (1.0 - _phi(abs(z)))


def _phi(x: float) -> float:
    """CDF da normal padrão — Abramowitz & Stegun (erro < 7.5e-8)."""
    t = 1.0 / (1.0 + 0.2316419 * abs(x))
    poly = t * (
        0.319381530 + t * (-0.356563782 + t * (1.781477937 + t * (-1.821255978 + t * 1.330274429)))
    )
    pdf = math.exp(-0.5 * x * x) / math.sqrt(2.0 * math.pi)
    return 1.0 - pdf * poly if x >= 0 else pdf * poly


def benjamini_hochberg(p_valores: list[float], alfa: float = 0.05) -> list[bool]:
    """Correção de Benjamini-Hochberg (FDR).

    Retorna lista de booleanos: ``True`` = hipótese rejeitada ao nível ``alfa``
    após correção para comparações múltiplas.
    """
    n = len(p_valores)
    if n == 0:
        return []
    indexed = sorted(enumerate(p_valores), key=lambda x: x[1])
    rejected = [False] * n
    max_k = -1
    for k, (_, p) in enumerate(indexed):
        if p <= (k + 1) * alfa / n:
            max_k = k
    for k in range(max_k + 1):
        rejected[indexed[k][0]] = True
    return rejected
