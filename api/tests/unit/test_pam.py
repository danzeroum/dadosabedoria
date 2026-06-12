"""Testes unitários do adaptador IBGE PAM (pam.py)."""

from __future__ import annotations

import json

import polars as pl

from app.ingestao.adaptadores.pam import AdaptadorPam
from tests.fixtures.pam import AMOSTRA, FetcherFake


def test_parse_retorna_dataframe_com_colunas_obrigatorias() -> None:
    adaptador = AdaptadorPam(FetcherFake(AMOSTRA))
    bruto, _ = adaptador.baixar_bruto(None)  # type: ignore[arg-type]
    df = adaptador.parse(bruto)
    assert "cod_ibge" in df.columns
    assert "valor_mil_brl" in df.columns
    assert len(df) > 0


def test_parse_retorna_todas_as_series_das_duas_tabelas() -> None:
    adaptador = AdaptadorPam(FetcherFake(AMOSTRA))
    bruto, _ = adaptador.baixar_bruto(None)  # type: ignore[arg-type]
    df = adaptador.parse(bruto)
    # 4 entradas na tabela 1612 + 2 entradas na tabela 1613 = 6
    assert len(df) == 6


def test_transformar_prata_filtra_invalidos() -> None:
    adaptador = AdaptadorPam(FetcherFake(AMOSTRA))
    bruto, _ = adaptador.baixar_bruto(None)  # type: ignore[arg-type]
    df = adaptador.parse(bruto)
    prata = adaptador.transformar_prata(df)
    # 9999999 com "-" deve ser filtrado
    assert "9999999" not in prata["cod_ibge"].to_list()


def test_transformar_prata_converte_mil_brl_para_brl() -> None:
    adaptador = AdaptadorPam(FetcherFake(AMOSTRA))
    bruto, _ = adaptador.baixar_bruto(None)  # type: ignore[arg-type]
    df = adaptador.parse(bruto)
    prata = adaptador.transformar_prata(df)
    # SP tabela 1612: 5000 Mil BRL → 5.000.000 BRL
    sp_rows = prata.filter(pl.col("cod_ibge") == "3550308")
    assert any(abs(v - 5_000_000.0) < 1.0 for v in sp_rows["valor_brl"].to_list())


def test_agregar_soma_tabelas_por_municipio() -> None:
    adaptador = AdaptadorPam(FetcherFake(AMOSTRA))
    bruto, _ = adaptador.baixar_bruto(None)  # type: ignore[arg-type]
    df = adaptador.parse(bruto)
    prata = adaptador.transformar_prata(df)
    agregado = adaptador.agregar(prata)
    # SP: 5000+1000 Mil BRL = 6.000.000 BRL
    sp = agregado.filter(pl.col("cod_ibge") == "3550308")
    assert abs(sp["valor_brl"][0] - 6_000_000.0) < 1.0


def test_agregar_campinas_soma_tabelas() -> None:
    adaptador = AdaptadorPam(FetcherFake(AMOSTRA))
    bruto, _ = adaptador.baixar_bruto(None)  # type: ignore[arg-type]
    df = adaptador.parse(bruto)
    prata = adaptador.transformar_prata(df)
    agregado = adaptador.agregar(prata)
    # Campinas: 8000+2000 Mil BRL = 10.000.000 BRL
    cps = agregado.filter(pl.col("cod_ibge") == "3509502")
    assert abs(cps["valor_brl"][0] - 10_000_000.0) < 1.0


def test_agregar_rio_apenas_tabela_1612() -> None:
    adaptador = AdaptadorPam(FetcherFake(AMOSTRA))
    bruto, _ = adaptador.baixar_bruto(None)  # type: ignore[arg-type]
    df = adaptador.parse(bruto)
    prata = adaptador.transformar_prata(df)
    agregado = adaptador.agregar(prata)
    # Rio: apenas tabela 1612 com 200 Mil BRL = 200.000 BRL
    rio = agregado.filter(pl.col("cod_ibge") == "3304557")
    assert abs(rio["valor_brl"][0] - 200_000.0) < 1.0


def test_extrair_valida_contrato() -> None:
    adaptador = AdaptadorPam(FetcherFake(AMOSTRA))
    from app.ingestao.adaptadores.base import Janela

    df = adaptador.extrair(Janela(2023, 1))
    assert "cod_ibge" in df.columns
    assert "valor_mil_brl" in df.columns


def test_parse_json_vazio_retorna_dataframe_sem_linhas() -> None:
    bruto = json.dumps([]).encode("utf-8")
    adaptador = AdaptadorPam(FetcherFake(bruto))
    df = adaptador.parse(bruto)
    assert len(df) == 0
