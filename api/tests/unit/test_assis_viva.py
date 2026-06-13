"""Testes unitários do produto SOCIAL-01 AssisViva."""

from __future__ import annotations

import pytest

from app.produtos.assis_viva import (
    NOTA_HONESTA,
    calcular,
    classificar_nivel,
)

# ------------------------------------------------------------------ classificar_nivel


def test_classificar_nivel_expressivo() -> None:
    assert classificar_nivel(150.0) == "expressivo"
    assert classificar_nivel(300.0) == "expressivo"


def test_classificar_nivel_expressivo_limiar() -> None:
    assert classificar_nivel(150.0) == "expressivo"


def test_classificar_nivel_moderado() -> None:
    assert classificar_nivel(50.0) == "moderado"
    assert classificar_nivel(80.0) == "moderado"
    assert classificar_nivel(149.99) == "moderado"


def test_classificar_nivel_incipiente() -> None:
    assert classificar_nivel(0.0) == "incipiente"
    assert classificar_nivel(25.0) == "incipiente"
    assert classificar_nivel(49.99) == "incipiente"


def test_classificar_nivel_sem_dado() -> None:
    assert classificar_nivel(None) == "sem_dado"


# ------------------------------------------------------------------ calcular


def test_calcular_municipio_expressivo() -> None:
    # R$ 15M / 100k hab = R$ 150/hab → expressivo
    av = calcular(
        "3509502",
        "Campinas",
        "SP",
        100_000,
        ano=2024,
        valor_liquidado=15_000_000.0,
    )
    assert av.codigo_ibge == "3509502"
    assert av.nome == "Campinas"
    assert av.uf == "SP"
    assert av.populacao == 100_000
    assert av.ano == 2024
    assert av.valor_liquidado == pytest.approx(15_000_000.0)
    assert av.valor_por_hab == pytest.approx(150.0)
    assert av.nivel == "expressivo"


def test_calcular_municipio_moderado() -> None:
    # R$ 5M / 100k hab = R$ 50/hab → moderado
    av = calcular(
        "5000002",
        "Municipio Moderado",
        "MS",
        100_000,
        ano=2024,
        valor_liquidado=5_000_000.0,
    )
    assert av.nivel == "moderado"
    assert av.valor_por_hab == pytest.approx(50.0)


def test_calcular_municipio_incipiente() -> None:
    # R$ 2M / 100k hab = R$ 20/hab → incipiente
    av = calcular(
        "5000001",
        "Municipio Incipiente",
        "MS",
        100_000,
        ano=2024,
        valor_liquidado=2_000_000.0,
    )
    assert av.nivel == "incipiente"
    assert av.valor_por_hab == pytest.approx(20.0)


def test_calcular_zero_liquidado_nivel_incipiente() -> None:
    av = calcular("3550308", "SP", "SP", 1_000_000, ano=2024, valor_liquidado=0.0)
    assert av.valor_por_hab == pytest.approx(0.0)
    assert av.nivel == "incipiente"


def test_calcular_sem_populacao_retorna_none_por_hab() -> None:
    av = calcular("3550308", "SP", "SP", None, ano=2024, valor_liquidado=1_000_000.0)
    assert av.valor_por_hab is None
    assert av.nivel == "sem_dado"


def test_calcular_populacao_zero_retorna_none_por_hab() -> None:
    av = calcular("3550308", "SP", "SP", 0, ano=2024, valor_liquidado=1_000_000.0)
    assert av.valor_por_hab is None
    assert av.nivel == "sem_dado"


# ------------------------------------------------------------------ nota honesta


def test_nota_honesta_presente() -> None:
    assert "função 08" in NOTA_HONESTA
    assert "Assistência Social" in NOTA_HONESTA
    assert "Bolsa Família" in NOTA_HONESTA
    assert "dupla face" in NOTA_HONESTA
