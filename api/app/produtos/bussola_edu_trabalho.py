"""Bússola Educação-Trabalho (EDU-01) — base educacional e emprego formal por município.

Pergunta do produto: **como está a base educacional e o mercado de trabalho formal no município?**
Combina matrículas do ensino fundamental (INEP/Censo Escolar, anual) com o saldo de emprego
formal e o salário médio das admissões (Novo CAGED, mensal). Lógica **pura** — sem rede/DB.

HONESTIDADE:
- Matrículas do fundamental: alunos em escolas municipais, estaduais e privadas no ano de
  referência — cobertura do ensino **formal**, não da escolarização em sentido amplo.
- Emprego formal (CAGEDMOV): admissões − desligamentos com carteira assinada; não capta trabalho
  informal (~40% da força de trabalho) nem autônomo.
- A relação entre educação e emprego é de **CONTEXTO**, não causal: mais matrículas não causa mais
  empregos formais — serve para enquadrar o município, não para estabelecer causalidade.
- Lag: INEP é anual (publicação ~1 ano após o censo); CAGED é mensal (~30–40 dias).
- Usa apenas CAGEDMOV; CAGEDFOR (ajustes retroativos) não está incorporado — refinamento futuro.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from app.produtos.giro_local import NivelEmprego
from app.produtos.salario_radar import NivelSalario, classificar_nivel_salario

#: Nível de cobertura de matrículas no ensino fundamental por 1.000 habitantes.
NivelEducacao = Literal["alto", "medio", "baixo", "sem_dado"]

# Limiares provisórios (matrículas/1.000 hab). Calibrar com distribuição real nacional na Onda 2.
# Referência: ~14% da população está em idade escolar fundamental (6–14 anos); cobertura ≈100%.
_LIMIAR_ALTO = 120  # ≥120/1.000 → cobertura forte
_LIMIAR_MEDIO = 70  # 70–119/1.000 → cobertura moderada

NOTA_HONESTA = (
    "Matrículas do ensino fundamental (Censo Escolar/INEP): alunos em escolas municipais, "
    "estaduais e privadas no ano de referência — cobertura do ensino formal, não da escolarização "
    "total. Saldo de emprego formal (CAGEDMOV/MTE): admissões menos desligamentos com carteira "
    "assinada; não capta trabalho informal (~40% da força de trabalho) nem autônomo. A relação "
    "entre educação e emprego é de CONTEXTO, não causal: mais matrículas não causa mais empregos "
    "formais. Lag: INEP é anual (publicação ~1 ano após o censo); CAGED é mensal (~30–40 dias). "
    "Usa apenas CAGEDMOV; CAGEDFOR (ajustes retroativos) não está incorporado — refinamento futuro."
)


@dataclass(frozen=True)
class BussolaEduTrab:
    """Contrato: base educacional (INEP) + mercado de trabalho formal (CAGED) por município."""

    codigo_ibge: str
    nome: str
    uf: str | None
    populacao: int | None

    # Educação (INEP — anual)
    periodo_educacao: str | None  # YYYY
    matriculas: int | None  # matrículas no ensino fundamental
    matriculas_por_mil: float | None  # matrículas / populacao × 1.000
    nivel_educacao: NivelEducacao

    # Emprego formal (CAGED — mensal)
    periodo_emprego: str | None  # YYYY-MM do último dado disponível
    saldo_emprego: int | None  # admissões − desligamentos
    nivel_emprego: NivelEmprego

    # Salário médio das admissões (CAGED — mensal)
    salario_medio: float | None  # R$ médio declarado nas admissões
    nivel_salario: NivelSalario


def classificar_nivel_educacao(matriculas_por_mil: float | None) -> NivelEducacao:
    """Cobertura de matrículas no fundamental por 1.000 hab vs. limiares provisórios."""
    if matriculas_por_mil is None:
        return "sem_dado"
    if matriculas_por_mil >= _LIMIAR_ALTO:
        return "alto"
    if matriculas_por_mil >= _LIMIAR_MEDIO:
        return "medio"
    return "baixo"


def calcular(
    codigo_ibge: str,
    nome: str,
    uf: str | None,
    populacao: int | None,
    *,
    periodo_educacao: str | None,
    matriculas: int | None,
    periodo_emprego: str | None,
    saldo_emprego: int | None,
    salario_medio: float | None,
) -> BussolaEduTrab:
    """Monta a Bússola a partir dos dados disponíveis; degrada graciosamente com dado parcial."""
    por_mil: float | None
    if matriculas is not None and populacao and populacao > 0:
        por_mil = matriculas / populacao * 1000
    else:
        por_mil = None

    if saldo_emprego is None:
        nivel_emp: NivelEmprego = "sem_dado"
    elif saldo_emprego > 0:
        nivel_emp = "criando"
    elif saldo_emprego < 0:
        nivel_emp = "reduzindo"
    else:
        nivel_emp = "estavel"

    return BussolaEduTrab(
        codigo_ibge=codigo_ibge,
        nome=nome,
        uf=uf,
        populacao=populacao,
        periodo_educacao=periodo_educacao,
        matriculas=matriculas,
        matriculas_por_mil=round(por_mil, 1) if por_mil is not None else None,
        nivel_educacao=classificar_nivel_educacao(por_mil),
        periodo_emprego=periodo_emprego,
        saldo_emprego=saldo_emprego,
        nivel_emprego=nivel_emp,
        salario_medio=round(salario_medio, 2) if salario_medio is not None else None,
        nivel_salario=classificar_nivel_salario(salario_medio),
    )
