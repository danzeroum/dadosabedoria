"""Unidade do adaptador PNCP (parse/prata/agregação + contrato) — puro, sem rede/DB."""

from __future__ import annotations

import polars as pl
import pytest

from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.pncp import CONTRATO, AdaptadorPncp
from app.ingestao.contratos import ContratoVioladoError
from tests.fixtures.pncp import AMOSTRA, FetcherFake


def _ad() -> AdaptadorPncp:
    return AdaptadorPncp(FetcherFake(AMOSTRA))


def test_parse_le_data() -> None:
    df = _ad().parse(AMOSTRA)
    assert "unidadeOrgao" in df.columns
    assert df.height == 4


def test_prata_extrai_ibge_aninhado_e_filtra() -> None:
    a = _ad()
    df = a.transformar_prata(a.parse(AMOSTRA))
    assert set(df.columns) == {"cod_ibge", "valor"}
    assert df.height == 3  # o contrato sem valorGlobal é descartado


def test_agregar_soma_por_municipio() -> None:
    a = _ad()
    ag = a.agregar(a.transformar_prata(a.parse(AMOSTRA)))
    por = {r["cod_ibge"]: r["valor_contratos"] for r in ag.iter_rows(named=True)}
    assert por == {"3550308": 1_500_000.0, "3509502": 250_000.0}


def test_extrair_valida_contrato() -> None:
    assert _ad().extrair(Janela(2024, 1)).height == 4


def test_contrato_reprova_layout_mudado() -> None:
    df = pl.DataFrame({"valorGlobal": [1.0]})  # falta a coluna 'unidadeOrgao'
    with pytest.raises(ContratoVioladoError):
        CONTRATO.validar(df)
