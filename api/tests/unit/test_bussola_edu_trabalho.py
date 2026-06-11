"""Unidade do contrato da Bússola Educação-Trabalho (EDU-01). Puro, sem DB.

Valores do seed (SP/Campinas) para consistência com os testes de integração.
"""

from __future__ import annotations

from app.produtos.bussola_edu_trabalho import calcular, classificar_nivel_educacao

POP_SP = 11_451_245
MAT_SP = 980_000  # → ~85.6/1.000 → "medio"

POP_CPS = 1_213_792
MAT_CPS = 150_000  # → ~123.6/1.000 → "alto"


def test_nivel_alto() -> None:
    assert classificar_nivel_educacao(125.0) == "alto"


def test_nivel_medio() -> None:
    assert classificar_nivel_educacao(85.0) == "medio"


def test_nivel_baixo() -> None:
    assert classificar_nivel_educacao(50.0) == "baixo"


def test_nivel_sem_dado() -> None:
    assert classificar_nivel_educacao(None) == "sem_dado"


def test_limiar_exato_alto() -> None:
    assert classificar_nivel_educacao(120.0) == "alto"


def test_limiar_exato_medio() -> None:
    assert classificar_nivel_educacao(70.0) == "medio"


def test_calcular_sp_medio_reduzindo() -> None:
    b = calcular(
        "3550308",
        "São Paulo",
        "SP",
        POP_SP,
        periodo_educacao="2024",
        matriculas=MAT_SP,
        periodo_emprego="2026-04",
        saldo_emprego=-9100,
        salario_medio=2500.0,
    )
    assert b.matriculas_por_mil is not None
    assert 85.0 < b.matriculas_por_mil < 86.0
    assert b.nivel_educacao == "medio"
    assert b.nivel_emprego == "reduzindo"
    assert b.nivel_salario == "medio"
    assert b.saldo_emprego == -9100
    assert b.periodo_educacao == "2024"
    assert b.periodo_emprego == "2026-04"


def test_calcular_campinas_alto_criando() -> None:
    b = calcular(
        "3509502",
        "Campinas",
        "SP",
        POP_CPS,
        periodo_educacao="2024",
        matriculas=MAT_CPS,
        periodo_emprego="2026-04",
        saldo_emprego=300,
        salario_medio=4500.0,
    )
    assert b.nivel_educacao == "alto"  # 123.6/1.000 ≥ 120
    assert b.nivel_emprego == "criando"
    assert b.nivel_salario == "alto"


def test_calcular_sem_populacao_sem_per_capita() -> None:
    b = calcular(
        "0000001",
        "Município Teste",
        None,
        None,
        periodo_educacao="2024",
        matriculas=50_000,
        periodo_emprego=None,
        saldo_emprego=None,
        salario_medio=None,
    )
    assert b.matriculas_por_mil is None  # sem pop → sem per capita
    assert b.nivel_educacao == "sem_dado"
    assert b.nivel_emprego == "sem_dado"
    assert b.nivel_salario == "sem_dado"


def test_calcular_so_educacao() -> None:
    b = calcular(
        "1",
        "Apenas Edu",
        "SP",
        100_000,
        periodo_educacao="2024",
        matriculas=15_000,  # 150/1.000 → alto
        periodo_emprego=None,
        saldo_emprego=None,
        salario_medio=None,
    )
    assert b.nivel_educacao == "alto"
    assert b.nivel_emprego == "sem_dado"
    assert b.nivel_salario == "sem_dado"
    assert b.saldo_emprego is None


def test_calcular_so_emprego() -> None:
    b = calcular(
        "2",
        "Apenas Emprego",
        "SP",
        500_000,
        periodo_educacao=None,
        matriculas=None,
        periodo_emprego="2026-04",
        saldo_emprego=200,
        salario_medio=1800.0,
    )
    assert b.nivel_educacao == "sem_dado"
    assert b.nivel_emprego == "criando"
    assert b.nivel_salario == "baixo"


def test_calcular_emprego_zero_e_estavel() -> None:
    b = calcular(
        "3",
        "Estável",
        None,
        10_000,
        periodo_educacao=None,
        matriculas=None,
        periodo_emprego="2026-03",
        saldo_emprego=0,
        salario_medio=1518.0,
    )
    assert b.nivel_emprego == "estavel"
    assert b.nivel_salario == "baixo"  # < 2000
