"""Testes unitários do produto SAUDE-11 Pressão no SUS."""

from __future__ import annotations

import pytest

from app.produtos.pressao_sus import (
    NOTA_HONESTA,
    calcular,
    classificar_nivel,
)

# ------------------------------------------------------------------ classificar_nivel


def test_classificar_nivel_adequado() -> None:
    assert classificar_nivel(500.0) == "adequado"
    assert classificar_nivel(1200.0) == "adequado"


def test_classificar_nivel_adequado_limiar() -> None:
    assert classificar_nivel(500.0) == "adequado"


def test_classificar_nivel_atencao() -> None:
    assert classificar_nivel(200.0) == "atenção"
    assert classificar_nivel(350.0) == "atenção"
    assert classificar_nivel(499.99) == "atenção"


def test_classificar_nivel_critico() -> None:
    assert classificar_nivel(0.0) == "crítico"
    assert classificar_nivel(100.0) == "crítico"
    assert classificar_nivel(199.99) == "crítico"


def test_classificar_nivel_sem_dado() -> None:
    assert classificar_nivel(None) == "sem_dado"


# ------------------------------------------------------------------ calcular


def test_calcular_sp() -> None:
    # SP: SICONFI 2024 ≈ R$ 14 bi / 11.45M hab ≈ R$ 1.200/hab → adequado
    ps = calcular(
        "3550308",
        "São Paulo",
        "SP",
        11_451_245,
        ano=2024,
        valor_liquidado=14_000_000_000.0,
    )
    assert ps.codigo_ibge == "3550308"
    assert ps.nome == "São Paulo"
    assert ps.uf == "SP"
    assert ps.populacao == 11_451_245
    assert ps.ano == 2024
    assert ps.valor_liquidado == pytest.approx(14_000_000_000.0)
    assert ps.valor_por_hab is not None
    assert abs(ps.valor_por_hab - 1222.67) < 1.0
    assert ps.nivel == "adequado"


def test_calcular_municipio_critico() -> None:
    # Município pequeno: R$ 5M / 50k hab = R$ 100/hab → crítico
    ps = calcular(
        "5000001",
        "Municipio Teste",
        "MS",
        50_000,
        ano=2024,
        valor_liquidado=5_000_000.0,
    )
    assert ps.nivel == "crítico"
    assert ps.valor_por_hab == pytest.approx(100.0)


def test_calcular_municipio_atencao() -> None:
    # R$ 12M / 40k hab = R$ 300/hab → atenção
    ps = calcular(
        "5000002",
        "Municipio Atenção",
        "MS",
        40_000,
        ano=2024,
        valor_liquidado=12_000_000.0,
    )
    assert ps.nivel == "atenção"
    assert ps.valor_por_hab == pytest.approx(300.0)


def test_calcular_sem_populacao_retorna_none_por_hab() -> None:
    ps = calcular("3550308", "SP", "SP", None, ano=2024, valor_liquidado=1_000_000.0)
    assert ps.valor_por_hab is None
    assert ps.nivel == "sem_dado"


def test_calcular_populacao_zero_retorna_none_por_hab() -> None:
    ps = calcular("3550308", "SP", "SP", 0, ano=2024, valor_liquidado=1_000_000.0)
    assert ps.valor_por_hab is None
    assert ps.nivel == "sem_dado"


def test_calcular_zero_liquidado_nivel_critico() -> None:
    ps = calcular("3550308", "SP", "SP", 1_000_000, ano=2024, valor_liquidado=0.0)
    assert ps.valor_por_hab == pytest.approx(0.0)
    assert ps.nivel == "crítico"


# ------------------------------------------------------------------ nota honesta


def test_nota_honesta_presente() -> None:
    assert "função 10" in NOTA_HONESTA
    assert "burnout" in NOTA_HONESTA
    assert "Proxy" in NOTA_HONESTA
    assert "CAT/INSS" in NOTA_HONESTA
