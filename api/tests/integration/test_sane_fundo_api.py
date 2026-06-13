"""Integração do endpoint GET /v1/sane-fundo/{codigo_ibge} (SANE-05).

Semeia execucao_funcao diretamente para controlar os dados de função 17 (Saneamento).
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


async def _seed_funcao17(conn_url: str) -> None:
    """Insere função 17 para Campinas (≥ R$60/hab → expressivo) e SP sem função 17."""
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
        # Campinas: função 17 com R$ 90M liquidado / ~1.2M hab ≈ R$ 75/hab → expressivo
        await conn.execute(
            text(_ins),
            {
                "tid": terr_campinas,
                "per": periodo,
                "fcod": "17",
                "fnome": "Saneamento",
                "emp": 100_000_000,
                "liq": 90_000_000,
                "fid": fonte_id,
                "now": now,
            },
        )
        # SP: função 20 (sem função 17)
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
async def test_sane_fundo_200_campinas(client: AsyncClient, db_pronto: None) -> None:
    await _limpar()
    await _seed_funcao17(get_settings().database_url)
    resp = await client.get("/v1/sane-fundo/3509502")
    assert resp.status_code == 200
    body = resp.json()
    assert body["codigo_ibge"] == "3509502"
    assert body["nome"] == "Campinas"
    assert abs(body["valor_liquidado"] - 90_000_000.0) < 1.0
    assert body["nivel"] in ("expressivo", "moderado", "incipiente")
    assert body["ano"] == 2023
    assert body["nota"] != ""


@pytest.mark.asyncio()
async def test_sane_fundo_200_sp_sem_funcao17_retorna_incipiente(
    client: AsyncClient, db_pronto: None
) -> None:
    await _limpar()
    await _seed_funcao17(get_settings().database_url)
    resp = await client.get("/v1/sane-fundo/3550308")
    assert resp.status_code == 200
    body = resp.json()
    assert body["codigo_ibge"] == "3550308"
    # SP tem SICONFI mas sem função 17 → zero → incipiente
    assert body["valor_liquidado"] == pytest.approx(0.0)
    assert body["nivel"] == "incipiente"


@pytest.mark.asyncio()
async def test_sane_fundo_404_sem_siconfi(client: AsyncClient, db_pronto: None) -> None:
    await _limpar()
    resp = await client.get("/v1/sane-fundo/3550308")
    assert resp.status_code == 404


@pytest.mark.asyncio()
async def test_sane_fundo_404_municipio_invalido(client: AsyncClient, db_pronto: None) -> None:
    resp = await client.get("/v1/sane-fundo/9999999")
    assert resp.status_code == 404
