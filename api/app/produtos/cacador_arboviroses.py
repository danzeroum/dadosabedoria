"""Caçador de Arboviroses (SAUDE-02) — dengue confirmada por 100 mil habitantes/ano.

Pergunta do produto: **qual a incidência de dengue confirmada no município no último
ano disponível?**

HONESTIDADE:
- Cobre apenas casos notificados ao SINAN — subnotificação estimada em 3 a 10×.
- O k-anonimato (n_minimo=5) suprime municípios com menos de 5 casos confirmados.
- Incidência = casos confirmados / população (Censo 2022); None se pop. indisponível.
- Lag típico: 6–12 meses após o ano de notificação.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

NivelArboviroses = Literal["crítico", "elevado", "moderado", "baixo", "sem_dado"]

#: Limiares de incidência/100k hab (referência epidemiológica MS/PAHO).
_LIMIAR_CRITICO = 300.0  # ≥ 300 casos/100k → situação epidêmica
_LIMIAR_ELEVADO = 100.0  # ≥ 100 casos/100k → alto risco
_LIMIAR_MODERADO = 20.0  # ≥  20 casos/100k → moderado

NOTA_HONESTA = (
    "Casos confirmados de dengue por 100 mil habitantes, por município/ano, "
    "fonte: SINAN (Sistema de Informação de Agravos de Notificação/MS). "
    "Cobre dengue clássico, com sinais de alarme e grave (CLASSI_FIN 1-3). "
    "Inclui apenas casos notificados — subnotificação estimada em 3-10x. "
    "Incidência = casos / população (Censo 2022). Lag típico: 6-12 meses. "
    "(SAUDE-02, dupla face §17)."
)


@dataclass(frozen=True)
class CacadorArboviroses:
    """Contrato do produto Caçador de Arboviroses por município/ano."""

    codigo_ibge: str
    nome: str
    uf: str | None
    populacao: int | None
    ano: int | None
    casos_confirmados: int | None
    incidencia_100k: float | None
    nivel: NivelArboviroses


def classificar_nivel(incidencia_100k: float | None) -> NivelArboviroses:
    """Classifica o nível de risco de arboviroses dada a incidência por 100k hab."""
    if incidencia_100k is None:
        return "sem_dado"
    if incidencia_100k >= _LIMIAR_CRITICO:
        return "crítico"
    if incidencia_100k >= _LIMIAR_ELEVADO:
        return "elevado"
    if incidencia_100k >= _LIMIAR_MODERADO:
        return "moderado"
    return "baixo"


def calcular(
    codigo_ibge: str,
    nome: str,
    uf: str | None,
    populacao: int | None,
    *,
    ano: int | None,
    casos_confirmados: int | None,
) -> CacadorArboviroses:
    """Monta o produto Caçador de Arboviroses a partir dos valores do banco."""
    incidencia: float | None = None
    if casos_confirmados is not None and populacao is not None and populacao > 0:
        incidencia = round((casos_confirmados / populacao) * 100_000, 2)

    return CacadorArboviroses(
        codigo_ibge=codigo_ibge,
        nome=nome,
        uf=uf,
        populacao=populacao,
        ano=ano,
        casos_confirmados=casos_confirmados,
        incidencia_100k=incidencia,
        nivel=classificar_nivel(incidencia),
    )
