"""Unidade do adaptador DATASUS/SIH (parse/prata/agregação + contrato) — puro, sem rede/DB."""

from __future__ import annotations

from datetime import date

import polars as pl
import pytest

from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.datasus import CONTRATO, AdaptadorDatasus
from app.ingestao.contratos import ContratoVioladoError
from tests.fixtures.datasus import AMOSTRA, FetcherFake


def _ad() -> AdaptadorDatasus:
    return AdaptadorDatasus(FetcherFake(AMOSTRA))


def test_parse_le_tabular() -> None:
    df = _ad().parse(AMOSTRA)
    assert "DIAG_PRINC" in df.columns
    assert "MUNIC_RES" in df.columns
    assert "DT_INTER" in df.columns
    assert df.height == 6


def test_prata_filtra_grupo_j_e_extrai_mes() -> None:
    a = _ad()
    df = a.transformar_prata(a.parse(AMOSTRA))
    assert set(df.columns) == {"cod_munres", "diag", "mes_internacao"}
    assert df.height == 5  # linha I10 (hipertensão) filtrada


def test_prata_mes_internacao_nao_e_null() -> None:
    """Guard: se mes_internacao fosse toda null, transformar_prata retornaria 0 linhas.

    Esse teste falha se o formato de DT_INTER na fixture divergir do esperado pelo parser
    (bug real em produção: fixture usava 'YYYY-MM-DD' mas o DBF real é 'YYYYMMDD').
    """
    a = _ad()
    df = a.transformar_prata(a.parse(AMOSTRA))
    assert df.height > 0, "prata retornou 0 linhas — DT_INTER provavelmente em formato errado"
    nulls = df["mes_internacao"].null_count()
    assert nulls == 0, f"mes_internacao tem {nulls} nulls — formato DT_INTER errado"


def test_prata_mes_internacao_e_primeiro_dia_do_mes() -> None:
    a = _ad()
    df = a.transformar_prata(a.parse(AMOSTRA))
    # DT_INTER "20260903" e "20260911" (YYYYMMDD) devem resultar em 2026-09-01
    meses = df["mes_internacao"].to_list()
    assert all(m == date(2026, 9, 1) for m in meses)


def test_agregar_conta_aih_por_municipio_e_mes() -> None:
    a = _ad()
    ag = a.agregar(a.transformar_prata(a.parse(AMOSTRA)))
    # fixture: SP = 3 J, Campinas = 2 J, tudo em 2026-09 → 1 linha por município
    assert ag.height == 2
    por = {r["cod_munres"]: r["internacoes"] for r in ag.iter_rows(named=True)}
    assert por == {"355030": 3, "350950": 2}


def test_extrair_valida_contrato() -> None:
    assert _ad().extrair(Janela(2026, 9)).height == 6


def test_contrato_reprova_layout_mudado() -> None:
    # Falta DT_INTER → contrato deve falhar
    df = pl.DataFrame({"MUNIC_RES": ["355030"], "DIAG_PRINC": ["J189"]})
    with pytest.raises(ContratoVioladoError):
        CONTRATO.validar(df)


def test_contrato_reprova_sem_diag() -> None:
    df = pl.DataFrame({"MUNIC_RES": ["355030"], "DT_INTER": ["2026-09-01"]})
    with pytest.raises(ContratoVioladoError):
        CONTRATO.validar(df)


def test_prata_normaliza_munic_res_float() -> None:
    """MUNIC_RES como '355030.0' (DBF numeric float via write_csv) é normalizado para '355030'."""
    dados = (
        b"MUNIC_RES,MUNIC_MOV,DIAG_PRINC,DT_INTER,ANO_CMPT,MES_CMPT\n"
        b"355030.0,355030.0,J189,20260903,2026,9\n"
        b"350950.0,350950.0,J450,20260904,2026,9\n"
    )
    a = _ad()
    prata = a.transformar_prata(a.parse(dados))
    assert prata.height == 2
    assert set(prata["cod_munres"].to_list()) == {"355030", "350950"}


def test_prata_normaliza_munic_res_inteiro() -> None:
    """MUNIC_RES como string '355030' (caso real confirmado) também funciona."""
    dados = (
        b"MUNIC_RES,MUNIC_MOV,DIAG_PRINC,DT_INTER,ANO_CMPT,MES_CMPT\n"
        b"355030,355030,J189,20260903,2026,9\n"
    )
    a = _ad()
    prata = a.transformar_prata(a.parse(dados))
    assert prata.height == 1
    assert prata["cod_munres"][0] == "355030"
