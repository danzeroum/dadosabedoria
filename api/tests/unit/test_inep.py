"""Unidade do adaptador INEP (parse/prata/agregação + contrato) — puro, sem rede/DB."""

from __future__ import annotations

import polars as pl
import pytest

from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.inep import CONTRATO, AdaptadorInep
from app.ingestao.contratos import ContratoVioladoError
from tests.fixtures.inep import AMOSTRA, FetcherFake


def _ad() -> AdaptadorInep:
    return AdaptadorInep(FetcherFake(AMOSTRA))


def test_parse_le_csv() -> None:
    df = _ad().parse(AMOSTRA)
    assert "CO_MUNICIPIO" in df.columns
    assert df.height == 4


def test_prata_normaliza_e_filtra_nulos() -> None:
    a = _ad()
    df = a.transformar_prata(a.parse(AMOSTRA))
    assert set(df.columns) == {"cod_ibge", "matriculas"}
    assert df.height == 3  # a escola sem matrícula no fundamental é descartada


def test_agregar_soma_por_municipio() -> None:
    a = _ad()
    ag = a.agregar(a.transformar_prata(a.parse(AMOSTRA)))
    por = {r["cod_ibge"]: r["matriculas"] for r in ag.iter_rows(named=True)}
    assert por == {"3550308": 1000, "3509502": 150}


def test_extrair_valida_contrato() -> None:
    assert _ad().extrair(Janela(2024, 1)).height == 4


def test_contrato_reprova_layout_mudado() -> None:
    df = pl.DataFrame({"CO_MUNICIPIO": ["3550308"]})  # falta a coluna 'QT_MAT_FUND'
    with pytest.raises(ContratoVioladoError):
        CONTRATO.validar(df)
