"""Unidade do ObraViva — contratações públicas via PNCP (TRANSP-05). Puro, sem rede/DB."""

from __future__ import annotations

import pytest

from app.produtos.obra_viva import ObraViva, calcular, classificar_nivel_contratos

# ---------- classificar_nivel_contratos ----------


def test_classificar_elevado() -> None:
    assert classificar_nivel_contratos(3_000.0) == "elevado"
    assert classificar_nivel_contratos(10_000.0) == "elevado"


def test_classificar_moderado() -> None:
    assert classificar_nivel_contratos(500.0) == "moderado"
    assert classificar_nivel_contratos(2_999.9) == "moderado"


def test_classificar_baixo() -> None:
    assert classificar_nivel_contratos(0.0) == "baixo"
    assert classificar_nivel_contratos(499.9) == "baixo"


def test_classificar_sem_dado() -> None:
    assert classificar_nivel_contratos(None) == "sem_dado"


# ---------- calcular ----------


def _obra(
    *,
    populacao: int | None = 100_000,
    valor_contratos: int | None = 200_000_000,
    periodo: str | None = "2024",
) -> ObraViva:
    return calcular(
        "3550308",
        "São Paulo",
        "SP",
        populacao,
        periodo=periodo,
        valor_contratos=valor_contratos,
    )


def test_calcular_por_hab() -> None:
    o = _obra(populacao=100_000, valor_contratos=300_000_000)
    # 300M / 100k = R$ 3.000/hab → elevado
    assert o.valor_por_hab == pytest.approx(3_000.0)
    assert o.nivel == "elevado"


def test_calcular_moderado() -> None:
    o = _obra(populacao=100_000, valor_contratos=100_000_000)
    # 100M / 100k = R$ 1.000/hab → moderado
    assert o.valor_por_hab == pytest.approx(1_000.0)
    assert o.nivel == "moderado"


def test_calcular_baixo() -> None:
    o = _obra(populacao=100_000, valor_contratos=20_000_000)
    # 20M / 100k = R$ 200/hab → baixo
    assert o.valor_por_hab == pytest.approx(200.0)
    assert o.nivel == "baixo"


def test_calcular_sem_valor() -> None:
    o = _obra(valor_contratos=None)
    assert o.valor_contratos is None
    assert o.valor_por_hab is None
    assert o.nivel == "sem_dado"


def test_calcular_sem_populacao() -> None:
    o = _obra(populacao=None)
    assert o.valor_por_hab is None
    assert o.nivel == "sem_dado"


def test_calcular_sem_periodo() -> None:
    o = _obra(periodo=None)
    assert o.periodo is None
    # R$200M/100k hab = R$2000/hab → moderado; período não afeta o cálculo
    assert o.nivel == "moderado"


def test_calcular_preserva_campos_territorio() -> None:
    o = calcular("3550308", "São Paulo", "SP", 12_300_000, periodo="2024", valor_contratos=None)
    assert o.codigo_ibge == "3550308"
    assert o.nome == "São Paulo"
    assert o.uf == "SP"
    assert o.populacao == 12_300_000


def test_calcular_populacao_zero_sem_por_hab() -> None:
    o = _obra(populacao=0)
    assert o.valor_por_hab is None
    assert o.nivel == "sem_dado"
