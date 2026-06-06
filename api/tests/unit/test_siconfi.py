"""Unidade do adaptador SICONFI (parse/prata/agregação + contrato) — puro, sem rede/DB."""

from __future__ import annotations

import polars as pl
import pytest

from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.siconfi import CONTRATO, AdaptadorSiconfi
from app.ingestao.contratos import ContratoVioladoError
from tests.fixtures.siconfi import AMOSTRA, FetcherFake


def _ad() -> AdaptadorSiconfi:
    return AdaptadorSiconfi(FetcherFake(AMOSTRA))


def test_parse_le_items() -> None:
    df = _ad().parse(AMOSTRA)
    assert "cod_ibge" in df.columns
    assert df.height == 4


def test_prata_filtra_conta_alvo() -> None:
    a = _ad()
    df = a.transformar_prata(a.parse(AMOSTRA))
    assert set(df.columns) == {"cod_ibge", "valor"}
    assert df.height == 3  # ignora a linha "Receita Tributária"


def test_agregar_soma_por_municipio() -> None:
    a = _ad()
    ag = a.agregar(a.transformar_prata(a.parse(AMOSTRA)))
    por = {r["cod_ibge"]: r["transferencias"] for r in ag.iter_rows(named=True)}
    assert por == {"3550308": 1_500_000.0, "3509502": 250_000.0}


def test_extrair_valida_contrato() -> None:
    assert _ad().extrair(Janela(2024, 1)).height == 4


def test_contrato_reprova_layout_mudado() -> None:
    df = pl.DataFrame({"cod_ibge": ["3550308"], "valor": ["1"]})  # falta a coluna 'conta'
    with pytest.raises(ContratoVioladoError):
        CONTRATO.validar(df)
