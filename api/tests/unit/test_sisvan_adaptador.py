"""Testes unitários do adaptador SISVAN (parse + prata + ouro) — forma API JSON."""

from __future__ import annotations

import pytest

from app.ingestao.adaptadores.sisvan import AdaptadorSisvan
from tests.fixtures.sisvan import AMOSTRA, FetcherFake


@pytest.fixture()
def adaptador() -> AdaptadorSisvan:
    return AdaptadorSisvan(FetcherFake(AMOSTRA))


def test_parse_retorna_dataframe(adaptador: AdaptadorSisvan) -> None:
    df = adaptador.parse(AMOSTRA)
    assert "codigo_municipio" in df.columns
    assert "idade" in df.columns
    assert "crianca_imc_x_idade" in df.columns
    assert df.height > 0


def test_prata_filtra_idade_maior_igual_5(adaptador: AdaptadorSisvan) -> None:
    df = adaptador.parse(AMOSTRA)
    prata = adaptador.transformar_prata(df)
    # Só os 4 municípios de teste (6 díg.) devem sobreviver; idades >= 5 são removidas
    fora = prata.filter(~prata["cod_ibge"].is_in(["355030", "350950", "330455", "510792"]))
    assert fora.height == 0


def test_prata_filtra_ibge_vazio(adaptador: AdaptadorSisvan) -> None:
    df = adaptador.parse(AMOSTRA)
    prata = adaptador.transformar_prata(df)
    assert prata.filter(prata["cod_ibge"] == "").height == 0
    assert None not in prata["cod_ibge"].to_list()


def test_ouro_pct_campinas(adaptador: AdaptadorSisvan) -> None:
    df = adaptador.parse(AMOSTRA)
    ouro = adaptador.agregar(adaptador.transformar_prata(df))
    row = ouro.filter(ouro["cod_ibge"] == "350950").row(0, named=True)
    # Campinas: 1/20 = 5.0%
    assert abs(row["baixo_peso_pct"] - 5.0) < 0.01
    assert row["n_total"] == 20


def test_ouro_pct_sp(adaptador: AdaptadorSisvan) -> None:
    df = adaptador.parse(AMOSTRA)
    ouro = adaptador.agregar(adaptador.transformar_prata(df))
    row = ouro.filter(ouro["cod_ibge"] == "355030").row(0, named=True)
    # SP: 1/50 = 2.0%
    assert abs(row["baixo_peso_pct"] - 2.0) < 0.01
    assert row["n_total"] == 50


def test_ouro_pct_sorriso_critico(adaptador: AdaptadorSisvan) -> None:
    df = adaptador.parse(AMOSTRA)
    ouro = adaptador.agregar(adaptador.transformar_prata(df))
    row = ouro.filter(ouro["cod_ibge"] == "510792").row(0, named=True)
    # Sorriso: 4/10 = 40%
    assert abs(row["baixo_peso_pct"] - 40.0) < 0.01
    assert row["n_total"] == 10


def test_ouro_pct_rio_zero(adaptador: AdaptadorSisvan) -> None:
    df = adaptador.parse(AMOSTRA)
    ouro = adaptador.agregar(adaptador.transformar_prata(df))
    row = ouro.filter(ouro["cod_ibge"] == "330455").row(0, named=True)
    # Rio: 0/5 = 0%
    assert row["baixo_peso_pct"] == pytest.approx(0.0)
    assert row["n_total"] == 5


def test_parse_bytes_invalidos_retorna_vazio(adaptador: AdaptadorSisvan) -> None:
    df = adaptador.parse(b"lixo sem json")
    assert df.height == 0
