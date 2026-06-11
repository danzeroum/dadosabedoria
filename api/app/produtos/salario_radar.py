"""Salário Radar (TRAB-02) — nível salarial das novas contratações formais por município/mês.

Pergunta do produto: **como está o salário de quem foi contratado formalmente no município?**

Usa o salário médio declarado nas admissões do Novo CAGED (saldomovimentação=1) para revelar
o patamar salarial da demanda por trabalho formal local. Valores mais altos indicam mais vagas
técnicas e qualificadas; mais baixos, predominância de vagas de salário mínimo.

HONESTIDADE:
- Cobre apenas o emprego **formal** (CAGED): não capta salários informais (~40% da força).
- É o salário **declarado na admissão**, não o salário real pago ao longo do contrato.
- O salário mínimo federal de referência (jan/2026) é R$ 1.518,00.
- Lag típico do CAGED: ~40 dias após a competência.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

#: Nível salarial das admissões formais do município no período.
NivelSalario = Literal["alto", "medio", "baixo", "sem_dado"]

# Referências de classificação (R$ brutos declarados na admissão).
# alto  ≥ R$ 4.000 → ≥ 2,6× salário mínimo jan/2026 (R$ 1.518) — vagas qualificadas
# medio ≥ R$ 2.000 → ≈ 1,3× salário mínimo — faixa intermediária
# baixo <  R$ 2.000 → próximo ou abaixo do salário mínimo
_SALARIO_ALTO = 4_000.0
_SALARIO_MEDIO = 2_000.0

NOTA_HONESTA = (
    "Salário Radar mostra a média salarial das novas contratações formais (Novo CAGED, "
    "saldomovimentação=1) no mês. Representa a demanda local por trabalho formal — não o "
    "salário médio da população em geral nem dos empregados em estoque. Cobre apenas empregos "
    "com carteira assinada; não capta salários informais (~40% da força de trabalho). "
    "Referência: salário mínimo federal jan/2026 = R$ 1.518,00."
)


@dataclass(frozen=True)
class SalarioRadar:
    """Contrato do Salário Radar: nível salarial das novas contratações formais."""

    codigo_ibge: str
    nome: str
    uf: str | None
    periodo: str | None  # YYYY-MM do último dado disponível
    salario_medio: float | None  # média R$ das admissões do período (None se sem dado)
    nivel: NivelSalario


def classificar_nivel_salario(salario: float | None) -> NivelSalario:
    """Nível salarial: R$ brutos médios das admissões vs. referências nacionais."""
    if salario is None:
        return "sem_dado"
    if salario >= _SALARIO_ALTO:
        return "alto"
    if salario >= _SALARIO_MEDIO:
        return "medio"
    return "baixo"


def calcular(
    codigo_ibge: str,
    nome: str,
    uf: str | None,
    *,
    periodo: str | None,
    salario_medio: float | None,
) -> SalarioRadar:
    """Monta o Salário Radar a partir dos dados disponíveis."""
    nivel = classificar_nivel_salario(salario_medio)
    return SalarioRadar(
        codigo_ibge=codigo_ibge,
        nome=nome,
        uf=uf,
        periodo=periodo,
        salario_medio=round(salario_medio, 2) if salario_medio is not None else None,
        nivel=nivel,
    )
