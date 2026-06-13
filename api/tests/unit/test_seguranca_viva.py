"""Testes unitários do produto SEG-01 SegurançaViva."""

from __future__ import annotations

import pytest

from app.produtos.seguranca_viva import (
    NOTA_HONESTA,
    calcular,
    classificar_nivel,
)

# ------------------------------------------------------------------ classificar_nivel


def test_classificar_nivel_expressivo() -> None:
    assert classificar_nivel(100.0) == "expressivo"
    assert classificar_nivel(300.0) == "expressivo"


def test_classificar_nivel_expressivo_limiar() -> None:
    assert classificar_nivel(100.0) == "expressivo"


def test_classificar_nivel_moderado() -> None:
    assert classificar_nivel(30.0) == "moderado"
    assert classificar_nivel(60.0) == "moderado"
    assert classificar_nivel(99.99) == "moderado"


def test_classificar_nivel_incipiente() -> None:
    assert classificar_nivel(0.0) == "incipiente"
    assert classificar_nivel(15.0) == "incipiente"
    assert classificar_nivel(29.99) == "incipiente"


def test_classificar_nivel_sem_dado() -> None:
    assert classificar_nivel(None) == "sem_dado"


# ------------------------------------------------------------------ calcular


def test_calcular_municipio_expressivo() -> None:
    # R$ 12M / 120k hab = R$ 100/hab → expressivo
    sv = calcular(
        "3509502",
        "Campinas",
        "SP",
        120_000,
        ano=2024,
        valor_liquidado=12_000_000.0,
    )
    assert sv.codigo_ibge == "3509502"
    assert sv.nome == "Campinas"
    assert sv.uf == "SP"
    assert sv.populacao == 120_000
    assert sv.ano == 2024
    assert sv.valor_liquidado == pytest.approx(12_000_000.0)
    assert sv.valor_por_hab == pytest.approx(100.0)
    assert sv.nivel == "expressivo"


def test_calcular_municipio_moderado() -> None:
    # R$ 3.6M / 120k hab = R$ 30/hab → moderado
    sv = calcular(
        "5000002",
        "Municipio Moderado",
        "MS",
        120_000,
        ano=2024,
        valor_liquidado=3_600_000.0,
    )
    assert sv.nivel == "moderado"
    assert sv.valor_por_hab == pytest.approx(30.0)


def test_calcular_municipio_incipiente() -> None:
    # R$ 1.2M / 120k hab = R$ 10/hab → incipiente
    sv = calcular(
        "5000001",
        "Municipio Incipiente",
        "MS",
        120_000,
        ano=2024,
        valor_liquidado=1_200_000.0,
    )
    assert sv.nivel == "incipiente"
    assert sv.valor_por_hab == pytest.approx(10.0)


def test_calcular_zero_liquidado_nivel_incipiente() -> None:
    sv = calcular("3550308", "SP", "SP", 1_000_000, ano=2024, valor_liquidado=0.0)
    assert sv.valor_por_hab == pytest.approx(0.0)
    assert sv.nivel == "incipiente"


def test_calcular_sem_populacao_retorna_none_por_hab() -> None:
    sv = calcular("3550308", "SP", "SP", None, ano=2024, valor_liquidado=1_000_000.0)
    assert sv.valor_por_hab is None
    assert sv.nivel == "sem_dado"


def test_calcular_populacao_zero_retorna_none_por_hab() -> None:
    sv = calcular("3550308", "SP", "SP", 0, ano=2024, valor_liquidado=1_000_000.0)
    assert sv.valor_por_hab is None
    assert sv.nivel == "sem_dado"


# ------------------------------------------------------------------ nota honesta


def test_nota_honesta_presente() -> None:
    assert "função 06" in NOTA_HONESTA
    assert "Segurança Pública" in NOTA_HONESTA
    assert "GCM" in NOTA_HONESTA
    assert "dupla face" in NOTA_HONESTA
