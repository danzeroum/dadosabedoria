"""Testes unitários do produto MOB-01 ViaViva."""

from __future__ import annotations

import pytest

from app.produtos.via_viva import (
    NOTA_HONESTA,
    calcular,
    classificar_nivel,
)

# ------------------------------------------------------------------ classificar_nivel


def test_classificar_nivel_elevado() -> None:
    assert classificar_nivel(300.0) == "elevado"
    assert classificar_nivel(1000.0) == "elevado"


def test_classificar_nivel_elevado_limiar() -> None:
    assert classificar_nivel(300.0) == "elevado"


def test_classificar_nivel_moderado() -> None:
    assert classificar_nivel(80.0) == "moderado"
    assert classificar_nivel(150.0) == "moderado"
    assert classificar_nivel(299.99) == "moderado"


def test_classificar_nivel_baixo() -> None:
    assert classificar_nivel(0.0) == "baixo"
    assert classificar_nivel(50.0) == "baixo"
    assert classificar_nivel(79.99) == "baixo"


def test_classificar_nivel_sem_dado() -> None:
    assert classificar_nivel(None) == "sem_dado"


# ------------------------------------------------------------------ calcular


def test_calcular_municipio_elevado() -> None:
    # R$ 30M / 50k hab = R$ 600/hab → elevado
    vv = calcular(
        "3550308",
        "São Paulo",
        "SP",
        50_000,
        ano=2024,
        valor_liquidado=30_000_000.0,
    )
    assert vv.codigo_ibge == "3550308"
    assert vv.nome == "São Paulo"
    assert vv.uf == "SP"
    assert vv.populacao == 50_000
    assert vv.ano == 2024
    assert vv.valor_liquidado == pytest.approx(30_000_000.0)
    assert vv.valor_por_hab == pytest.approx(600.0)
    assert vv.nivel == "elevado"


def test_calcular_municipio_moderado() -> None:
    # R$ 4M / 40k hab = R$ 100/hab → moderado
    vv = calcular(
        "5000002",
        "Municipio Moderado",
        "MS",
        40_000,
        ano=2024,
        valor_liquidado=4_000_000.0,
    )
    assert vv.nivel == "moderado"
    assert vv.valor_por_hab == pytest.approx(100.0)


def test_calcular_municipio_baixo() -> None:
    # R$ 2M / 50k hab = R$ 40/hab → baixo
    vv = calcular(
        "5000001",
        "Municipio Baixo",
        "MS",
        50_000,
        ano=2024,
        valor_liquidado=2_000_000.0,
    )
    assert vv.nivel == "baixo"
    assert vv.valor_por_hab == pytest.approx(40.0)


def test_calcular_zero_liquidado_nivel_baixo() -> None:
    vv = calcular("3550308", "SP", "SP", 1_000_000, ano=2024, valor_liquidado=0.0)
    assert vv.valor_por_hab == pytest.approx(0.0)
    assert vv.nivel == "baixo"


def test_calcular_sem_populacao_retorna_none_por_hab() -> None:
    vv = calcular("3550308", "SP", "SP", None, ano=2024, valor_liquidado=1_000_000.0)
    assert vv.valor_por_hab is None
    assert vv.nivel == "sem_dado"


def test_calcular_populacao_zero_retorna_none_por_hab() -> None:
    vv = calcular("3550308", "SP", "SP", 0, ano=2024, valor_liquidado=1_000_000.0)
    assert vv.valor_por_hab is None
    assert vv.nivel == "sem_dado"


# ------------------------------------------------------------------ nota honesta


def test_nota_honesta_presente() -> None:
    assert "função 26" in NOTA_HONESTA
    assert "Transporte" in NOTA_HONESTA
    assert "rodovias" in NOTA_HONESTA
    assert "dupla face" in NOTA_HONESTA
