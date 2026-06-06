"""Unidade do adaptador DATASUS/SIH (parse/prata/agregação + contrato) — puro, sem rede/DB."""

from __future__ import annotations

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
    assert df.height == 6


def test_prata_filtra_grupo_j() -> None:
    a = _ad()
    df = a.transformar_prata(a.parse(AMOSTRA))
    assert set(df.columns) == {"cod_munres", "diag"}
    assert df.height == 5  # ignora a linha I10 (fora do grupo J)


def test_agregar_conta_aih_por_municipio() -> None:
    a = _ad()
    ag = a.agregar(a.transformar_prata(a.parse(AMOSTRA)))
    por = {r["cod_munres"]: r["internacoes"] for r in ag.iter_rows(named=True)}
    assert por == {"355030": 3, "350950": 2}


def test_extrair_valida_contrato() -> None:
    assert _ad().extrair(Janela(2026, 4)).height == 6


def test_contrato_reprova_layout_mudado() -> None:
    df = pl.DataFrame({"MUNIC_RES": ["355030"]})  # falta a coluna 'DIAG_PRINC'
    with pytest.raises(ContratoVioladoError):
        CONTRATO.validar(df)
