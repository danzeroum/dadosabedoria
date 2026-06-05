"""Integração da esteira CAGED: bronze→prata→ouro→escrever_ouro, contra Postgres real.

Usa um município isolado (Rio) para não colidir com a série semeada (SP/Campinas) que outros
testes verificam. Prova: saldo correto, proveniência (linhagem com hash do bruto), e idempotência.
"""

from __future__ import annotations

from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.config import get_settings
from app.core.db import connect
from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.caged import AdaptadorCaged
from app.ingestao.bronze import ArmazenamentoMemoria
from app.ingestao.pipeline import executar_caged
from tests.fixtures.caged import AMOSTRA_RIO, FetcherFake

pytestmark = pytest.mark.integration

_SQL_VALOR_RIO = text(
    """
    SELECT v.valor, v.suprimido FROM valor v
    JOIN indicador i ON i.id = v.indicador_id
    JOIN territorio t ON t.id = v.territorio_id
    WHERE i.codigo = 'trabalho.emprego.saldo_caged'
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


async def test_pipeline_grava_saldo_via_ouro(db_pronto: None) -> None:
    store = ArmazenamentoMemoria()
    adaptador = AdaptadorCaged(FetcherFake(AMOSTRA_RIO))
    async with connect(get_settings().database_url) as conn:
        await _inserir_rio(conn)
        resumo = await executar_caged(Janela(2026, 7), conn, adaptador, store, responsavel="test")

        assert resumo.registros_carregados == 1  # só Rio (999999 fora do cadastro)
        assert resumo.suprimidos == 0  # saldo: n_minimo=0 → nunca suprimido

        row = (await conn.execute(_SQL_VALOR_RIO)).mappings().first()
        assert row is not None
        assert row["suprimido"] is False
        assert row["valor"] == Decimal(3)

        lin = (
            (
                await conn.execute(
                    text(
                        "SELECT hash_origem, url_extracao FROM linhagem "
                        "WHERE transformacoes LIKE 'caged 202607%' "
                        "ORDER BY executado_em DESC LIMIT 1"
                    )
                )
            )
            .mappings()
            .first()
        )
    assert lin is not None
    assert lin["hash_origem"]  # bronze rodou (hash do bruto)
    assert lin["url_extracao"] == "fixture://caged"
    assert store.ler("caged/202607.txt") == AMOSTRA_RIO


async def test_pipeline_idempotente(db_pronto: None) -> None:
    adaptador = AdaptadorCaged(FetcherFake(AMOSTRA_RIO))
    for _ in range(2):
        async with connect(get_settings().database_url) as conn:
            await _inserir_rio(conn)
            await executar_caged(
                Janela(2026, 7), conn, adaptador, ArmazenamentoMemoria(), responsavel="test"
            )
    async with connect(get_settings().database_url) as conn:
        n = (
            await conn.execute(
                text(
                    "SELECT count(*) FROM valor v JOIN indicador i ON i.id=v.indicador_id "
                    "JOIN territorio t ON t.id=v.territorio_id "
                    "WHERE i.codigo='trabalho.emprego.saldo_caged' "
                    "AND t.codigo_ibge='3304557' AND v.periodo='2026-07-01'"
                )
            )
        ).scalar_one()
    assert n == 1  # upsert não duplica
