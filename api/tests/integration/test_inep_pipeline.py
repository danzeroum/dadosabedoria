"""Integração da esteira INEP: bronze→prata→ouro→escrever_ouro, contra Postgres real."""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import connect
from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.inep import AdaptadorInep
from app.ingestao.bronze import ArmazenamentoMemoria
from app.ingestao.pipeline import executar_inep
from tests.fixtures.inep import AMOSTRA, FetcherFake

pytestmark = pytest.mark.integration

# Ano 2025 (o seed usa 2024) → a esteira grava célula própria, sem colidir com a semente.
_SQL_SP = text(
    """
    SELECT v.valor, v.suprimido, v.atualizacao FROM valor v
    JOIN indicador i ON i.id = v.indicador_id
    JOIN territorio t ON t.id = v.territorio_id
    WHERE i.codigo = 'educacao.matriculas.fundamental'
      AND t.codigo_ibge = '3550308' AND v.periodo = '2025-01-01'
    """
)


async def test_pipeline_grava_matriculas_via_ouro(db_pronto: None) -> None:
    store = ArmazenamentoMemoria()
    adaptador = AdaptadorInep(FetcherFake(AMOSTRA))
    async with connect(get_settings().database_url) as conn:
        resumo = await executar_inep(Janela(2025, 1), conn, adaptador, store, responsavel="test")

        # SP + Campinas (ambos no cadastro do seed); matrículas agregadas por município.
        assert resumo.registros_carregados == 2
        assert resumo.suprimidos == 0  # contagem pública, n_minimo=0 → sem supressão

        row = (await conn.execute(_SQL_SP)).mappings().first()
        assert row is not None
        assert row["suprimido"] is False
        assert row["atualizacao"] == "anual"
        assert int(row["valor"]) == 1000  # soma da fixture para SP
    assert store.ler("inep/2025.csv") == AMOSTRA


async def test_pipeline_idempotente(db_pronto: None) -> None:
    adaptador = AdaptadorInep(FetcherFake(AMOSTRA))
    for _ in range(2):
        async with connect(get_settings().database_url) as conn:
            await executar_inep(
                Janela(2025, 1), conn, adaptador, ArmazenamentoMemoria(), responsavel="test"
            )
    async with connect(get_settings().database_url) as conn:
        n = (
            await conn.execute(
                text(
                    "SELECT count(*) FROM valor v JOIN indicador i ON i.id=v.indicador_id "
                    "JOIN territorio t ON t.id=v.territorio_id "
                    "WHERE i.codigo='educacao.matriculas.fundamental' "
                    "AND t.codigo_ibge='3550308' AND v.periodo='2025-01-01'"
                )
            )
        ).scalar_one()
    assert n == 1
