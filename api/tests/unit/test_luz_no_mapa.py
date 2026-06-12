"""Testes da lógica pura do produto LuzNoMapa (SANE-04): classificação e cálculo."""

from __future__ import annotations

import pytest

from app.produtos.luz_no_mapa import (
    NivelEnergia,
    calcular,
    classificar_dec,
    classificar_fec,
)


@pytest.mark.parametrize(
    ("dec", "esperado"),
    [
        (0.0, "confiavel"),
        (8.0, "confiavel"),  # exato no limiar
        (8.01, "regular"),
        (20.0, "regular"),  # exato no limiar
        (20.01, "fragil"),
        (30.0, "fragil"),
        (None, "sem_dado"),
    ],
)
def test_classificar_dec(dec: float | None, esperado: NivelEnergia) -> None:
    assert classificar_dec(dec) == esperado


@pytest.mark.parametrize(
    ("fec", "esperado"),
    [
        (0.0, "confiavel"),
        (6.0, "confiavel"),  # exato no limiar
        (6.01, "regular"),
        (15.0, "regular"),  # exato no limiar
        (15.01, "fragil"),
        (25.0, "fragil"),
        (None, "sem_dado"),
    ],
)
def test_classificar_fec(fec: float | None, esperado: NivelEnergia) -> None:
    assert classificar_fec(fec) == esperado


def test_calcular_com_dados_completos() -> None:
    lnm = calcular(
        "3550308",
        "São Paulo",
        "SP",
        periodo="2023",
        dec=3.52,
        fec=4.21,
    )
    assert lnm.codigo_ibge == "3550308"
    assert lnm.nome == "São Paulo"
    assert lnm.uf == "SP"
    assert lnm.periodo == "2023"
    assert lnm.dec == pytest.approx(3.52)
    assert lnm.fec == pytest.approx(4.21)
    assert lnm.nivel_dec == "confiavel"
    assert lnm.nivel_fec == "confiavel"


def test_calcular_sem_fec_degrada_graciosamente() -> None:
    lnm = calcular("1501402", "Belém", "PA", periodo="2023", dec=25.4, fec=None)
    assert lnm.nivel_dec == "fragil"
    assert lnm.nivel_fec == "sem_dado"
    assert lnm.fec is None


def test_calcular_sem_dec_degrada_graciosamente() -> None:
    lnm = calcular("3509502", "Campinas", "SP", periodo=None, dec=None, fec=None)
    assert lnm.nivel_dec == "sem_dado"
    assert lnm.nivel_fec == "sem_dado"
    assert lnm.periodo is None


def test_calcular_nivel_regular() -> None:
    lnm = calcular("3304557", "Rio de Janeiro", "RJ", periodo="2023", dec=9.8, fec=8.15)
    assert lnm.nivel_dec == "regular"
    assert lnm.nivel_fec == "regular"
