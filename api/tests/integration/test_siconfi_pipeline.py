"""Integração da esteira SICONFI: bronze→prata→ouro→escrever_ouro, contra Postgres real."""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import connect
from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.siconfi import AdaptadorSiconfi
from app.ingestao.bronze import ArmazenamentoMemoria
from app.ingestao.pipeline import executar_siconfi
from tests.fixtures.siconfi import AMOSTRA, FetcherFake

pytestmark = pytest.mark.integration

# Exercício 2025 (o seed usa 2024) → a esteira grava célula própria, sem colidir com a semente.
_SQL_SP = text(
    """
    SELECT v.valor, v.suprimido, v.atualizacao FROM valor v
    JOIN indicador i ON i.id = v.indicador_id
    JOIN territorio t ON t.id = v.territorio_id
    WHERE i.codigo = 'financas.transferencias.correntes'
      AND t.codigo_ibge = '3550308' AND v.periodo = '2025-01-01'
    """
)


async def test_pipeline_grava_transferencias_via_ouro(db_pronto: None) -> None:
    store = ArmazenamentoMemoria()
    adaptador = AdaptadorSiconfi(FetcherFake(AMOSTRA))
    async with connect(get_settings().database_url) as conn:
        resumo = await executar_siconfi(Janela(2025, 1), conn, adaptador, store, responsavel="test")

        # SP + outro município (ambos no cadastro do seed); deduções/intra/off-target caem na prata.
        assert resumo.registros_carregados == 2
        assert resumo.suprimidos == 0

        row = (await conn.execute(_SQL_SP)).mappings().first()
        assert row is not None
        assert row["suprimido"] is False
        assert row["atualizacao"] == "anual"
        # Forma real (#0): só a Transferência Corrente orçamentária realizada — sem dedução/intra.
        assert float(row["valor"]) == 1_000_000.0
    assert store.ler("siconfi/2025.json") == AMOSTRA


async def test_pipeline_idempotente(db_pronto: None) -> None:
    adaptador = AdaptadorSiconfi(FetcherFake(AMOSTRA))
    for _ in range(2):
        async with connect(get_settings().database_url) as conn:
            await executar_siconfi(
                Janela(2025, 1), conn, adaptador, ArmazenamentoMemoria(), responsavel="test"
            )
    async with connect(get_settings().database_url) as conn:
        n = (
            await conn.execute(
                text(
                    "SELECT count(*) FROM valor v JOIN indicador i ON i.id=v.indicador_id "
                    "JOIN territorio t ON t.id=v.territorio_id "
                    "WHERE i.codigo='financas.transferencias.correntes' "
                    "AND t.codigo_ibge='3550308' AND v.periodo='2025-01-01'"
                )
            )
        ).scalar_one()
    assert n == 1
