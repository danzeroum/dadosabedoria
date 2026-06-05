"""Integração da esteira ESTBAN: bronze→prata→ouro→escrever_ouro, contra Postgres real."""

from __future__ import annotations

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.config import get_settings
from app.core.db import connect
from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.estban import AdaptadorEstban
from app.ingestao.bronze import ArmazenamentoMemoria
from app.ingestao.pipeline import executar_estban
from tests.fixtures.caged import FetcherFake
from tests.fixtures.estban import AMOSTRA_ESTBAN

pytestmark = pytest.mark.integration

_SQL_CREDITO_RIO = text(
    """
    SELECT v.valor, v.suprimido FROM valor v
    JOIN indicador i ON i.id = v.indicador_id
    JOIN territorio t ON t.id = v.territorio_id
    WHERE i.codigo = 'credito.operacoes.saldo_total'
      AND t.codigo_ibge = '3304557' AND v.periodo = '2026-07-01'
    """
)


async def _inserir_rio(conn: AsyncConnection) -> None:
    await conn.execute(
        text(
            """
            INSERT INTO territorio (codigo_ibge, nome, nivel, uf, populacao)
            VALUES ('3304557','Rio de Janeiro','municipio','RJ',6747815)
            ON CONFLICT (codigo_ibge) DO NOTHING
            """
        )
    )


async def test_pipeline_grava_credito_via_ouro(db_pronto: None) -> None:
    store = ArmazenamentoMemoria()
    adaptador = AdaptadorEstban(FetcherFake(AMOSTRA_ESTBAN))
    async with connect(get_settings().database_url) as conn:
        await _inserir_rio(conn)
        resumo = await executar_estban(Janela(2026, 7), conn, adaptador, store, responsavel="test")

        assert resumo.registros_carregados == 1  # só Rio (9999999 fora do cadastro)
        assert resumo.suprimidos == 0

        row = (await conn.execute(_SQL_CREDITO_RIO)).mappings().first()
        assert row is not None
        assert row["suprimido"] is False
        assert float(row["valor"]) == 1_500_000_500.0  # reais
    assert store.ler("estban/202607.csv") == AMOSTRA_ESTBAN


async def test_pipeline_idempotente(db_pronto: None) -> None:
    adaptador = AdaptadorEstban(FetcherFake(AMOSTRA_ESTBAN))
    for _ in range(2):
        async with connect(get_settings().database_url) as conn:
            await _inserir_rio(conn)
            await executar_estban(
                Janela(2026, 7), conn, adaptador, ArmazenamentoMemoria(), responsavel="test"
            )
    async with connect(get_settings().database_url) as conn:
        n = (
            await conn.execute(
                text(
                    "SELECT count(*) FROM valor v JOIN indicador i ON i.id=v.indicador_id "
                    "JOIN territorio t ON t.id=v.territorio_id "
                    "WHERE i.codigo='credito.operacoes.saldo_total' "
                    "AND t.codigo_ibge='3304557' AND v.periodo='2026-07-01'"
                )
            )
        ).scalar_one()
    assert n == 1
