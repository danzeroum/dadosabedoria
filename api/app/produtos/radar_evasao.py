"""Radar de Evasão Escolar (EDU-02) — cobertura de matrículas do ensino fundamental.

Pergunta do produto: **quantas crianças em idade escolar estão fora do ensino fundamental?**

Usa o indicador ``educacao.matriculas.fundamental`` (INEP/Censo Escolar) e a população municipal
(IBGE) para estimar a taxa de cobertura: matrículas / (população × 0,14) × 100. A fração 0,14
(14%) é um proxy da população em idade escolar fundamental (6–14 anos) baseado no Censo 2022.
Lógica **pura** — sem rede/DB.

HONESTIDADE:
- O denominador é uma estimativa: a proporção real de crianças 6–14 varia por município.
- Taxa > 100 % é esperada (alunos de outros municípios matriculados aqui); classifica como
  "adequada", não como erro — o município é polo de atração escolar.
- Só matrículas do ensino fundamental (INEP/Censo Escolar); não cobre EJA, creche, pré-escola.
- Lag: INEP é anual (publicação ~1 ano após o censo escolar).
- Ausência de dado INEP não significa ausência de alunos.
- Dupla face (§17): agregado por município — nunca identifica alunos individualmente.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

#: Nível de cobertura de matrículas no ensino fundamental vs. população estimada em idade escolar.
NivelEvasao = Literal["adequada", "atencao", "alerta", "sem_dado"]

# Fração da população estimada em idade escolar fundamental (6–14 anos) — Censo 2022.
_FRACAO_ESCOLAR = 0.14

# Limiares provisórios (%). Calibrar com distribuição real nacional.
# Referência: meta do Plano Nacional de Educação é cobertura universal (100 %).
_LIMIAR_ADEQUADA = 90.0  # ≥ 90 % → cobertura adequada
_LIMIAR_ATENCAO = 75.0  # 75–89 % → atenção

NOTA_HONESTA = (
    "Matrículas do ensino fundamental (Censo Escolar/INEP) divididas por uma estimativa da "
    "população em idade escolar (14 % da população municipal, proxy do Censo 2022). "
    "Taxa > 100 % é esperada: o município pode receber alunos de cidades vizinhas — classifica-se "
    "como 'adequada', não como erro. Cobre apenas matrículas do fundamental (EF); não inclui EJA, "
    "creche nem pré-escola. Lag: INEP é anual, publicado ~1 ano após o censo escolar. "
    "Limiares provisórios — a calibrar com a distribuição nacional. "
    "Agregado por município, sem identificação de alunos (dupla face §17, EDU-02)."
)


@dataclass(frozen=True)
class RadarEvasao:
    """Contrato: cobertura do ensino fundamental por município."""

    codigo_ibge: str
    nome: str
    uf: str | None
    populacao: int | None

    periodo: str | None  # YYYY do Censo Escolar mais recente com dado
    matriculas: int | None  # total de matrículas no ensino fundamental
    matriculas_por_mil: float | None  # matrículas / populacao × 1.000
    populacao_escolar_estimada: int | None  # populacao × 0,14 (arredondado)
    taxa_cobertura: float | None  # (matriculas / populacao_escolar_estimada) × 100
    nivel: NivelEvasao


def classificar_nivel_evasao(taxa: float | None) -> NivelEvasao:
    """Classifica a cobertura de matrículas no ensino fundamental."""
    if taxa is None:
        return "sem_dado"
    if taxa >= _LIMIAR_ADEQUADA:
        return "adequada"
    if taxa >= _LIMIAR_ATENCAO:
        return "atencao"
    return "alerta"


def calcular(
    codigo_ibge: str,
    nome: str,
    uf: str | None,
    populacao: int | None,
    *,
    periodo: str | None,
    matriculas: int | None,
) -> RadarEvasao:
    """Monta o RadarEvasao a partir dos dados disponíveis; degrada com dado parcial."""
    pop_escolar: int | None = None
    por_mil: float | None = None
    taxa: float | None = None

    if populacao and populacao > 0:
        pop_escolar = round(populacao * _FRACAO_ESCOLAR)
        if matriculas is not None:
            por_mil = round(matriculas / populacao * 1000, 1)
            if pop_escolar > 0:
                taxa = round(matriculas / pop_escolar * 100, 1)

    return RadarEvasao(
        codigo_ibge=codigo_ibge,
        nome=nome,
        uf=uf,
        populacao=populacao,
        periodo=periodo,
        matriculas=matriculas,
        matriculas_por_mil=por_mil,
        populacao_escolar_estimada=pop_escolar,
        taxa_cobertura=taxa,
        nivel=classificar_nivel_evasao(taxa),
    )
