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


def test_prata_mes_internacao_e_primeiro_dia_do_mes() -> None:
    a = _ad()
    df = a.transformar_prata(a.parse(AMOSTRA))
    # DT_INTER "2026-09-03" e "2026-09-11" devem resultar em 2026-09-01
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
