"""Integração da esteira DATASUS/SIH (origem sensível): k-anon suprime ANTES de gravar."""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import connect
from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.datasus import AdaptadorDatasus
from app.ingestao.bronze import ArmazenamentoMemoria
from app.ingestao.pipeline import executar_datasus
from tests.fixtures.datasus import AMOSTRA, FetcherFake

pytestmark = pytest.mark.integration

# Competência 2026-09 (livre do seed 04/05/06 e da poluição de outros testes).
_SQL_SP = text(
    """
    SELECT v.valor, v.suprimido, v.motivo_supressao, v.atualizacao FROM valor v
    JOIN indicador i ON i.id = v.indicador_id
    JOIN territorio t ON t.id = v.territorio_id
    WHERE i.codigo = 'saude.resp.internacoes_j'
      AND t.codigo_ibge = '3550308' AND v.periodo = '2026-09-01'
    """
)


async def test_pipeline_suprime_contagens_pequenas_antes_de_gravar(db_pronto: None) -> None:
    # A fixture dá SP=3 e Campinas=2 internações do grupo J — AMBAS abaixo do piso (n_minimo=5).
    # A regra única de k-anon suprime ANTES de gravar: a célula vira valor NULL + suprimido=true.
    store = ArmazenamentoMemoria()
    adaptador = AdaptadorDatasus(FetcherFake(AMOSTRA))
    async with connect(get_settings().database_url) as conn:
        resumo = await executar_datasus(Janela(2026, 9), conn, adaptador, store, responsavel="test")

        assert resumo.registros_carregados == 2  # SP + Campinas (ambos no cadastro)
        assert resumo.suprimidos == 2  # ambas as contagens (<5) protegidas

        row = (await conn.execute(_SQL_SP)).mappings().first()
        assert row is not None
        assert row["suprimido"] is True  # contagem pequena → protegida
        assert row["valor"] is None  # o número NUNCA é gravado
        assert row["motivo_supressao"] is not None
        assert row["atualizacao"] == "mensal"
    assert store.ler("datasus/202609.csv") == AMOSTRA


async def test_pipeline_idempotente(db_pronto: None) -> None:
    adaptador = AdaptadorDatasus(FetcherFake(AMOSTRA))
    for _ in range(2):
        async with connect(get_settings().database_url) as conn:
            await executar_datasus(
                Janela(2026, 9), conn, adaptador, ArmazenamentoMemoria(), responsavel="test"
            )
    async with connect(get_settings().database_url) as conn:
        n = (
            await conn.execute(
                text(
                    "SELECT count(*) FROM valor v JOIN indicador i ON i.id=v.indicador_id "
                    "JOIN territorio t ON t.id=v.territorio_id "
                    "WHERE i.codigo='saude.resp.internacoes_j' "
                    "AND t.codigo_ibge='3550308' AND v.periodo='2026-09-01'"
                )
            )
        ).scalar_one()
    assert n == 1
