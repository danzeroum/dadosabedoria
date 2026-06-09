"""Integração da esteira SICONFI Anexo I-E (execução por função) → tabela ``execucao_funcao``.

OndeFoi re-ancorado (ADR-0029): grava Empenhado/Liquidado por função numa fato dedicada (sem PII,
sem supressão k-anon). Contra Postgres real.
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import connect
from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.siconfi import AdaptadorSiconfi
from app.ingestao.bronze import ArmazenamentoMemoria
from app.ingestao.pipeline import executar_siconfi_funcoes
from tests.fixtures.siconfi import AMOSTRA_FUNCOES, FetcherFake

pytestmark = pytest.mark.integration

_SQL_SP = text(
    """
    SELECT ef.funcao_cod, ef.funcao_nome, ef.empenhado, ef.liquidado
    FROM execucao_funcao ef
    JOIN territorio t ON t.id = ef.territorio_id
    WHERE t.codigo_ibge = '3550308' AND ef.periodo = '2024-01-01'
    ORDER BY ef.funcao_cod
    """
)

_DELETE = text("DELETE FROM execucao_funcao")


async def _limpar() -> None:
    """Limpa execucao_funcao via ADMIN_DATABASE_URL (role_analitica não tem DELETE)."""
    admin_url = os.environ.get("ADMIN_DATABASE_URL", get_settings().database_url)
    async with connect(admin_url) as conn:
        await conn.execute(_DELETE)


async def test_pipeline_grava_execucao_por_funcao(db_pronto: None) -> None:
    await _limpar()
    store = ArmazenamentoMemoria()
    adaptador = AdaptadorSiconfi(FetcherFake(AMOSTRA_FUNCOES))
    async with connect(get_settings().database_url) as conn:
        resumo = await executar_siconfi_funcoes(
            Janela(2024, 1), conn, adaptador, store, responsavel="test"
        )
        assert resumo.registros_carregados == 4  # 08/10/12/17; a subfunção 10.301 fica fora
        assert resumo.suprimidos == 0

        rows = (await conn.execute(_SQL_SP)).mappings().all()
        assert [r["funcao_cod"] for r in rows] == ["08", "10", "12", "17"]
        saude = next(r for r in rows if r["funcao_cod"] == "10")
        assert saude["funcao_nome"] == "Saúde"
        # Valores exatos da API real (fixture fiel-à-forma, ADR-0028)
        assert float(saude["liquidado"]) == 21_927_842_055.50
        assert float(saude["empenhado"]) == 22_752_837_820.49
        # Guarda de ordem de grandeza: dezenas de bilhões, não R$ 1,5 bi (ADR-0034).
        assert float(saude["liquidado"]) > 10e9  # R$ 10 bi mínimo; real ~R$ 21,9 bi
        assert float(saude["empenhado"]) > 10e9  # R$ 10 bi mínimo; real ~R$ 22,7 bi
        # empenhar ≠ liquidar: mesma coluna lida 2× tornaria os valores idênticos (ADR-0034).
        assert saude["empenhado"] != saude["liquidado"]
    assert store.ler("siconfi/funcoes/2024.json") == AMOSTRA_FUNCOES


async def test_pipeline_funcoes_idempotente(db_pronto: None) -> None:
    await _limpar()
    adaptador = AdaptadorSiconfi(FetcherFake(AMOSTRA_FUNCOES))
    for _ in range(2):
        async with connect(get_settings().database_url) as conn:
            await executar_siconfi_funcoes(
                Janela(2024, 1), conn, adaptador, ArmazenamentoMemoria(), responsavel="test"
            )
    async with connect(get_settings().database_url) as conn:
        n = (
            await conn.execute(
                text(
                    "SELECT count(*) FROM execucao_funcao ef "
                    "JOIN territorio t ON t.id = ef.territorio_id "
                    "WHERE t.codigo_ibge = '3550308' AND ef.periodo = '2024-01-01'"
                )
            )
        ).scalar_one()
    assert n == 4  # reexecutar não duplica (upsert por território×período×função)
