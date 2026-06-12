"""Integração da esteira IBGE PAM: bronze→prata→ouro→escrever_ouro, contra Postgres real.

Usa municípios da fixture (SP, Campinas, Rio) para provar soma correta, proveniência e
idempotência. Rio é inserido ad-hoc via pipeline; não depende do seed.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import connect
from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.pam import AdaptadorPam
from app.ingestao.bronze import ArmazenamentoMemoria
from app.ingestao.pipeline import executar_pam
from tests.fixtures.pam import AMOSTRA, FetcherFake

pytestmark = pytest.mark.integration

_SQL_PRODUCAO_SP = text(
    """
    SELECT v.valor, v.suprimido FROM valor v
    JOIN indicador i ON i.id = v.indicador_id
    JOIN territorio t ON t.id = v.territorio_id
    WHERE i.codigo = 'alimentacao.producao.valor_total'
      AND t.codigo_ibge = '3550308' AND v.periodo = '2023-01-01'
    """
)

_SQL_PRODUCAO_CAMPINAS = text(
    """
    SELECT v.valor, v.suprimido FROM valor v
    JOIN indicador i ON i.id = v.indicador_id
    JOIN territorio t ON t.id = v.territorio_id
    WHERE i.codigo = 'alimentacao.producao.valor_total'
      AND t.codigo_ibge = '3509502' AND v.periodo = '2023-01-01'
    """
)


async def test_pipeline_pam_grava_producao(db_pronto: None) -> None:
    store = ArmazenamentoMemoria()
    adaptador = AdaptadorPam(FetcherFake(AMOSTRA))
    async with connect(get_settings().database_url) as conn:
        resumo = await executar_pam(Janela(2023, 1), conn, adaptador, store, responsavel="test")

    assert resumo.registros_carregados >= 2
    assert resumo.suprimidos == 0  # n_minimo=0 → nunca suprimido


async def test_pipeline_pam_valor_correto(db_pronto: None) -> None:
    store = ArmazenamentoMemoria()
    adaptador = AdaptadorPam(FetcherFake(AMOSTRA))
    async with connect(get_settings().database_url) as conn:
        await executar_pam(Janela(2023, 1), conn, adaptador, store, responsavel="test")
        row = (await conn.execute(_SQL_PRODUCAO_CAMPINAS)).mappings().first()

    assert row is not None
    assert row["suprimido"] is False
    # Campinas: 8000+2000 Mil BRL = 10.000.000 BRL
    assert abs(float(row["valor"]) - 10_000_000.0) < 1.0


async def test_pipeline_pam_idempotente(db_pronto: None) -> None:
    store = ArmazenamentoMemoria()
    adaptador = AdaptadorPam(FetcherFake(AMOSTRA))
    async with connect(get_settings().database_url) as conn:
        r1 = await executar_pam(Janela(2023, 1), conn, adaptador, store, responsavel="test")
        r2 = await executar_pam(Janela(2023, 1), conn, adaptador, store, responsavel="test")

    assert r1.registros_carregados == r2.registros_carregados
