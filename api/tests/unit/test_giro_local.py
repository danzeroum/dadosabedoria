"""Unidade do contrato do Giro Local (TRAB-03): per capita + níveis. Puro, sem DB.

Usa números do seed (SP/Campinas) para manter consistência entre unitário e integração.
"""

from __future__ import annotations

import pytest

from app.produtos.giro_local import (
    calcular,
    classificar_nivel_credito,
    classificar_nivel_emprego,
)

# Seed: SP 11451245 hab, Campinas 1213792 hab
SP_POP = 11_451_245
CPS_POP = 1_213_792

# Seed CAGED (último mês = 2026-04)
SP_SALDO_CAGED = -9_100
CPS_SALDO_CAGED = -300

# Seed ESTBAN (último mês = 2026-04): R$ 99 bi (SP), R$ 199 bi (Campinas)
SP_SALDO_ESTBAN = 99_000_000_000
CPS_SALDO_ESTBAN = 199_000_000_000


def test_nivel_emprego_positivo_e_criando() -> None:
    assert classificar_nivel_emprego(2.5) == "criando"
    assert classificar_nivel_emprego(0.1) == "criando"


def test_nivel_emprego_negativo_e_reduzindo() -> None:
    assert classificar_nivel_emprego(-1.0) == "reduzindo"
    assert classificar_nivel_emprego(-0.01) == "reduzindo"


def test_nivel_emprego_zero_e_estavel() -> None:
    assert classificar_nivel_emprego(0.0) == "estavel"


def test_nivel_emprego_sem_dado() -> None:
    assert classificar_nivel_emprego(None) == "sem_dado"


def test_nivel_credito_alto() -> None:
    assert classificar_nivel_credito(10_000.0) == "alto"
    assert classificar_nivel_credito(50_000.0) == "alto"


def test_nivel_credito_medio() -> None:
    assert classificar_nivel_credito(5_000.0) == "medio"
    assert classificar_nivel_credito(1_000.0) == "medio"


def test_nivel_credito_baixo() -> None:
    assert classificar_nivel_credito(999.0) == "baixo"
    assert classificar_nivel_credito(0.0) == "baixo"


def test_nivel_credito_sem_dado() -> None:
    assert classificar_nivel_credito(None) == "sem_dado"


def test_calcular_sp_abril_2026() -> None:
    """SP em abril: emprego negativo (reduzindo), crédito médio (~R$ 8.6k/hab)."""
    g = calcular(
        "3550308",
        "São Paulo",
        "SP",
        SP_POP,
        periodo_emprego="2026-04",
        saldo_emprego=SP_SALDO_CAGED,
        periodo_credito="2026-04",
        saldo_credito=SP_SALDO_ESTBAN,
    )
    assert g.codigo_ibge == "3550308"
    assert g.nome == "São Paulo"
    assert g.uf == "SP"
    assert g.populacao == SP_POP

    # Emprego: -9100 / 11451245 × 1000 ≈ -0.79 → reduzindo
    assert g.saldo_emprego == SP_SALDO_CAGED
    assert g.saldo_emprego_per_1000 is not None
    assert g.saldo_emprego_per_1000 < 0
    assert g.nivel_emprego == "reduzindo"

    # Crédito: 99e9 / 11451245 ≈ 8645 → médio (entre 1000 e 10000)
    assert g.saldo_credito == SP_SALDO_ESTBAN
    assert g.saldo_credito_per_hab is not None
    assert 1_000 <= g.saldo_credito_per_hab < 10_000
    assert g.nivel_credito == "medio"


def test_calcular_campinas_abril_2026() -> None:
    """Campinas em abril: emprego negativo, crédito alto (~R$ 163k/hab — seed inflado)."""
    g = calcular(
        "3509502",
        "Campinas",
        "SP",
        CPS_POP,
        periodo_emprego="2026-04",
        saldo_emprego=CPS_SALDO_CAGED,
        periodo_credito="2026-04",
        saldo_credito=CPS_SALDO_ESTBAN,
    )
    assert g.nivel_emprego == "reduzindo"
    # 199e9 / 1213792 ≈ 163944 → alto
    assert g.nivel_credito == "alto"
    assert g.saldo_credito_per_hab is not None
    assert g.saldo_credito_per_hab >= 10_000


def test_calcular_sem_credito_degrada() -> None:
    """Sem dado de crédito → nivel_credito=sem_dado, emprego ainda calcula."""
    g = calcular(
        "3550308",
        "São Paulo",
        "SP",
        SP_POP,
        periodo_emprego="2026-04",
        saldo_emprego=5000,
        periodo_credito=None,
        saldo_credito=None,
    )
    assert g.nivel_emprego == "criando"
    assert g.nivel_credito == "sem_dado"
    assert g.saldo_credito is None
    assert g.saldo_credito_per_hab is None


def test_calcular_sem_populacao_degrada_sem_per_capita() -> None:
    """Sem populacao → per_1000 e per_hab ficam None, mas níveis ainda calculam via absoluto."""
    g = calcular(
        "9999999",
        "Município Teste",
        None,
        None,
        periodo_emprego="2026-04",
        saldo_emprego=1000,
        periodo_credito="2026-04",
        saldo_credito=5_000_000,
    )
    assert g.populacao is None
    assert g.saldo_emprego_per_1000 is None
    assert g.saldo_credito_per_hab is None
    # nível de emprego por sinal absoluto: 1000 > 0 → criando
    assert g.nivel_emprego == "criando"
    # sem per capita → sem_dado para crédito
    assert g.nivel_credito == "sem_dado"


def test_calcular_sem_nenhum_dado_nao_ocorre_na_rota() -> None:
    """A rota garante que ao menos um componente existe antes de chamar calcular()."""
    g = calcular(
        "9999999",
        "Vazio",
        None,
        None,
        periodo_emprego=None,
        saldo_emprego=None,
        periodo_credito=None,
        saldo_credito=None,
    )
    assert g.nivel_emprego == "sem_dado"
    assert g.nivel_credito == "sem_dado"


def test_arredondamento_per_1000() -> None:
    g = calcular(
        "3550308",
        "SP",
        "SP",
        1_000_000,
        periodo_emprego="2026-04",
        saldo_emprego=1234,
        periodo_credito=None,
        saldo_credito=None,
    )
    assert g.saldo_emprego_per_1000 == pytest.approx(1.23, abs=0.01)
