"""Integração dos endpoints de analytics inferencial.

GET /v1/inferencia/distribuicao-funcao/{funcao_cod}
GET /v1/inferencia/municipio/{ibge}/orcamento

Semeia 3 municípios com dados de função 08 (Assistência Social) para cobrir
a lógica de distribuição nacional e percentil relativo.
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

# Campinas: 3509502  (~1.2 M hab) — maior gasto absoluto → maior per capita
# São Paulo: 3550308 (~11.5M hab) — gasto médio → per capita médio
# Rio de Janeiro: 3304557 (~6.2M hab) — menor gasto → menor per capita
_SEEDS = [
    ("3509502", "08", "Assistência Social", 180_000_000, 180_000_000),
    ("3550308", "08", "Assistência Social", 500_000_000, 500_000_000),
    ("3304557", "08", "Assistência Social", 50_000_000, 50_000_000),
]


async def _limpar() -> None:
    admin_url = os.environ.get("ADMIN_DATABASE_URL", get_settings().database_url)
    async with connect(admin_url) as conn:
        await conn.execute(_DELETE)


async def _seed(conn_url: str) -> None:
    async with connect(conn_url) as conn:
        q_terr = "SELECT id FROM territorio WHERE codigo_ibge = :c AND nivel = 'municipio'"
        fonte_id = (
            await conn.execute(text("SELECT id FROM fonte WHERE codigo = 'siconfi'"))
        ).scalar_one()

        ins = (
            "INSERT INTO execucao_funcao "
            "(territorio_id, periodo, funcao_cod, funcao_nome, empenhado, liquidado,"
            " fonte_id, carregado_em) "
            "VALUES (:tid, :per, :fcod, :fnome, :emp, :liq, :fid, :now) "
            "ON CONFLICT DO NOTHING"
        )
        now = datetime.now(tz=UTC)
        periodo = date(2023, 1, 1)

        for ibge, fcod, fnome, emp, liq in _SEEDS:
            tid = (await conn.execute(text(q_terr), {"c": ibge})).scalar_one()
            await conn.execute(
                text(ins),
                {
                    "tid": tid,
                    "per": periodo,
                    "fcod": fcod,
                    "fnome": fnome,
                    "emp": emp,
                    "liq": liq,
                    "fid": fonte_id,
                    "now": now,
                },
            )


@pytest.mark.asyncio()
async def test_distribuicao_funcao_200(client: AsyncClient, db_pronto: None) -> None:
    await _limpar()
    await _seed(get_settings().database_url)

    resp = await client.get("/v1/inferencia/distribuicao-funcao/08")
    assert resp.status_code == 200
    body = resp.json()
    assert body["funcao_cod"] == "08"
    assert body["funcao_nome"] == "Assistência Social"
    assert body["n_municipios"] == 3
    assert body["ano"] == 2023
    assert body["media_brl_hab"] is not None
    assert body["mediana_brl_hab"] is not None
    assert body["minimo"] is not None
    assert body["maximo"] is not None
    # maximo deve ser maior que media
    assert body["maximo"] > body["media_brl_hab"]


@pytest.mark.asyncio()
async def test_distribuicao_funcao_404_funcao_inexistente(
    client: AsyncClient, db_pronto: None
) -> None:
    await _limpar()
    resp = await client.get("/v1/inferencia/distribuicao-funcao/99")
    assert resp.status_code == 404


@pytest.mark.asyncio()
async def test_perfil_orcamentario_200(client: AsyncClient, db_pronto: None) -> None:
    await _limpar()
    await _seed(get_settings().database_url)

    # Campinas tem dado → deve retornar 200 com função 08
    resp = await client.get("/v1/inferencia/municipio/3509502/orcamento")
    assert resp.status_code == 200
    body = resp.json()
    assert body["codigo_ibge"] == "3509502"
    assert body["nome"] == "Campinas"
    assert body["ano"] == 2023
    assert len(body["funcoes"]) == 1
    f08 = body["funcoes"][0]
    assert f08["funcao_cod"] == "08"
    assert f08["valor_por_hab"] is not None
    assert f08["percentil"] is not None
    assert 0.0 <= f08["percentil"] <= 100.0


@pytest.mark.asyncio()
async def test_perfil_orcamentario_percentil_coerente(client: AsyncClient, db_pronto: None) -> None:
    """Campinas tem maior gasto per capita → percentil deve ser o mais alto."""
    await _limpar()
    await _seed(get_settings().database_url)

    resp_campinas = await client.get("/v1/inferencia/municipio/3509502/orcamento")
    resp_rio = await client.get("/v1/inferencia/municipio/3304557/orcamento")

    assert resp_campinas.status_code == 200
    assert resp_rio.status_code == 200

    pct_campinas = resp_campinas.json()["funcoes"][0]["percentil"]
    pct_rio = resp_rio.json()["funcoes"][0]["percentil"]

    # Campinas: R$180M / ~1.2M hab → ~R$147/hab (mais alto que Rio: R$50M / ~6.2M ≈ R$8/hab)
    assert pct_campinas > pct_rio


@pytest.mark.asyncio()
async def test_perfil_orcamentario_404_sem_dados(client: AsyncClient, db_pronto: None) -> None:
    await _limpar()
    # Campinas não tem dados após limpeza
    resp = await client.get("/v1/inferencia/municipio/3509502/orcamento")
    assert resp.status_code == 404


@pytest.mark.asyncio()
async def test_perfil_orcamentario_404_municipio_invalido(
    client: AsyncClient, db_pronto: None
) -> None:
    resp = await client.get("/v1/inferencia/municipio/9999999/orcamento")
    assert resp.status_code == 404
