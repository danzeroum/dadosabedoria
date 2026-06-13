"""Testes unitários do produto HAB-02 CasaViva."""

from __future__ import annotations

import pytest

from app.produtos.casa_viva import (
    NOTA_HONESTA,
    calcular,
    classificar_nivel,
)

# ------------------------------------------------------------------ classificar_nivel


def test_classificar_nivel_expressivo() -> None:
    assert classificar_nivel(50.0) == "expressivo"
    assert classificar_nivel(200.0) == "expressivo"


def test_classificar_nivel_expressivo_limiar() -> None:
    assert classificar_nivel(50.0) == "expressivo"


def test_classificar_nivel_moderado() -> None:
    assert classificar_nivel(10.0) == "moderado"
    assert classificar_nivel(30.0) == "moderado"
    assert classificar_nivel(49.99) == "moderado"


def test_classificar_nivel_incipiente() -> None:
    assert classificar_nivel(0.0) == "incipiente"
    assert classificar_nivel(5.0) == "incipiente"
    assert classificar_nivel(9.99) == "incipiente"


def test_classificar_nivel_sem_dado() -> None:
    assert classificar_nivel(None) == "sem_dado"


# ------------------------------------------------------------------ calcular


def test_calcular_municipio_expressivo() -> None:
    # R$ 25M / 100k hab = R$ 250/hab → expressivo
    cv = calcular(
        "3550308",
        "São Paulo",
        "SP",
        100_000,
        ano=2024,
        valor_liquidado=25_000_000.0,
    )
    assert cv.codigo_ibge == "3550308"
    assert cv.nome == "São Paulo"
    assert cv.uf == "SP"
    assert cv.populacao == 100_000
    assert cv.ano == 2024
    assert cv.valor_liquidado == pytest.approx(25_000_000.0)
    assert cv.valor_por_hab == pytest.approx(250.0)
    assert cv.nivel == "expressivo"


def test_calcular_municipio_moderado() -> None:
    # R$ 600k / 40k hab = R$ 15/hab → moderado
    cv = calcular(
        "5000002",
        "Municipio Moderado",
        "MS",
        40_000,
        ano=2024,
        valor_liquidado=600_000.0,
    )
    assert cv.nivel == "moderado"
    assert cv.valor_por_hab == pytest.approx(15.0)


def test_calcular_municipio_incipiente() -> None:
    # R$ 200k / 50k hab = R$ 4/hab → incipiente
    cv = calcular(
        "5000001",
        "Municipio Incipiente",
        "MS",
        50_000,
        ano=2024,
        valor_liquidado=200_000.0,
    )
    assert cv.nivel == "incipiente"
    assert cv.valor_por_hab == pytest.approx(4.0)


def test_calcular_zero_liquidado_nivel_incipiente() -> None:
    cv = calcular("3550308", "SP", "SP", 1_000_000, ano=2024, valor_liquidado=0.0)
    assert cv.valor_por_hab == pytest.approx(0.0)
    assert cv.nivel == "incipiente"


def test_calcular_sem_populacao_retorna_none_por_hab() -> None:
    cv = calcular("3550308", "SP", "SP", None, ano=2024, valor_liquidado=1_000_000.0)
    assert cv.valor_por_hab is None
    assert cv.nivel == "sem_dado"


def test_calcular_populacao_zero_retorna_none_por_hab() -> None:
    cv = calcular("3550308", "SP", "SP", 0, ano=2024, valor_liquidado=1_000_000.0)
    assert cv.valor_por_hab is None
    assert cv.nivel == "sem_dado"


# ------------------------------------------------------------------ nota honesta


def test_nota_honesta_presente() -> None:
    assert "função 16" in NOTA_HONESTA
    assert "Habitação" in NOTA_HONESTA
    assert "MCMV" in NOTA_HONESTA
    assert "dupla face" in NOTA_HONESTA
