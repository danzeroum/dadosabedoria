"""Integração do endpoint GET /v1/cacador-arboviroses/{codigo_ibge} (SAUDE-02).

Semeia a tabela valor via pipeline para controlar os casos de dengue.
"""

from __future__ import annotations

import os

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import connect
from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.sinan import AdaptadorSinan
from app.ingestao.bronze import ArmazenamentoMemoria
from app.ingestao.pipeline import executar_sinan
from tests.fixtures.sinan import AMOSTRA, FetcherFake

pytestmark = pytest.mark.integration

_DELETE = text(
    "DELETE FROM valor v USING indicador i "
    "WHERE i.id = v.indicador_id AND i.codigo = 'saude.arboviroses.dengue_casos'"
)


async def _limpar() -> None:
    admin_url = os.environ.get("ADMIN_DATABASE_URL", get_settings().database_url)
    async with connect(admin_url) as conn:
        await conn.execute(_DELETE)


async def _limpar_e_semear() -> None:
    await _limpar()
    async with connect(get_settings().database_url) as conn:
        adaptador = AdaptadorSinan(FetcherFake(AMOSTRA))
        await executar_sinan(
            Janela(2023, 1), conn, adaptador, ArmazenamentoMemoria(), responsavel="test"
        )


@pytest.mark.asyncio()
async def test_cacador_arboviroses_200_sp(client: AsyncClient, db_pronto: None) -> None:
    await _limpar_e_semear()
    resp = await client.get("/v1/cacador-arboviroses/3550308")
    assert resp.status_code == 200
    body = resp.json()
    assert body["codigo_ibge"] == "3550308"
    assert body["nome"] == "São Paulo"
    assert body["casos_confirmados"] == 8
    assert body["ano"] == 2023
    assert body["nivel"] in ("crítico", "elevado", "moderado", "baixo", "sem_dado")
    assert body["nota"] != ""
    assert "meta" in body


@pytest.mark.asyncio()
async def test_cacador_arboviroses_200_campinas_suprimido(
    client: AsyncClient, db_pronto: None
) -> None:
    """Campinas tem 3 casos < n_minimo=5 → suprimido → casos_confirmados=None."""
    await _limpar_e_semear()
    resp = await client.get("/v1/cacador-arboviroses/3509502")
    assert resp.status_code == 200
    body = resp.json()
    assert body["codigo_ibge"] == "3509502"
    # Suprimido → casos_confirmados e incidencia_100k devem ser null
    assert body["casos_confirmados"] is None
    assert body["incidencia_100k"] is None
    assert body["nivel"] == "sem_dado"


@pytest.mark.asyncio()
async def test_cacador_arboviroses_404_sem_dado(client: AsyncClient, db_pronto: None) -> None:
    await _limpar()
    resp = await client.get("/v1/cacador-arboviroses/3550308")
    assert resp.status_code == 404


@pytest.mark.asyncio()
async def test_cacador_arboviroses_404_municipio_invalido(
    client: AsyncClient, db_pronto: None
) -> None:
    resp = await client.get("/v1/cacador-arboviroses/9999999")
    assert resp.status_code == 404
