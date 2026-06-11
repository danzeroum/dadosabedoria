"""Unidade do adaptador CAGED (parse/prata/agregação) e da agenda — puros, sem rede/DB."""

from __future__ import annotations

from datetime import date

from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.caged import AdaptadorCaged
from app.ingestao.agenda import competencia_alvo
from tests.fixtures.caged import AMOSTRA_UNIT, FetcherFake


def _adaptador() -> AdaptadorCaged:
    return AdaptadorCaged(FetcherFake(AMOSTRA_UNIT))


def test_parse_le_colunas() -> None:
    df = _adaptador().parse(AMOSTRA_UNIT)
    assert "município" in df.columns
    assert df.height == 8


def test_prata_normaliza_e_filtra() -> None:
    a = _adaptador()
    df = a.transformar_prata(a.parse(AMOSTRA_UNIT))
    assert set(df.columns) == {"competencia", "municipio", "saldo_mov", "salario_brl"}
    assert df.height == 8


def test_agregar_saldo() -> None:
    a = _adaptador()
    saldos = a.agregar_saldo(a.transformar_prata(a.parse(AMOSTRA_UNIT)))
    por_municipio = {r["municipio"]: r["saldo"] for r in saldos.iter_rows(named=True)}
    assert por_municipio == {"355030": 2, "350950": -1, "999999": 1}


def test_extrair_usa_fetcher() -> None:
    df = _adaptador().extrair(Janela(2026, 7))
    assert df.height == 8


def test_competencia_alvo() -> None:
    assert competencia_alvo(date(2026, 6, 15)) == "202604"
    assert competencia_alvo(date(2026, 1, 10)) == "202511"  # vira o ano
    assert competencia_alvo(date(2026, 3, 1), defasagem_meses=1) == "202602"
