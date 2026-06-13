"""Fome Oculta (ALIM-02) — insegurança nutricional de crianças < 5 anos (SISVAN/MS).

Pergunta do produto: **qual a prevalência de baixo peso em crianças menores de 5 anos
acompanhadas pelo SISVAN no município?**

"Fome oculta" refere-se à deficiência de micronutrientes e subnutrição que não aparece
nos dados de renda ou fome absoluta — o indicador de baixo peso (magreza + magreza acentuada)
é o marcador epidemiológico mais disponível com cobertura municipal.

HONESTIDADE:
- Cobre apenas crianças acompanhadas pelo SISVAN (Atenção Básica/CadÚnico) — não é censo.
- Municípios com maior cobertura de acompanhamento podem apresentar taxas aparentemente
  maiores, pois captam mais casos.
- Lag típico: ~6–12 meses após a competência de acompanhamento.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

NivelFomeOculta = Literal["crítico", "elevado", "moderado", "baixo", "sem_dado"]

#: Limiares provisórios de % de crianças < 5 com baixo peso (ALIM-02, dupla face §17).
_LIMIAR_CRITICO = 10.0  # ≥ 10% → crítico
_LIMIAR_ELEVADO = 5.0  # ≥ 5% → elevado
_LIMIAR_MODERADO = 2.0  # ≥ 2% → moderado

NOTA_HONESTA = (
    "Prevalência de baixo peso (magreza acentuada + magreza) em crianças < 5 anos "
    "acompanhadas pelo SISVAN (Sistema de Vigilância Alimentar e Nutricional/MS). "
    "Indicador de estado nutricional (peso-para-idade ou IMC-para-idade Z < -2). "
    "Cobre apenas crianças acompanhadas na Atenção Básica/CadÚnico — não é censo: "
    "municípios com maior cobertura de vigilância nutricional podem registrar taxas "
    "aparentemente maiores. Interprete junto à taxa de cobertura do município. "
    "Fome oculta (micronutrientes) não é captada diretamente — este indicador é o proxy "
    "disponível com cobertura municipal. Lag típico: ~6–12 meses (ALIM-02, dupla face §17)."
)


@dataclass(frozen=True)
class FomeOculta:
    """Contrato do produto Fome Oculta por município/ano."""

    codigo_ibge: str
    nome: str
    uf: str | None
    populacao: int | None
    ano: int | None
    n_acompanhadas: int | None
    baixo_peso_pct: float | None
    nivel: NivelFomeOculta


def classificar_nivel(baixo_peso_pct: float | None) -> NivelFomeOculta:
    """Classifica o nível de fome oculta dado o % de baixo peso."""
    if baixo_peso_pct is None:
        return "sem_dado"
    if baixo_peso_pct >= _LIMIAR_CRITICO:
        return "crítico"
    if baixo_peso_pct >= _LIMIAR_ELEVADO:
        return "elevado"
    if baixo_peso_pct >= _LIMIAR_MODERADO:
        return "moderado"
    return "baixo"


def calcular(
    codigo_ibge: str,
    nome: str,
    uf: str | None,
    populacao: int | None,
    *,
    ano: int | None,
    n_acompanhadas: int | None,
    baixo_peso_pct: float | None,
) -> FomeOculta:
    """Monta o produto Fome Oculta a partir dos valores do banco."""
    pct = round(baixo_peso_pct, 2) if baixo_peso_pct is not None else None
    return FomeOculta(
        codigo_ibge=codigo_ibge,
        nome=nome,
        uf=uf,
        populacao=populacao,
        ano=ano,
        n_acompanhadas=n_acompanhadas,
        baixo_peso_pct=pct,
        nivel=classificar_nivel(pct),
    )
