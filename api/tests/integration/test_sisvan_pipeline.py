"""Integração da esteira SISVAN: bronze→prata→ouro→escrever_ouro, contra Postgres real."""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import connect
from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.sisvan import AdaptadorSisvan
from app.ingestao.bronze import ArmazenamentoMemoria
from app.ingestao.pipeline import executar_sisvan
from tests.fixtures.sisvan import AMOSTRA, FetcherFake

pytestmark = pytest.mark.integration

_SQL_SISVAN = text(
    """
    SELECT v.valor, v.n_amostra, v.suprimido FROM valor v
    JOIN indicador i ON i.id = v.indicador_id
    JOIN territorio t ON t.id = v.territorio_id
    WHERE i.codigo = 'alimentacao.nutricao.baixo_peso_pct'
      AND t.codigo_ibge = :ibge AND v.periodo = '2023-01-01'
    """
)


async def test_pipeline_sisvan_grava_indicador(db_pronto: None) -> None:
    store = ArmazenamentoMemoria()
    adaptador = AdaptadorSisvan(FetcherFake(AMOSTRA))
    async with connect(get_settings().database_url) as conn:
        resumo = await executar_sisvan(Janela(2023, 1), conn, adaptador, store, responsavel="test")

    assert resumo.registros_carregados >= 2


async def test_pipeline_sisvan_pct_campinas(db_pronto: None) -> None:
    store = ArmazenamentoMemoria()
    adaptador = AdaptadorSisvan(FetcherFake(AMOSTRA))
    async with connect(get_settings().database_url) as conn:
        await executar_sisvan(Janela(2023, 1), conn, adaptador, store, responsavel="test")
        row = (await conn.execute(_SQL_SISVAN, {"ibge": "3509502"})).mappings().first()

    assert row is not None
    assert row["suprimido"] is False
    # Campinas: 1/20 = 5.0%
    assert abs(float(row["valor"]) - 5.0) < 0.01
    assert row["n_amostra"] == 20


async def test_pipeline_sisvan_pct_sp(db_pronto: None) -> None:
    store = ArmazenamentoMemoria()
    adaptador = AdaptadorSisvan(FetcherFake(AMOSTRA))
    async with connect(get_settings().database_url) as conn:
        await executar_sisvan(Janela(2023, 1), conn, adaptador, store, responsavel="test")
        row = (await conn.execute(_SQL_SISVAN, {"ibge": "3550308"})).mappings().first()

    assert row is not None
    # SP: 1/50 = 2.0%
    assert abs(float(row["valor"]) - 2.0) < 0.01
    assert row["n_amostra"] == 50


async def test_pipeline_sisvan_idempotente(db_pronto: None) -> None:
    store = ArmazenamentoMemoria()
    adaptador = AdaptadorSisvan(FetcherFake(AMOSTRA))
    async with connect(get_settings().database_url) as conn:
        r1 = await executar_sisvan(Janela(2023, 1), conn, adaptador, store, responsavel="test")
        r2 = await executar_sisvan(Janela(2023, 1), conn, adaptador, store, responsavel="test")

    assert r1.registros_carregados == r2.registros_carregados
