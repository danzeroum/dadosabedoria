"""SAUDE-03 Sentinela Materna — risco nutricional de gestantes (SISVAN/MS).

Pergunta do produto: **qual a prevalência de baixo peso em gestantes acompanhadas pelo SISVAN
no município?**

Baixo peso materno (IMC pré-gestacional < 18,5 kg/m²) aumenta o risco de prematuridade,
baixo peso ao nascer e déficit cognitivo. O SISVAN monitora gestantes inscritas no
CadÚnico/Bolsa Família — não é censo da população gestante total.

HONESTIDADE:
- Cobre apenas gestantes acompanhadas pelo SISVAN (Atenção Básica/CadÚnico) — não é censo.
- Municípios com maior cobertura de acompanhamento podem apresentar taxas aparentemente
  maiores, pois captam mais casos.
- Lag típico: ~6–12 meses após a competência de acompanhamento.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

NivelMaterno = Literal["crítico", "elevado", "moderado", "baixo", "sem_dado"]

_LIMIAR_CRITICO = 30.0  # ≥ 30% gestantes com baixo peso
_LIMIAR_ELEVADO = 20.0  # ≥ 20%
_LIMIAR_MODERADO = 10.0  # ≥ 10%

NOTA_HONESTA = (
    "O SISVAN monitora gestantes inscritas no CadÚnico/Bolsa Família — não é censo da população. "
    "Municípios com cobertura baixa podem apresentar distorção. Lag típico: 6-12 meses. "
    "Baixo peso materno aumenta o risco de prematuridade, baixo peso ao nascer "
    "e déficit cognitivo. "
    "Dados suprimidos (< 5 gestantes) preservam privacidade estatística. "
    "Este indicador não identifica gestantes. Dado agregado por município."
)


@dataclass(frozen=True)
class SentinelaMaterna:
    """Contrato do produto Sentinela Materna por município/ano."""

    codigo_ibge: str
    nome: str
    uf: str | None
    populacao: int | None
    ano: int | None
    n_gestantes: int | None
    gestante_baixo_peso_pct: float | None
    nivel: NivelMaterno


def classificar_nivel(pct: float | None) -> NivelMaterno:
    """Classifica o nível de risco nutricional materno dado o % de baixo peso."""
    if pct is None:
        return "sem_dado"
    if pct >= _LIMIAR_CRITICO:
        return "crítico"
    if pct >= _LIMIAR_ELEVADO:
        return "elevado"
    if pct >= _LIMIAR_MODERADO:
        return "moderado"
    return "baixo"


def calcular(
    codigo_ibge: str,
    nome: str,
    uf: str | None,
    populacao: int | None,
    *,
    ano: int | None,
    n_gestantes: int | None,
    gestante_baixo_peso_pct: float | None,
) -> SentinelaMaterna:
    """Monta o produto Sentinela Materna a partir dos valores do banco."""
    pct = round(gestante_baixo_peso_pct, 2) if gestante_baixo_peso_pct is not None else None
    nivel = classificar_nivel(pct)
    return SentinelaMaterna(
        codigo_ibge=codigo_ibge,
        nome=nome,
        uf=uf,
        populacao=populacao,
        ano=ano,
        n_gestantes=n_gestantes,
        gestante_baixo_peso_pct=pct,
        nivel=nivel,
    )
