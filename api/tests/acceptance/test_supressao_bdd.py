"""Liga o cenário Gherkin ao caminho ouro REAL (pytest-bdd) — invariante 1, §11."""

from __future__ import annotations

import asyncio
from datetime import date
from decimal import Decimal

import pytest
from pytest_bdd import given, parsers, scenario, then, when
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import connect
from app.ingestao.ouro import CelulaOuro, ContextoLinhagem, GravadorOuro
from app.ingestao.supressao import MetaIndicadorSupressao

pytestmark = pytest.mark.integration


@scenario("features/supressao.feature", "supressão de indicador de origem sensível")
def test_supressao_origem_sensivel() -> None:
    pass


@pytest.fixture
def contexto() -> dict:
    return {}


@given(parsers.parse("um indicador com origem_sensivel = true e n_minimo = {n:d}"))
def _indicador(contexto: dict, n: int) -> None:
    contexto["n_minimo"] = n
    contexto["origem_sensivel"] = True


@given(parsers.parse("uma célula município×mês com n_amostra = {n:d}"))
def _celula(contexto: dict, n: int) -> None:
    contexto["n_amostra"] = n


@when("a agregação ouro é executada")
def _executar(contexto: dict, db_pronto: None) -> None:
    asyncio.run(_rodar_ouro(contexto))


@then(parsers.parse('o valor é gravado com suprimido = true e motivo "{motivo}"'))
def _verificar(contexto: dict, motivo: str) -> None:
    row = contexto["row"]
    assert row["suprimido"] is True
    assert row["motivo_supressao"] == motivo
    assert row["valor"] is None


async def _rodar_ouro(contexto: dict) -> None:
    async with connect(get_settings().database_url) as conn:
        ind = (
            (
                await conn.execute(
                    text(
                        "SELECT id, fonte_id FROM indicador WHERE codigo='saude.resp.internacoes_j'"
                    )
                )
            )
            .mappings()
            .first()
        )
        ter = (
            await conn.execute(text("SELECT id FROM territorio WHERE codigo_ibge='3550308'"))
        ).scalar_one()

        periodo = date(2032, 6, 1)
        grav = GravadorOuro(conn)
        await grav.escrever_ouro(
            [
                CelulaOuro(
                    ind["id"],
                    ter,
                    periodo,
                    "mensal",
                    Decimal(99),
                    contexto["n_amostra"],
                    4,
                    ind["fonte_id"],
                )
            ],
            {
                ind["id"]: MetaIndicadorSupressao(
                    n_minimo=contexto["n_minimo"], origem_sensivel=contexto["origem_sensivel"]
                )
            },
            ContextoLinhagem(ind["fonte_id"], ind["id"], "bdd", "pytest"),
        )
        contexto["row"] = (
            (
                await conn.execute(
                    text(
                        "SELECT valor, suprimido, motivo_supressao FROM valor "
                        "WHERE indicador_id=:i AND territorio_id=:t AND periodo=:p AND versao=1"
                    ),
                    {"i": ind["id"], "t": ter, "p": periodo},
                )
            )
            .mappings()
            .first()
        )
