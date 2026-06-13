"""Integração do endpoint GET /v1/via-viva/{codigo_ibge} (MOB-01).

Semeia execucao_funcao diretamente para controlar os dados de função 26 (Transporte).
"""

from __future__ import annotations

import os
from datetime import UTC, date, datetime

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import connect

pytestmark = pytest.mark.integration

_DELETE = text("DELETE FROM execucao_funcao")


async def _limpar() -> None:
    admin_url = os.environ.get("ADMIN_DATABASE_URL", get_settings().database_url)
    async with connect(admin_url) as conn:
        await conn.execute(_DELETE)


async def _seed_funcao26(conn_url: str) -> None:
    """Insere função 26 para Campinas (≥ R$300/hab → elevado) e SP sem função 26."""
    async with connect(conn_url) as conn:
        _q = "SELECT id FROM territorio WHERE codigo_ibge = :c AND nivel = 'municipio'"
        terr_campinas = (await conn.execute(text(_q), {"c": "3509502"})).scalar_one()
        terr_sp = (await conn.execute(text(_q), {"c": "3550308"})).scalar_one()
        fonte_id = (
            await conn.execute(text("SELECT id FROM fonte WHERE codigo = 'siconfi'"))
        ).scalar_one()

        now = datetime.now(tz=UTC)
        periodo = date(2023, 1, 1)

        _ins = (
            "INSERT INTO execucao_funcao "
            "(territorio_id, periodo, funcao_cod, funcao_nome,"
            " empenhado, liquidado, fonte_id, carregado_em) "
            "VALUES (:tid, :per, :fcod, :fnome, :emp, :liq, :fid, :now) "
            "ON CONFLICT DO NOTHING"
        )
        # Campinas: função 26 com R$ 400M liquidado / ~1.2M hab ≈ R$ 333/hab → elevado
        await conn.execute(
            text(_ins),
            {
                "tid": terr_campinas,
                "per": periodo,
                "fcod": "26",
                "fnome": "Transporte",
                "emp": 450_000_000,
                "liq": 400_000_000,
                "fid": fonte_id,
                "now": now,
            },
        )
        # SP: função 20 (sem função 26)
        await conn.execute(
            text(_ins),
            {
                "tid": terr_sp,
                "per": periodo,
                "fcod": "20",
                "fnome": "Agricultura",
                "emp": 10_000_000,
                "liq": 8_000_000,
                "fid": fonte_id,
                "now": now,
            },
        )


@pytest.mark.asyncio()
async def test_via_viva_200_campinas(client: AsyncClient, db_pronto: None) -> None:
    await _limpar()
    await _seed_funcao26(get_settings().database_url)
    resp = await client.get("/v1/via-viva/3509502")
    assert resp.status_code == 200
    body = resp.json()
    assert body["codigo_ibge"] == "3509502"
    assert body["nome"] == "Campinas"
    assert abs(body["valor_liquidado"] - 400_000_000.0) < 1.0
    assert body["nivel"] in ("elevado", "moderado", "baixo")
    assert body["ano"] == 2023
    assert body["nota"] != ""


@pytest.mark.asyncio()
async def test_via_viva_200_sp_sem_funcao26_retorna_baixo(
    client: AsyncClient, db_pronto: None
) -> None:
    await _limpar()
    await _seed_funcao26(get_settings().database_url)
    resp = await client.get("/v1/via-viva/3550308")
    assert resp.status_code == 200
    body = resp.json()
    assert body["codigo_ibge"] == "3550308"
    # SP tem SICONFI mas sem função 26 → zero → baixo
    assert body["valor_liquidado"] == pytest.approx(0.0)
    assert body["nivel"] == "baixo"


@pytest.mark.asyncio()
async def test_via_viva_404_sem_siconfi(client: AsyncClient, db_pronto: None) -> None:
    await _limpar()
    resp = await client.get("/v1/via-viva/3550308")
    assert resp.status_code == 404


@pytest.mark.asyncio()
async def test_via_viva_404_municipio_invalido(client: AsyncClient, db_pronto: None) -> None:
    resp = await client.get("/v1/via-viva/9999999")
    assert resp.status_code == 404
