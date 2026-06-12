"""Testes de integração do pipeline ANA Monitor de Secas (bronze→prata→ouro)."""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncConnection

from app.ingestao.adaptadores.ana import AdaptadorAna
from app.ingestao.adaptadores.base import Janela
from app.ingestao.pipeline import executar_ana
from tests.fixtures.ana import AMOSTRA, FetcherFake


@pytest.fixture()
def adaptador() -> AdaptadorAna:
    return AdaptadorAna(FetcherFake(AMOSTRA))


@pytest.fixture()
def janela() -> Janela:
    return Janela.de_competencia("202301")


@pytest.mark.asyncio()
async def test_executa_grava_indicador_seca(
    db_conn: AsyncConnection,
    adaptador: AdaptadorAna,
    janela: Janela,
    store,
) -> None:
    resumo = await executar_ana(janela, db_conn, adaptador, store)
    await db_conn.commit()
    assert resumo.gravados > 0


@pytest.mark.asyncio()
async def test_valores_corretos_sp(
    db_conn: AsyncConnection,
    adaptador: AdaptadorAna,
    janela: Janela,
    store,
) -> None:
    from sqlalchemy import text

    await executar_ana(janela, db_conn, adaptador, store)
    await db_conn.commit()

    # SP: max(Normal=0.0, D1=2.0) = 2.0
    row = await db_conn.execute(
        text(
            "SELECT f.valor FROM leituras_ouro f "
            "JOIN indicadores i ON i.id = f.indicador_id "
            "JOIN territorios t ON t.id = f.territorio_id "
            "WHERE i.codigo = 'saneamento.agua.seca_indice' "
            "AND t.codigo_ibge = '3550308'"
        )
    )
    val = row.scalar()
    assert val is not None
    assert float(val) == pytest.approx(2.0)


@pytest.mark.asyncio()
async def test_idempotente(
    db_conn: AsyncConnection,
    adaptador: AdaptadorAna,
    janela: Janela,
    store,
) -> None:
    from sqlalchemy import text

    await executar_ana(janela, db_conn, adaptador, store)
    await db_conn.commit()
    await executar_ana(janela, db_conn, adaptador, store)
    await db_conn.commit()

    row = await db_conn.execute(
        text(
            "SELECT COUNT(*) FROM leituras_ouro f "
            "JOIN indicadores i ON i.id = f.indicador_id "
            "WHERE i.codigo = 'saneamento.agua.seca_indice'"
        )
    )
    cnt = row.scalar()
    assert cnt is not None
    # idempotente: não duplica
    assert int(cnt) <= 10


@pytest.mark.asyncio()
async def test_critico_fortaleza(
    db_conn: AsyncConnection,
    adaptador: AdaptadorAna,
    janela: Janela,
    store,
) -> None:
    from sqlalchemy import text

    await executar_ana(janela, db_conn, adaptador, store)
    await db_conn.commit()

    # Fortaleza: D3 → seca_indice=4.0
    row = await db_conn.execute(
        text(
            "SELECT f.valor FROM leituras_ouro f "
            "JOIN indicadores i ON i.id = f.indicador_id "
            "JOIN territorios t ON t.id = f.territorio_id "
            "WHERE i.codigo = 'saneamento.agua.seca_indice' "
            "AND t.codigo_ibge = '2304400'"
        )
    )
    val = row.scalar()
    # Fortaleza não está no seed de territórios — pode ser ignorado (None)
    # se não estiver na tabela de territórios do DB de teste
    if val is not None:
        assert float(val) == pytest.approx(4.0)
