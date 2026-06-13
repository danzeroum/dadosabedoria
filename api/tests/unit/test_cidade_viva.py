"""Testes unitários do produto URB-01 CidadeViva."""

from __future__ import annotations

import pytest

from app.produtos.cidade_viva import (
    NOTA_HONESTA,
    calcular,
    classificar_nivel,
)

# ------------------------------------------------------------------ classificar_nivel


def test_classificar_nivel_expressivo() -> None:
    assert classificar_nivel(200.0) == "expressivo"
    assert classificar_nivel(500.0) == "expressivo"


def test_classificar_nivel_expressivo_limiar() -> None:
    assert classificar_nivel(200.0) == "expressivo"


def test_classificar_nivel_moderado() -> None:
    assert classificar_nivel(80.0) == "moderado"
    assert classificar_nivel(120.0) == "moderado"
    assert classificar_nivel(199.99) == "moderado"


def test_classificar_nivel_incipiente() -> None:
    assert classificar_nivel(0.0) == "incipiente"
    assert classificar_nivel(40.0) == "incipiente"
    assert classificar_nivel(79.99) == "incipiente"


def test_classificar_nivel_sem_dado() -> None:
    assert classificar_nivel(None) == "sem_dado"


# ------------------------------------------------------------------ calcular


def test_calcular_municipio_expressivo() -> None:
    # R$ 24M / 120k hab = R$ 200/hab → expressivo
    cv = calcular(
        "3509502",
        "Campinas",
        "SP",
        120_000,
        ano=2024,
        valor_liquidado=24_000_000.0,
    )
    assert cv.codigo_ibge == "3509502"
    assert cv.nome == "Campinas"
    assert cv.uf == "SP"
    assert cv.populacao == 120_000
    assert cv.ano == 2024
    assert cv.valor_liquidado == pytest.approx(24_000_000.0)
    assert cv.valor_por_hab == pytest.approx(200.0)
    assert cv.nivel == "expressivo"


def test_calcular_municipio_moderado() -> None:
    # R$ 9.6M / 120k hab = R$ 80/hab → moderado
    cv = calcular(
        "5000002",
        "Municipio Moderado",
        "MS",
        120_000,
        ano=2024,
        valor_liquidado=9_600_000.0,
    )
    assert cv.nivel == "moderado"
    assert cv.valor_por_hab == pytest.approx(80.0)


def test_calcular_municipio_incipiente() -> None:
    # R$ 4.8M / 120k hab = R$ 40/hab → incipiente
    cv = calcular(
        "5000001",
        "Municipio Incipiente",
        "MS",
        120_000,
        ano=2024,
        valor_liquidado=4_800_000.0,
    )
    assert cv.nivel == "incipiente"
    assert cv.valor_por_hab == pytest.approx(40.0)


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
    assert "função 15" in NOTA_HONESTA
    assert "Urbanismo" in NOTA_HONESTA
    assert "pavimentação" in NOTA_HONESTA
    assert "dupla face" in NOTA_HONESTA
