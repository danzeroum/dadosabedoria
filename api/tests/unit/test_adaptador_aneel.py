"""Testes do adaptador ANEEL DEC/FEC (sem rede — usa FetcherFake)."""

from __future__ import annotations

from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.energia import AdaptadorAneel
from tests.fixtures.energia import AMOSTRA, FetcherFake


def _adaptador() -> AdaptadorAneel:
    return AdaptadorAneel(FetcherFake(AMOSTRA))


def test_parse_retorna_dataframe_com_colunas_esperadas() -> None:
    ad = _adaptador()
    bruto, _ = ad.baixar_bruto(Janela(2023, 1))
    df = ad.parse(bruto)
    assert "cod_ibge" in df.columns
    assert "dec" in df.columns
    assert "fec" in df.columns


def test_transformar_prata_converte_float_e_filtra_nulos() -> None:
    ad = _adaptador()
    bruto, _ = ad.baixar_bruto(Janela(2023, 1))
    df = ad.parse(bruto)
    prata = ad.transformar_prata(df)
    # cod_ibge inválido (9999999) ainda está na fixture com dec válido → mantido
    assert len(prata) >= 6
    # colunas devem ser float64
    import polars as pl

    assert prata["dec"].dtype == pl.Float64


def test_agregar_consolida_por_municipio() -> None:
    ad = _adaptador()
    bruto, _ = ad.baixar_bruto(Janela(2023, 1))
    df = ad.parse(bruto)
    prata = ad.transformar_prata(df)
    agregado = ad.agregar(prata)
    # Não deve ter duplicatas de cod_ibge
    assert agregado["cod_ibge"].n_unique() == len(agregado)


def test_extrair_valida_contrato() -> None:
    ad = _adaptador()
    df = ad.extrair(Janela(2023, 1))
    # Contrato requer cod_ibge e dec — deve passar com a fixture
    assert "cod_ibge" in df.columns
    assert "dec" in df.columns


def test_agregar_municipios_conhecidos_tem_valores_corretos() -> None:
    ad = _adaptador()
    bruto, _ = ad.baixar_bruto(Janela(2023, 1))
    df = ad.parse(bruto)
    prata = ad.transformar_prata(df)
    agregado = ad.agregar(prata)
    sp = agregado.filter(agregado["cod_ibge"] == "3550308")
    assert len(sp) == 1
    assert abs(float(sp["dec"][0]) - 3.52) < 0.01
