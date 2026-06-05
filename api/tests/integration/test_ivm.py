"""IVM: view materializada + endpoints (mapa semafórico + drill-down), contra Postgres real.

Usa dois municípios isolados (BH, Rio) num período próprio para exercitar a normalização min-max,
sem tocar a série de SP que outros testes verificam.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.config import get_settings
from app.core.db import connect
from app.indicadores.ivm import refrescar_ivm
from app.ingestao.ouro import CelulaOuro, ContextoLinhagem, GravadorOuro
from app.ingestao.supressao import MetaIndicadorSupressao

pytestmark = pytest.mark.integration

_PERIODO = date(2026, 8, 1)
_BH = "3106200"  # Belo Horizonte (menos vulnerável no fixture)
_RIO = "3304557"  # Rio de Janeiro (mais vulnerável no fixture)


async def _id_indicador(conn: AsyncConnection, codigo: str) -> tuple[int, int]:
    row = (
        (
            await conn.execute(
                text("SELECT id, fonte_id FROM indicador WHERE codigo = :c"), {"c": codigo}
            )
        )
        .mappings()
        .first()
    )
    assert row is not None
    return int(row["id"]), int(row["fonte_id"])


async def _id_territorio(conn: AsyncConnection, codigo_ibge: str) -> int:
    return int(
        (
            await conn.execute(
                text("SELECT id FROM territorio WHERE codigo_ibge = :c"), {"c": codigo_ibge}
            )
        ).scalar_one()
    )


async def _semear_ivm(conn: AsyncConnection) -> None:
    await conn.execute(
        text(
            "INSERT INTO territorio (codigo_ibge, nome, nivel, uf, populacao) VALUES "
            "('3106200','Belo Horizonte','municipio','MG',2315560),"
            "('3304557','Rio de Janeiro','municipio','RJ',6747815) "
            "ON CONFLICT (codigo_ibge) DO NOTHING"
        )
    )
    caged_id, caged_fonte = await _id_indicador(conn, "trabalho.emprego.saldo_caged")
    cred_id, cred_fonte = await _id_indicador(conn, "credito.operacoes.saldo_total")
    bh = await _id_territorio(conn, _BH)
    rio = await _id_territorio(conn, _RIO)

    meta = {
        caged_id: MetaIndicadorSupressao(0, origem_sensivel=False),
        cred_id: MetaIndicadorSupressao(0, origem_sensivel=False),
    }
    # BH: muito emprego + muito crédito (menos vulnerável). Rio: o oposto (mais vulnerável).
    celulas = [
        CelulaOuro(caged_id, bh, _PERIODO, "mensal", Decimal(10000), None, 5, caged_fonte),
        CelulaOuro(caged_id, rio, _PERIODO, "mensal", Decimal(-5000), None, 5, caged_fonte),
        CelulaOuro(cred_id, bh, _PERIODO, "mensal", Decimal("2e11"), None, 4, cred_fonte),
        CelulaOuro(cred_id, rio, _PERIODO, "mensal", Decimal("5e10"), None, 4, cred_fonte),
    ]
    await grav_escrever(conn, celulas, meta, caged_fonte)


async def grav_escrever(conn, celulas, meta, fonte_id) -> None:  # noqa: ANN001
    await GravadorOuro(conn).escrever_ouro(
        celulas, meta, ContextoLinhagem(fonte_id, None, "ivm test", "test")
    )


async def test_mapa_semaforo_por_periodo(client) -> None:
    async with connect(get_settings().database_url) as conn:
        await _semear_ivm(conn)
    await refrescar_ivm()

    r = await client.get("/v1/ivm", params={"periodo": "2026-08"})
    assert r.status_code == 200
    body = r.json()
    por_mun = {d["codigo_ibge"]: d for d in body["dados"]}
    assert por_mun[_BH]["ivm"] == 0.0
    assert por_mun[_BH]["semaforo"] == "verde"
    assert por_mun[_RIO]["ivm"] == 100.0
    assert por_mun[_RIO]["semaforo"] == "vermelho"
    assert body["meta"]["versao_metodologia"] == "v1"
    assert "trabalho.emprego.saldo_caged" in body["meta"]["componentes"]


async def test_periodo_padrao_e_o_mais_recente(client) -> None:
    async with connect(get_settings().database_url) as conn:
        await _semear_ivm(conn)
    await refrescar_ivm()

    r = await client.get("/v1/ivm")  # sem período → mais recente (2026-08)
    body = r.json()
    assert body["meta"]["periodo"] == "2026-08"
    assert len(body["dados"]) >= 2


async def test_serie_municipio_drilldown(client) -> None:
    # SP tem IVM semeado (2026-02..04) — drill-down sem depender deste teste escrever em SP.
    r = await client.get("/v1/ivm/3550308")
    assert r.status_code == 200
    body = r.json()
    assert body["dados"]
    assert all(d["codigo_ibge"] == "3550308" for d in body["dados"])


async def test_serie_municipio_sem_ivm_404(client) -> None:
    r = await client.get("/v1/ivm/0000000")
    assert r.status_code == 404
    assert r.json()["erro"] == "nao_encontrado"
