"""Testes unitários do produto SANE-05 SaneFundo."""

from __future__ import annotations

import pytest

from app.produtos.sane_fundo import (
    NOTA_HONESTA,
    calcular,
    classificar_nivel,
)

# ------------------------------------------------------------------ classificar_nivel


def test_classificar_nivel_expressivo() -> None:
    assert classificar_nivel(60.0) == "expressivo"
    assert classificar_nivel(200.0) == "expressivo"


def test_classificar_nivel_expressivo_limiar() -> None:
    assert classificar_nivel(60.0) == "expressivo"


def test_classificar_nivel_moderado() -> None:
    assert classificar_nivel(15.0) == "moderado"
    assert classificar_nivel(40.0) == "moderado"
    assert classificar_nivel(59.99) == "moderado"


def test_classificar_nivel_incipiente() -> None:
    assert classificar_nivel(0.0) == "incipiente"
    assert classificar_nivel(7.0) == "incipiente"
    assert classificar_nivel(14.99) == "incipiente"


def test_classificar_nivel_sem_dado() -> None:
    assert classificar_nivel(None) == "sem_dado"


# ------------------------------------------------------------------ calcular


def test_calcular_municipio_expressivo() -> None:
    # R$ 6M / 50k hab = R$ 120/hab → expressivo
    sf = calcular(
        "3550308",
        "São Paulo",
        "SP",
        50_000,
        ano=2024,
        valor_liquidado=6_000_000.0,
    )
    assert sf.codigo_ibge == "3550308"
    assert sf.nome == "São Paulo"
    assert sf.uf == "SP"
    assert sf.populacao == 50_000
    assert sf.ano == 2024
    assert sf.valor_liquidado == pytest.approx(6_000_000.0)
    assert sf.valor_por_hab == pytest.approx(120.0)
    assert sf.nivel == "expressivo"


def test_calcular_municipio_moderado() -> None:
    # R$ 1M / 40k hab = R$ 25/hab → moderado
    sf = calcular(
        "5000002",
        "Municipio Moderado",
        "MS",
        40_000,
        ano=2024,
        valor_liquidado=1_000_000.0,
    )
    assert sf.nivel == "moderado"
    assert sf.valor_por_hab == pytest.approx(25.0)


def test_calcular_municipio_incipiente() -> None:
    # R$ 200k / 50k hab = R$ 4/hab → incipiente
    sf = calcular(
        "5000001",
        "Municipio Incipiente",
        "MS",
        50_000,
        ano=2024,
        valor_liquidado=200_000.0,
    )
    assert sf.nivel == "incipiente"
    assert sf.valor_por_hab == pytest.approx(4.0)


def test_calcular_zero_liquidado_nivel_incipiente() -> None:
    sf = calcular("3550308", "SP", "SP", 1_000_000, ano=2024, valor_liquidado=0.0)
    assert sf.valor_por_hab == pytest.approx(0.0)
    assert sf.nivel == "incipiente"


def test_calcular_sem_populacao_retorna_none_por_hab() -> None:
    sf = calcular("3550308", "SP", "SP", None, ano=2024, valor_liquidado=1_000_000.0)
    assert sf.valor_por_hab is None
    assert sf.nivel == "sem_dado"


def test_calcular_populacao_zero_retorna_none_por_hab() -> None:
    sf = calcular("3550308", "SP", "SP", 0, ano=2024, valor_liquidado=1_000_000.0)
    assert sf.valor_por_hab is None
    assert sf.nivel == "sem_dado"


# ------------------------------------------------------------------ nota honesta


def test_nota_honesta_presente() -> None:
    assert "função 17" in NOTA_HONESTA
    assert "Saneamento" in NOTA_HONESTA
    assert "SABESP" in NOTA_HONESTA
    assert "dupla face" in NOTA_HONESTA
