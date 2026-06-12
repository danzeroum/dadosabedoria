"""Testes unitários do produto PratoFrio (ALIM-01)."""

from __future__ import annotations

from app.produtos.prato_frio import (
    _LIMIAR_ALTA,
    _LIMIAR_MODERADA,
    calcular,
    classificar_nivel,
)


def test_classificar_alta_exato() -> None:
    assert classificar_nivel(_LIMIAR_ALTA) == "alta"


def test_classificar_alta_acima() -> None:
    assert classificar_nivel(10_000.0) == "alta"


def test_classificar_moderada_exato() -> None:
    assert classificar_nivel(_LIMIAR_MODERADA) == "moderada"


def test_classificar_moderada_acima_do_limiar() -> None:
    assert classificar_nivel(4_999.99) == "moderada"


def test_classificar_baixa() -> None:
    assert classificar_nivel(100.0) == "baixa"


def test_classificar_baixa_zero() -> None:
    assert classificar_nivel(0.0) == "baixa"


def test_classificar_sem_dado_none() -> None:
    assert classificar_nivel(None) == "sem_dado"


def test_calcular_com_populacao() -> None:
    pf = calcular("3550308", "São Paulo", "SP", 11_451_245, periodo="2023", valor_total=6_000_000.0)
    assert pf.codigo_ibge == "3550308"
    assert pf.valor_total == 6_000_000.0
    assert pf.valor_por_hab is not None
    assert abs(pf.valor_por_hab - 0.52) < 0.01
    assert pf.nivel == "baixa"


def test_calcular_campinas_com_populacao() -> None:
    pf = calcular("3509502", "Campinas", "SP", 1_213_792, periodo="2023", valor_total=10_000_000.0)
    assert pf.valor_por_hab is not None
    assert abs(pf.valor_por_hab - 8.24) < 0.1
    assert pf.nivel == "baixa"


def test_calcular_sem_populacao() -> None:
    pf = calcular("3509502", "Campinas", "SP", None, periodo="2023", valor_total=10_000_000.0)
    assert pf.valor_por_hab is None
    assert pf.nivel == "sem_dado"


def test_calcular_populacao_zero() -> None:
    pf = calcular("3509502", "Campinas", "SP", 0, periodo="2023", valor_total=10_000_000.0)
    assert pf.valor_por_hab is None
    assert pf.nivel == "sem_dado"


def test_calcular_sem_valor() -> None:
    pf = calcular("3550308", "São Paulo", "SP", 11_451_245, periodo=None, valor_total=None)
    assert pf.valor_total is None
    assert pf.valor_por_hab is None
    assert pf.nivel == "sem_dado"


def test_calcular_nivel_alta() -> None:
    pf = calcular(
        "1234567", "Município Agrícola", "MT", 50_000, periodo="2023", valor_total=500_000_000.0
    )
    # 500_000_000 / 50_000 = 10_000 BRL/hab → alta
    assert pf.nivel == "alta"


def test_calcular_nivel_moderada() -> None:
    pf = calcular(
        "1234567", "Município Médio", "PR", 100_000, periodo="2023", valor_total=100_000_000.0
    )
    # 100_000_000 / 100_000 = 1_000 BRL/hab → moderada
    assert pf.nivel == "moderada"


def test_calcular_preserva_periodo() -> None:
    pf = calcular("3550308", "São Paulo", "SP", 1, periodo="2022", valor_total=1000.0)
    assert pf.periodo == "2022"


def test_calcular_sem_uf() -> None:
    pf = calcular(
        "9999999", "Território Indígena", None, 1000, periodo="2023", valor_total=5_000_000.0
    )
    assert pf.uf is None
    assert pf.nivel == "alta"
