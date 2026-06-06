"""Unidade dos contratos de dados (validação na borda bronze) — puro, sem rede/DB."""

from __future__ import annotations

import polars as pl
import pytest

from app.ingestao.adaptadores.base import Janela
from app.ingestao.contratos import ContratoFonte, ContratoVioladoError


def test_valida_quando_completo() -> None:
    c = ContratoFonte(fonte="x", colunas_obrigatorias=frozenset({"a", "b"}))
    c.validar(pl.DataFrame({"a": [1], "b": [2]}))  # não levanta


def test_reprova_coluna_ausente() -> None:
    c = ContratoFonte(fonte="x", colunas_obrigatorias=frozenset({"a", "b"}))
    with pytest.raises(ContratoVioladoError, match="b"):
        c.validar(pl.DataFrame({"a": [1]}))


def test_reprova_sem_coluna_contendo() -> None:
    c = ContratoFonte(
        fonte="estban", colunas_obrigatorias=frozenset({"CODMUN"}), coluna_contendo="160"
    )
    with pytest.raises(ContratoVioladoError, match="160"):
        c.validar(pl.DataFrame({"CODMUN": ["3550308"], "VERBETE_999": [1]}))
    c.validar(pl.DataFrame({"CODMUN": ["3550308"], "VERBETE_160_credito": [1]}))  # ok


def test_reprova_bruto_vazio() -> None:
    c = ContratoFonte(fonte="x", colunas_obrigatorias=frozenset({"a"}), min_linhas=1)
    with pytest.raises(ContratoVioladoError, match="linha"):
        c.validar(pl.DataFrame(schema={"a": pl.Int64}))


def test_amostra_real_caged_satisfaz_contrato() -> None:
    from app.ingestao.adaptadores.caged import CONTRATO, AdaptadorCaged
    from tests.fixtures.caged import AMOSTRA_UNIT, FetcherFake

    df = AdaptadorCaged(FetcherFake(AMOSTRA_UNIT)).parse(AMOSTRA_UNIT)
    CONTRATO.validar(df)  # a amostra real passa


def test_extrair_caged_reprova_layout_mudado() -> None:
    from app.ingestao.adaptadores.caged import AdaptadorCaged
    from tests.fixtures.caged import FetcherFake

    # bruto sem as colunas esperadas (nomes sem acento simulam mudança de layout na origem).
    bruto = b"competenciamov;municipio\n202607;355030\n"
    with pytest.raises(ContratoVioladoError):
        AdaptadorCaged(FetcherFake(bruto)).extrair(Janela(2026, 7))
