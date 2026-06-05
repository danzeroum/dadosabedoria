"""Unidade do adaptador ESTBAN (parse/prata/agregação) — puro, sem rede/DB."""

from __future__ import annotations

import polars as pl
import pytest

from app.ingestao.adaptadores.estban import AdaptadorEstban
from tests.fixtures.caged import FetcherFake
from tests.fixtures.estban import AMOSTRA_ESTBAN


def _adaptador() -> AdaptadorEstban:
    return AdaptadorEstban(FetcherFake(AMOSTRA_ESTBAN))


def test_parse_le_colunas() -> None:
    df = _adaptador().parse(AMOSTRA_ESTBAN)
    assert "CODMUN" in df.columns
    assert df.height == 3


def test_prata_normaliza_valor_brasileiro() -> None:
    a = _adaptador()
    df = a.transformar_prata(a.parse(AMOSTRA_ESTBAN))
    assert set(df.columns) == {"codmun", "credito"}
    por_linha = sorted(df["credito"].to_list())
    assert por_linha == [123.0, 500000.5, 1000000.0]


def test_agregar_credito_em_reais() -> None:
    a = _adaptador()
    saldos = a.agregar_credito(a.transformar_prata(a.parse(AMOSTRA_ESTBAN)))
    por_municipio = {r["codmun"]: r["saldo"] for r in saldos.iter_rows(named=True)}
    assert por_municipio["3304557"] == 1_500_000_500.0  # (1.000.000 + 500.000,50) × 1000
    assert por_municipio["9999999"] == 123_000.0


def test_coluna_credito_ausente_erra() -> None:
    df = pl.DataFrame({"CODMUN": ["3304557"], "OUTRA": ["1"]})
    with pytest.raises(ValueError, match="verbete 160"):
        _adaptador().transformar_prata(df)
