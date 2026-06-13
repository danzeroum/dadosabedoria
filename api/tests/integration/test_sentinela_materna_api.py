"""Integração do endpoint GET /v1/sentinela-materna/{codigo_ibge} (SAUDE-03).

Semeia a tabela valor diretamente para controlar o dado de gestante_baixo_peso_pct.
"""

from __future__ import annotations

import os

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import connect
from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.sisvan import AdaptadorSisvanGestante
from app.ingestao.bronze import ArmazenamentoMemoria
from app.ingestao.pipeline import executar_sisvan_gestante
from tests.fixtures.sisvan_gestante import AMOSTRA_GESTANTE, FetcherFake

pytestmark = pytest.mark.integration

_DELETE = text(
    "DELETE FROM valor v USING indicador i "
    "WHERE i.id = v.indicador_id AND i.codigo = 'saude.materno.gestante_baixo_peso_pct'"
)


async def _limpar() -> None:
    admin_url = os.environ.get("ADMIN_DATABASE_URL", get_settings().database_url)
    async with connect(admin_url) as conn:
        await conn.execute(_DELETE)


async def _limpar_e_semear() -> None:
    await _limpar()
    async with connect(get_settings().database_url) as conn:
        adaptador = AdaptadorSisvanGestante(FetcherFake(AMOSTRA_GESTANTE))
        await executar_sisvan_gestante(
            Janela(2023, 1), conn, adaptador, ArmazenamentoMemoria(), responsavel="test"
        )


@pytest.mark.asyncio()
async def test_sentinela_materna_200_campinas(client: AsyncClient, db_pronto: None) -> None:
    await _limpar_e_semear()
    resp = await client.get("/v1/sentinela-materna/3509502")
    assert resp.status_code == 200
    body = resp.json()
    assert body["codigo_ibge"] == "3509502"
    assert body["nome"] == "Campinas"
    assert abs(body["gestante_baixo_peso_pct"] - 15.0) < 0.01
    assert body["nivel"] == "moderado"
    assert body["n_gestantes"] == 20
    assert body["ano"] == 2023
    assert body["nota"] != ""


@pytest.mark.asyncio()
async def test_sentinela_materna_200_sp(client: AsyncClient, db_pronto: None) -> None:
    await _limpar_e_semear()
    resp = await client.get("/v1/sentinela-materna/3550308")
    assert resp.status_code == 200
    body = resp.json()
    assert body["codigo_ibge"] == "3550308"
    # SP: 1 em 30 = 3.33%, mas n_amostra=30 ≥ 5 → não suprimido
    assert body["gestante_baixo_peso_pct"] is not None
    assert body["nivel"] == "baixo"


@pytest.mark.asyncio()
async def test_sentinela_materna_404_sem_dado(client: AsyncClient, db_pronto: None) -> None:
    await _limpar()
    resp = await client.get("/v1/sentinela-materna/3550308")
    assert resp.status_code == 404


@pytest.mark.asyncio()
async def test_sentinela_materna_404_municipio_invalido(
    client: AsyncClient, db_pronto: None
) -> None:
    resp = await client.get("/v1/sentinela-materna/9999999")
    assert resp.status_code == 404
