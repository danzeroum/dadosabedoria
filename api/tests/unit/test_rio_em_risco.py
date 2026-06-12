"""Testes da lógica pura do produto RioEmRisco (SANE-02): classificação e cálculo."""

from __future__ import annotations

import pytest

from app.produtos.rio_em_risco import (
    NivelSeca,
    calcular,
    classificar_nivel,
)


@pytest.mark.parametrize(
    ("indice", "esperado"),
    [
        (0.0, "normal"),  # Normal
        (0.9, "normal"),  # abaixo do limiar D0
        (1.0, "atencao"),  # exato no limiar D0
        (1.5, "atencao"),  # D0.5 hipotético
        (2.0, "atencao"),  # D1
        (2.9, "atencao"),  # abaixo do limiar D2
        (3.0, "critico"),  # exato no limiar D2
        (4.0, "critico"),  # D3
        (5.0, "critico"),  # D4 máximo
        (None, "sem_dado"),
    ],
)
def test_classificar_nivel(indice: float | None, esperado: NivelSeca) -> None:
    assert classificar_nivel(indice) == esperado


def test_calcular_normal() -> None:
    r = calcular("1501402", "Belém", "PA", periodo="2023", seca_indice=0.0)
    assert r.codigo_ibge == "1501402"
    assert r.nome == "Belém"
    assert r.uf == "PA"
    assert r.periodo == "2023"
    assert r.seca_indice == pytest.approx(0.0)
    assert r.nivel == "normal"


def test_calcular_atencao() -> None:
    r = calcular("3550308", "São Paulo", "SP", periodo="2023", seca_indice=2.0)
    assert r.nivel == "atencao"
    assert r.seca_indice == pytest.approx(2.0)


def test_calcular_critico() -> None:
    r = calcular("2304400", "Fortaleza", "CE", periodo="2023", seca_indice=4.0)
    assert r.nivel == "critico"


def test_calcular_sem_dado_degrada_graciosamente() -> None:
    r = calcular("9999999", "Sem Dado", None, periodo=None, seca_indice=None)
    assert r.nivel == "sem_dado"
    assert r.seca_indice is None
    assert r.periodo is None
    assert r.uf is None
