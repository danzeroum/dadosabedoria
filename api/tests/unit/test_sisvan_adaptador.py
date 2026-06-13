"""Testes unitários do adaptador SISVAN (parse + prata + ouro)."""

from __future__ import annotations

import pytest

from app.ingestao.adaptadores.sisvan import AdaptadorSisvan
from tests.fixtures.sisvan import AMOSTRA, FetcherFake


@pytest.fixture()
def adaptador() -> AdaptadorSisvan:
    return AdaptadorSisvan(FetcherFake(AMOSTRA))


def test_parse_retorna_dataframe(adaptador: AdaptadorSisvan) -> None:
    df = adaptador.parse(AMOSTRA)
    assert "CO_MUNICIPIO_IBGE" in df.columns
    assert "NU_IDADE_ANO" in df.columns
    assert "CO_ESTADO_NUTRI_CRIANCA" in df.columns
    assert df.height > 0


def test_prata_filtra_idade_maior_igual_5(adaptador: AdaptadorSisvan) -> None:
    df = adaptador.parse(AMOSTRA)
    prata = adaptador.transformar_prata(df)
    # Linhas com idade >= 5 devem ser removidas
    idades_invalidas = prata.filter(
        ~(prata["cod_ibge"].is_in(["3550308", "3509502", "3304557", "5107925"]))
    )
    assert idades_invalidas.height == 0


def test_prata_filtra_ibge_vazio(adaptador: AdaptadorSisvan) -> None:
    df = adaptador.parse(AMOSTRA)
    prata = adaptador.transformar_prata(df)
    assert prata.filter(prata["cod_ibge"] == "").height == 0


def test_ouro_pct_campinas(adaptador: AdaptadorSisvan) -> None:
    df = adaptador.parse(AMOSTRA)
    prata = adaptador.transformar_prata(df)
    ouro = adaptador.agregar(prata)
    row = ouro.filter(ouro["cod_ibge"] == "3509502").row(0, named=True)
    # Campinas: 1/20 = 5.0%
    assert abs(row["baixo_peso_pct"] - 5.0) < 0.01
    assert row["n_total"] == 20


def test_ouro_pct_sp(adaptador: AdaptadorSisvan) -> None:
    df = adaptador.parse(AMOSTRA)
    prata = adaptador.transformar_prata(df)
    ouro = adaptador.agregar(prata)
    row = ouro.filter(ouro["cod_ibge"] == "3550308").row(0, named=True)
    # SP: 1/50 = 2.0%
    assert abs(row["baixo_peso_pct"] - 2.0) < 0.01
    assert row["n_total"] == 50


def test_ouro_pct_sorriso_critico(adaptador: AdaptadorSisvan) -> None:
    df = adaptador.parse(AMOSTRA)
    prata = adaptador.transformar_prata(df)
    ouro = adaptador.agregar(prata)
    row = ouro.filter(ouro["cod_ibge"] == "5107925").row(0, named=True)
    # Sorriso: 4/10 = 40%
    assert abs(row["baixo_peso_pct"] - 40.0) < 0.01
    assert row["n_total"] == 10


def test_ouro_pct_rio_zero(adaptador: AdaptadorSisvan) -> None:
    df = adaptador.parse(AMOSTRA)
    prata = adaptador.transformar_prata(df)
    ouro = adaptador.agregar(prata)
    row = ouro.filter(ouro["cod_ibge"] == "3304557").row(0, named=True)
    # Rio: 0/5 = 0%
    assert row["baixo_peso_pct"] == pytest.approx(0.0)
    assert row["n_total"] == 5


def test_parse_bytes_invalidos_retorna_vazio(adaptador: AdaptadorSisvan) -> None:
    df = adaptador.parse(b"lixo sem colunas")
    assert df.height == 0 or "CO_MUNICIPIO_IBGE" not in df.columns or df.height == 0
