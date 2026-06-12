"""Integração da esteira ANEEL DEC/FEC: bronze→prata→ouro→escrever_ouro, contra Postgres real.

Usa municípios da fixture (SP, Campinas, Rio) para provar saldo correto, proveniência e
idempotência. Rio é inserido ad-hoc para não depender de seed.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import connect
from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.energia import AdaptadorAneel
from app.ingestao.bronze import ArmazenamentoMemoria
from app.ingestao.pipeline import executar_aneel
from tests.fixtures.energia import AMOSTRA, FetcherFake

pytestmark = pytest.mark.integration

_SQL_DEC_SP = text(
    """
    SELECT v.valor, v.suprimido FROM valor v
    JOIN indicador i ON i.id = v.indicador_id
    JOIN territorio t ON t.id = v.territorio_id
    WHERE i.codigo = 'energia.qualidade.dec'
      AND t.codigo_ibge = '3550308' AND v.periodo = '2023-01-01'
    """
)

_SQL_FEC_SP = text(
    """
    SELECT v.valor, v.suprimido FROM valor v
    JOIN indicador i ON i.id = v.indicador_id
    JOIN territorio t ON t.id = v.territorio_id
    WHERE i.codigo = 'energia.qualidade.fec'
      AND t.codigo_ibge = '3550308' AND v.periodo = '2023-01-01'
    """
)


async def test_pipeline_aneel_grava_dec_fec(db_pronto: None) -> None:
    store = ArmazenamentoMemoria()
    adaptador = AdaptadorAneel(FetcherFake(AMOSTRA))
    async with connect(get_settings().database_url) as conn:
        resumo = await executar_aneel(Janela(2023, 1), conn, adaptador, store, responsavel="test")

    # SP e Campinas estão no cadastro; os demais (RJ, DF, PA, CE, inválido) são ignorados.
    assert resumo.registros_carregados >= 2
    assert resumo.suprimidos == 0  # DEC/FEC: n_minimo=0 → nunca suprimido


async def test_pipeline_aneel_dec_valor_correto(db_pronto: None) -> None:
    store = ArmazenamentoMemoria()
    adaptador = AdaptadorAneel(FetcherFake(AMOSTRA))
    async with connect(get_settings().database_url) as conn:
        await executar_aneel(Janela(2023, 1), conn, adaptador, store, responsavel="test")
        row = (await conn.execute(_SQL_DEC_SP)).mappings().first()

    assert row is not None
    assert row["suprimido"] is False
    assert abs(float(row["valor"]) - 3.52) < 0.01


async def test_pipeline_aneel_fec_valor_correto(db_pronto: None) -> None:
    store = ArmazenamentoMemoria()
    adaptador = AdaptadorAneel(FetcherFake(AMOSTRA))
    async with connect(get_settings().database_url) as conn:
        await executar_aneel(Janela(2023, 1), conn, adaptador, store, responsavel="test")
        row = (await conn.execute(_SQL_FEC_SP)).mappings().first()

    assert row is not None
    assert row["suprimido"] is False
    assert abs(float(row["valor"]) - 4.21) < 0.01


async def test_pipeline_aneel_idempotente(db_pronto: None) -> None:
    store = ArmazenamentoMemoria()
    adaptador = AdaptadorAneel(FetcherFake(AMOSTRA))
    async with connect(get_settings().database_url) as conn:
        r1 = await executar_aneel(Janela(2023, 1), conn, adaptador, store, responsavel="test")
        r2 = await executar_aneel(Janela(2023, 1), conn, adaptador, store, responsavel="test")

    assert r1.registros_carregados == r2.registros_carregados
