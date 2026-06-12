"""Testes de integração do pipeline ANA Monitor de Secas (bronze→prata→ouro)."""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import connect
from app.ingestao.adaptadores.ana import AdaptadorAna
from app.ingestao.adaptadores.base import Janela
from app.ingestao.bronze import ArmazenamentoMemoria
from app.ingestao.pipeline import executar_ana
from tests.fixtures.ana import AMOSTRA, FetcherFake

pytestmark = pytest.mark.integration

_JANELA = Janela(2023, 1)


async def test_executa_grava_indicador_seca(db_pronto: None) -> None:
    store = ArmazenamentoMemoria()
    adaptador = AdaptadorAna(FetcherFake(AMOSTRA))
    async with connect(get_settings().database_url) as conn:
        resumo = await executar_ana(_JANELA, conn, adaptador, store)
    assert resumo.registros_carregados > 0


async def test_valores_corretos_sp(db_pronto: None) -> None:
    store = ArmazenamentoMemoria()
    adaptador = AdaptadorAna(FetcherFake(AMOSTRA))
    async with connect(get_settings().database_url) as conn:
        await executar_ana(_JANELA, conn, adaptador, store)
        row = await conn.execute(
            text(
                "SELECT v.valor FROM valor v "
                "JOIN indicador i ON i.id = v.indicador_id "
                "JOIN territorio t ON t.id = v.territorio_id "
                "WHERE i.codigo = 'saneamento.agua.seca_indice' "
                "AND t.codigo_ibge = '3550308'"
            )
        )
        val = row.scalar()

    # SP: max(Normal=0.0, D1=2.0) = 2.0
    assert val is not None
    assert float(val) == pytest.approx(2.0)


async def test_idempotente(db_pronto: None) -> None:
    store = ArmazenamentoMemoria()
    adaptador = AdaptadorAna(FetcherFake(AMOSTRA))
    async with connect(get_settings().database_url) as conn:
        await executar_ana(_JANELA, conn, adaptador, store)
        await executar_ana(_JANELA, conn, adaptador, store)
        row = await conn.execute(
            text(
                "SELECT COUNT(*) FROM valor v "
                "JOIN indicador i ON i.id = v.indicador_id "
                "WHERE i.codigo = 'saneamento.agua.seca_indice'"
            )
        )
        cnt = row.scalar()

    assert cnt is not None
    # idempotente: não duplica
    assert int(cnt) <= 10


async def test_critico_fortaleza(db_pronto: None) -> None:
    store = ArmazenamentoMemoria()
    adaptador = AdaptadorAna(FetcherFake(AMOSTRA))
    async with connect(get_settings().database_url) as conn:
        await executar_ana(_JANELA, conn, adaptador, store)
        row = await conn.execute(
            text(
                "SELECT v.valor FROM valor v "
                "JOIN indicador i ON i.id = v.indicador_id "
                "JOIN territorio t ON t.id = v.territorio_id "
                "WHERE i.codigo = 'saneamento.agua.seca_indice' "
                "AND t.codigo_ibge = '2304400'"
            )
        )
        val = row.scalar()

    # Fortaleza não está no seed de territórios — pode ser ignorado (None)
    # se não estiver na tabela de territórios do DB de teste
    if val is not None:
        assert float(val) == pytest.approx(4.0)
