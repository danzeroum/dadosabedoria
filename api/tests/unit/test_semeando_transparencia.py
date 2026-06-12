"""Testes unitários do produto SemeandoTransparência (ALIM-05)."""

from __future__ import annotations

import pytest

from app.produtos.semeando_transparencia import (
    _LIMIAR_ALTO,
    _LIMIAR_MODERADO,
    calcular,
    classificar_nivel,
)


def test_classificar_alto_exato() -> None:
    assert classificar_nivel(_LIMIAR_ALTO) == "alto"


def test_classificar_alto_acima() -> None:
    assert classificar_nivel(500.0) == "alto"


def test_classificar_moderado_exato() -> None:
    assert classificar_nivel(_LIMIAR_MODERADO) == "moderado"


def test_classificar_moderado_acima_do_limiar() -> None:
    assert classificar_nivel(99.99) == "moderado"


def test_classificar_baixo() -> None:
    assert classificar_nivel(5.0) == "baixo"


def test_classificar_baixo_zero() -> None:
    assert classificar_nivel(0.0) == "baixo"


def test_classificar_sem_dado_none() -> None:
    assert classificar_nivel(None) == "sem_dado"


def test_calcular_municipio_agricola() -> None:
    # 5_000_000 BRL / 50_000 hab = 100 BRL/hab → alto
    st = calcular("1234567", "Sorriso", "MT", 50_000, ano=2023, valor_liquidado=5_000_000.0)
    assert st.nivel == "alto"
    assert st.valor_por_hab is not None
    assert abs(st.valor_por_hab - 100.0) < 0.01


def test_calcular_municipio_moderado() -> None:
    # 1_000_000 BRL / 100_000 hab = 10 BRL/hab → moderado
    st = calcular("1234567", "Cidade Média", "PR", 100_000, ano=2023, valor_liquidado=1_000_000.0)
    assert st.nivel == "moderado"


def test_calcular_municipio_urbano_zero() -> None:
    st = calcular("3550308", "São Paulo", "SP", 11_451_245, ano=2023, valor_liquidado=0.0)
    assert st.nivel == "baixo"
    assert st.valor_por_hab == 0.0


def test_calcular_sem_populacao() -> None:
    st = calcular("3509502", "Campinas", "SP", None, ano=2023, valor_liquidado=1_000_000.0)
    assert st.valor_por_hab is None
    assert st.nivel == "sem_dado"


def test_calcular_populacao_zero() -> None:
    st = calcular("3509502", "Campinas", "SP", 0, ano=2023, valor_liquidado=1_000_000.0)
    assert st.valor_por_hab is None
    assert st.nivel == "sem_dado"


def test_calcular_sem_valor_liquidado() -> None:
    st = calcular("3550308", "São Paulo", "SP", 11_451_245, ano=None, valor_liquidado=None)
    assert st.valor_liquidado is None
    assert st.valor_por_hab is None
    assert st.nivel == "sem_dado"


def test_calcular_preserva_ano() -> None:
    st = calcular("3550308", "São Paulo", "SP", 1, ano=2022, valor_liquidado=100.0)
    assert st.ano == 2022


def test_calcular_sem_uf() -> None:
    st = calcular("9999999", "Município", None, 10_000, ano=2023, valor_liquidado=2_000_000.0)
    assert st.uf is None
    assert st.nivel == "alto"


def test_calcular_arredondamento() -> None:
    st = calcular("1234567", "Mun", "SP", 3, ano=2023, valor_liquidado=100.0)
    assert st.valor_por_hab == pytest.approx(33.33, abs=0.01)
