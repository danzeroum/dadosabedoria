"""Testes unitários do adaptador SINAN/Dengue (sem rede, sem banco)."""

from __future__ import annotations

import pytest

from app.ingestao.adaptadores.sinan import (
    COL_ANO,
    COL_CLASSI,
    COL_MUNICIPIO,
    CONTRATO,
    AdaptadorSinan,
)
from tests.fixtures.sinan import AMOSTRA, FetcherFake


@pytest.fixture()
def adaptador() -> AdaptadorSinan:
    return AdaptadorSinan(FetcherFake(AMOSTRA))


def test_parse_retorna_tres_colunas(adaptador: AdaptadorSinan) -> None:
    df = adaptador.parse(AMOSTRA)
    assert COL_MUNICIPIO in df.columns
    assert COL_ANO in df.columns
    assert COL_CLASSI in df.columns
    # Não deve ter outras colunas
    assert len(df.columns) == 3


def test_parse_total_linhas(adaptador: AdaptadorSinan) -> None:
    df = adaptador.parse(AMOSTRA)
    # 10 SP + 3 Campinas + 10 Rio + 1 sem município = 24 linhas (excluindo header)
    assert df.height == 24


def test_contrato_valida_colunas_ok(adaptador: AdaptadorSinan) -> None:
    df = adaptador.parse(AMOSTRA)
    # Não deve lançar
    CONTRATO.validar(df)


def test_prata_filtra_descartados(adaptador: AdaptadorSinan) -> None:
    df = adaptador.parse(AMOSTRA)
    prata = adaptador.transformar_prata(df)
    # SP tem 2 descartados (CLASSI_FIN=5) → excluídos
    sp_rows = prata.filter(prata["cod_mun6"] == "355030")
    assert sp_rows.height == 8


def test_prata_filtra_municipio_vazio(adaptador: AdaptadorSinan) -> None:
    df = adaptador.parse(AMOSTRA)
    prata = adaptador.transformar_prata(df)
    # A linha sem município deve ser excluída
    sem_mun = prata.filter(prata["cod_mun6"].is_null() | (prata["cod_mun6"] == ""))
    assert sem_mun.height == 0


def test_prata_campinas_tres_casos(adaptador: AdaptadorSinan) -> None:
    df = adaptador.parse(AMOSTRA)
    prata = adaptador.transformar_prata(df)
    cps = prata.filter(prata["cod_mun6"] == "350950")
    assert cps.height == 3


def test_prata_rio_dez_casos(adaptador: AdaptadorSinan) -> None:
    df = adaptador.parse(AMOSTRA)
    prata = adaptador.transformar_prata(df)
    rio = prata.filter(prata["cod_mun6"] == "330455")
    assert rio.height == 10


def test_agregar_casos_por_municipio(adaptador: AdaptadorSinan) -> None:
    df = adaptador.parse(AMOSTRA)
    prata = adaptador.transformar_prata(df)
    ouro = adaptador.agregar(prata)
    # Devemos ter 3 municípios
    assert ouro.height == 3


def test_agregar_sp_oito_casos(adaptador: AdaptadorSinan) -> None:
    df = adaptador.parse(AMOSTRA)
    prata = adaptador.transformar_prata(df)
    ouro = adaptador.agregar(prata)
    sp = ouro.filter(ouro["cod_mun6"] == "355030")
    assert sp.height == 1
    assert int(sp["casos"][0]) == 8


def test_agregar_rio_dez_casos(adaptador: AdaptadorSinan) -> None:
    df = adaptador.parse(AMOSTRA)
    prata = adaptador.transformar_prata(df)
    ouro = adaptador.agregar(prata)
    rio = ouro.filter(ouro["cod_mun6"] == "330455")
    assert rio.height == 1
    assert int(rio["casos"][0]) == 10


def test_agregar_campinas_tres_casos(adaptador: AdaptadorSinan) -> None:
    """Campinas: 3 casos < n_minimo=5, mas agregar não suprime — supressão ocorre no ouro."""
    df = adaptador.parse(AMOSTRA)
    prata = adaptador.transformar_prata(df)
    ouro = adaptador.agregar(prata)
    cps = ouro.filter(ouro["cod_mun6"] == "350950")
    assert cps.height == 1
    assert int(cps["casos"][0]) == 3
