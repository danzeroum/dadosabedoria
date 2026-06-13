"""Testes unitários do produto AMB-01 EcoVivo."""

from __future__ import annotations

import pytest

from app.produtos.eco_vivo import (
    NOTA_HONESTA,
    calcular,
    classificar_nivel,
)

# ------------------------------------------------------------------ classificar_nivel


def test_classificar_nivel_expressivo() -> None:
    assert classificar_nivel(30.0) == "expressivo"
    assert classificar_nivel(100.0) == "expressivo"


def test_classificar_nivel_expressivo_limiar() -> None:
    assert classificar_nivel(30.0) == "expressivo"


def test_classificar_nivel_moderado() -> None:
    assert classificar_nivel(5.0) == "moderado"
    assert classificar_nivel(15.0) == "moderado"
    assert classificar_nivel(29.99) == "moderado"


def test_classificar_nivel_incipiente() -> None:
    assert classificar_nivel(0.0) == "incipiente"
    assert classificar_nivel(2.5) == "incipiente"
    assert classificar_nivel(4.99) == "incipiente"


def test_classificar_nivel_sem_dado() -> None:
    assert classificar_nivel(None) == "sem_dado"


# ------------------------------------------------------------------ calcular


def test_calcular_municipio_expressivo() -> None:
    # R$ 3M / 50k hab = R$ 60/hab → expressivo
    ev = calcular(
        "3550308",
        "São Paulo",
        "SP",
        50_000,
        ano=2024,
        valor_liquidado=3_000_000.0,
    )
    assert ev.codigo_ibge == "3550308"
    assert ev.nome == "São Paulo"
    assert ev.uf == "SP"
    assert ev.populacao == 50_000
    assert ev.ano == 2024
    assert ev.valor_liquidado == pytest.approx(3_000_000.0)
    assert ev.valor_por_hab == pytest.approx(60.0)
    assert ev.nivel == "expressivo"


def test_calcular_municipio_moderado() -> None:
    # R$ 350k / 50k hab = R$ 7/hab → moderado
    ev = calcular(
        "5000002",
        "Municipio Moderado",
        "MS",
        50_000,
        ano=2024,
        valor_liquidado=350_000.0,
    )
    assert ev.nivel == "moderado"
    assert ev.valor_por_hab == pytest.approx(7.0)


def test_calcular_municipio_incipiente() -> None:
    # R$ 100k / 50k hab = R$ 2/hab → incipiente
    ev = calcular(
        "5000001",
        "Municipio Incipiente",
        "MS",
        50_000,
        ano=2024,
        valor_liquidado=100_000.0,
    )
    assert ev.nivel == "incipiente"
    assert ev.valor_por_hab == pytest.approx(2.0)


def test_calcular_zero_liquidado_nivel_incipiente() -> None:
    ev = calcular("3550308", "SP", "SP", 1_000_000, ano=2024, valor_liquidado=0.0)
    assert ev.valor_por_hab == pytest.approx(0.0)
    assert ev.nivel == "incipiente"


def test_calcular_sem_populacao_retorna_none_por_hab() -> None:
    ev = calcular("3550308", "SP", "SP", None, ano=2024, valor_liquidado=1_000_000.0)
    assert ev.valor_por_hab is None
    assert ev.nivel == "sem_dado"


def test_calcular_populacao_zero_retorna_none_por_hab() -> None:
    ev = calcular("3550308", "SP", "SP", 0, ano=2024, valor_liquidado=1_000_000.0)
    assert ev.valor_por_hab is None
    assert ev.nivel == "sem_dado"


# ------------------------------------------------------------------ nota honesta


def test_nota_honesta_presente() -> None:
    assert "função 18" in NOTA_HONESTA
    assert "Gestão Ambiental" in NOTA_HONESTA
    assert "IBAMA" in NOTA_HONESTA
    assert "dupla face" in NOTA_HONESTA
