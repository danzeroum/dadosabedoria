"""Testes unitários do produto FomeOculta (ALIM-02)."""

from __future__ import annotations

import pytest

from app.produtos.fome_oculta import (
    _LIMIAR_CRITICO,
    _LIMIAR_ELEVADO,
    _LIMIAR_MODERADO,
    calcular,
    classificar_nivel,
)


def test_classificar_critico_exato() -> None:
    assert classificar_nivel(_LIMIAR_CRITICO) == "crítico"


def test_classificar_critico_acima() -> None:
    assert classificar_nivel(50.0) == "crítico"


def test_classificar_elevado_exato() -> None:
    assert classificar_nivel(_LIMIAR_ELEVADO) == "elevado"


def test_classificar_elevado_abaixo_critico() -> None:
    assert classificar_nivel(9.99) == "elevado"


def test_classificar_moderado_exato() -> None:
    assert classificar_nivel(_LIMIAR_MODERADO) == "moderado"


def test_classificar_moderado_abaixo_elevado() -> None:
    assert classificar_nivel(4.99) == "elevado"


def test_classificar_baixo() -> None:
    assert classificar_nivel(1.0) == "baixo"


def test_classificar_baixo_zero() -> None:
    assert classificar_nivel(0.0) == "baixo"


def test_classificar_sem_dado_none() -> None:
    assert classificar_nivel(None) == "sem_dado"


def test_calcular_critico() -> None:
    fo = calcular(
        "5107925", "Sorriso", "MT", 90000, ano=2023, n_acompanhadas=100, baixo_peso_pct=40.0
    )
    assert fo.nivel == "crítico"
    assert fo.baixo_peso_pct == pytest.approx(40.0)


def test_calcular_elevado() -> None:
    fo = calcular(
        "3509502", "Campinas", "SP", 1200000, ano=2023, n_acompanhadas=20, baixo_peso_pct=5.0
    )
    assert fo.nivel == "elevado"


def test_calcular_moderado() -> None:
    fo = calcular(
        "3550308", "São Paulo", "SP", 11451245, ano=2023, n_acompanhadas=50, baixo_peso_pct=2.0
    )
    assert fo.nivel == "moderado"


def test_calcular_baixo() -> None:
    fo = calcular(
        "3304557", "Rio de Janeiro", "RJ", 6747815, ano=2023, n_acompanhadas=5, baixo_peso_pct=0.0
    )
    assert fo.nivel == "baixo"
    assert fo.baixo_peso_pct == 0.0


def test_calcular_sem_dado() -> None:
    fo = calcular(
        "9999999", "Município", None, None, ano=None, n_acompanhadas=None, baixo_peso_pct=None
    )
    assert fo.nivel == "sem_dado"
    assert fo.baixo_peso_pct is None


def test_calcular_preserva_campos() -> None:
    fo = calcular("1234567", "Mun", "GO", 50000, ano=2022, n_acompanhadas=30, baixo_peso_pct=3.5)
    assert fo.codigo_ibge == "1234567"
    assert fo.nome == "Mun"
    assert fo.uf == "GO"
    assert fo.populacao == 50000
    assert fo.ano == 2022
    assert fo.n_acompanhadas == 30


def test_calcular_sem_uf() -> None:
    fo = calcular(
        "9999999", "Município", None, 10000, ano=2023, n_acompanhadas=10, baixo_peso_pct=6.0
    )
    assert fo.uf is None
    assert fo.nivel == "elevado"


def test_calcular_arredondamento() -> None:
    fo = calcular("1234567", "Mun", "SP", 1, ano=2023, n_acompanhadas=3, baixo_peso_pct=5.555)
    assert fo.baixo_peso_pct == pytest.approx(5.56, abs=0.01)
