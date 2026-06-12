"""RioEmRisco (SANE-02) — risco hídrico de seca por município (ANA Monitor de Secas).

Pergunta do produto: **qual o risco de escassez hídrica no município?**

Usa o indicador ``saneamento.agua.seca_indice`` (float 0–5) derivado da classificação do
Monitor de Secas da ANA: Normal=0, D0=1, D1=2, D2=3, D3=4, D4=5.
O valor anual representa o pior mês do exercício.

Classificação de risco:
- ``normal``   : 0 ≤ índice < 1 (Normal — sem seca registrada)
- ``atencao``  : 1 ≤ índice < 3 (D0 Anorm. Seco ou D1 Seco Moderado)
- ``critico``  : índice ≥ 3     (D2 Seco Grave, D3 Extremo, D4 Excepcional)
- ``sem_dado`` : sem dado disponível

HONESTIDADE:
- O Monitor de Secas da ANA cobre principalmente o Semiárido e Centro-Oeste; municípios do
  Sul/Sudeste úmidos podem aparecer sem dado ou como Normal.
- O índice representa o pior mês do ano — não a condição atual.
- Dado mensal consolidado anualmente; lag típico de 1–2 meses em relação à referência.
- Dupla face (§17): vulnerabilidade estrutural — não culpa dos moradores; seca é fenômeno
  climático e hidrológico, não resultado de gestão municipal isolada. (SANE-02)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

NivelSeca = Literal["normal", "atencao", "critico", "sem_dado"]

_LIMIAR_ATENCAO = 1.0  # D0: Anormalmente Seco
_LIMIAR_CRITICO = 3.0  # D2: Seco Grave

NOTA_HONESTA = (
    "Índice de seca pelo Monitor de Secas da ANA (Agência Nacional de Águas), baseado na "
    "metodologia USDM adaptada. Classes Normal, D0–D4 convertidas em índice 0–5; "
    "valor anual = pior mês do exercício. "
    "Cobertura maior no Semiárido e Centro-Oeste — municípios úmidos podem aparecer sem dado. "
    "Risco estrutural de escassez hídrica — não culpa dos moradores. "
    "Forma a confirmar na 1ª busca real (SANE-02, dupla face §17)."
)


@dataclass(frozen=True)
class RioEmRisco:
    """Contrato: risco hídrico de seca por município."""

    codigo_ibge: str
    nome: str
    uf: str | None

    periodo: str | None  # YYYY do exercício
    seca_indice: float | None  # 0–5 (pior mês do ano)
    nivel: NivelSeca


def classificar_nivel(indice: float | None) -> NivelSeca:
    """Classifica o risco de seca a partir do índice numérico (0–5)."""
    if indice is None:
        return "sem_dado"
    if indice >= _LIMIAR_CRITICO:
        return "critico"
    if indice >= _LIMIAR_ATENCAO:
        return "atencao"
    return "normal"


def calcular(
    codigo_ibge: str,
    nome: str,
    uf: str | None,
    *,
    periodo: str | None,
    seca_indice: float | None,
) -> RioEmRisco:
    """Monta o RioEmRisco a partir dos dados disponíveis; degrada graciosamente."""
    return RioEmRisco(
        codigo_ibge=codigo_ibge,
        nome=nome,
        uf=uf,
        periodo=periodo,
        seca_indice=seca_indice,
        nivel=classificar_nivel(seca_indice),
    )
