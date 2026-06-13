"""Integração da esteira SINAN/Dengue: bronze→prata→ouro→escrever_ouro, contra Postgres real."""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import connect
from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.sinan import AdaptadorSinan
from app.ingestao.bronze import ArmazenamentoMemoria
from app.ingestao.pipeline import executar_sinan
from tests.fixtures.sinan import AMOSTRA, FetcherFake

pytestmark = pytest.mark.integration

_SQL_SINAN = text(
    """
    SELECT v.valor, v.n_amostra, v.suprimido FROM valor v
    JOIN indicador i ON i.id = v.indicador_id
    JOIN territorio t ON t.id = v.territorio_id
    WHERE i.codigo = 'saude.arboviroses.dengue_casos'
      AND t.codigo_ibge = :ibge AND v.periodo = '2023-01-01'
    """
)


async def test_pipeline_sinan_grava_indicador(db_pronto: None) -> None:
    store = ArmazenamentoMemoria()
    adaptador = AdaptadorSinan(FetcherFake(AMOSTRA))
    async with connect(get_settings().database_url) as conn:
        resumo = await executar_sinan(Janela(2023, 1), conn, adaptador, store, responsavel="test")

    assert resumo.registros_carregados >= 1


async def test_pipeline_sinan_sp_oito_casos(db_pronto: None) -> None:
    store = ArmazenamentoMemoria()
    adaptador = AdaptadorSinan(FetcherFake(AMOSTRA))
    async with connect(get_settings().database_url) as conn:
        await executar_sinan(Janela(2023, 1), conn, adaptador, store, responsavel="test")
        row = (await conn.execute(_SQL_SINAN, {"ibge": "3550308"})).mappings().first()

    assert row is not None
    assert row["suprimido"] is False
    assert int(row["n_amostra"]) == 8
    assert int(row["valor"]) == 8


async def test_pipeline_sinan_campinas_suprimido(db_pronto: None) -> None:
    """Campinas tem 3 casos < n_minimo=5 → deve ser suprimido."""
    store = ArmazenamentoMemoria()
    adaptador = AdaptadorSinan(FetcherFake(AMOSTRA))
    async with connect(get_settings().database_url) as conn:
        await executar_sinan(Janela(2023, 1), conn, adaptador, store, responsavel="test")
        row = (await conn.execute(_SQL_SINAN, {"ibge": "3509502"})).mappings().first()

    # Campinas: 3 casos < n_minimo=5 → suprimido
    assert row is not None
    assert row["suprimido"] is True


async def test_pipeline_sinan_idempotente(db_pronto: None) -> None:
    store = ArmazenamentoMemoria()
    adaptador = AdaptadorSinan(FetcherFake(AMOSTRA))
    async with connect(get_settings().database_url) as conn:
        r1 = await executar_sinan(Janela(2023, 1), conn, adaptador, store, responsavel="test")
        r2 = await executar_sinan(Janela(2023, 1), conn, adaptador, store, responsavel="test")

    assert r1.registros_carregados == r2.registros_carregados
