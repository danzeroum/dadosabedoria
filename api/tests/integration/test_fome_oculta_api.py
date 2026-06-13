"""Integração do endpoint GET /v1/fome-oculta/{codigo_ibge} (ALIM-02).

Semeia a tabela valor diretamente para controlar o dado de baixo_peso_pct.
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import connect
from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.sisvan import AdaptadorSisvan
from app.ingestao.bronze import ArmazenamentoMemoria
from app.ingestao.pipeline import executar_sisvan
from tests.fixtures.sisvan import AMOSTRA, FetcherFake

pytestmark = pytest.mark.integration

_DELETE = text(
    "DELETE FROM valor v USING indicador i "
    "WHERE i.id = v.indicador_id AND i.codigo = 'alimentacao.nutricao.baixo_peso_pct'"
)


async def _limpar_e_semear() -> None:
    async with connect(get_settings().database_url) as conn:
        await conn.execute(_DELETE)
        adaptador = AdaptadorSisvan(FetcherFake(AMOSTRA))
        await executar_sisvan(
            Janela(2023, 1), conn, adaptador, ArmazenamentoMemoria(), responsavel="test"
        )


@pytest.mark.asyncio()
async def test_fome_oculta_200_campinas(client: AsyncClient, db_pronto: None) -> None:
    await _limpar_e_semear()
    resp = await client.get("/v1/fome-oculta/3509502")
    assert resp.status_code == 200
    body = resp.json()
    assert body["codigo_ibge"] == "3509502"
    assert body["nome"] == "Campinas"
    assert abs(body["baixo_peso_pct"] - 5.0) < 0.01
    assert body["nivel"] == "elevado"
    assert body["n_acompanhadas"] == 20
    assert body["ano"] == 2023
    assert body["nota"] != ""


@pytest.mark.asyncio()
async def test_fome_oculta_200_sp(client: AsyncClient, db_pronto: None) -> None:
    await _limpar_e_semear()
    resp = await client.get("/v1/fome-oculta/3550308")
    assert resp.status_code == 200
    body = resp.json()
    assert body["codigo_ibge"] == "3550308"
    assert abs(body["baixo_peso_pct"] - 2.0) < 0.01
    assert body["nivel"] == "moderado"


@pytest.mark.asyncio()
async def test_fome_oculta_404_sem_dado(client: AsyncClient, db_pronto: None) -> None:
    async with connect(get_settings().database_url) as conn:
        await conn.execute(_DELETE)
    resp = await client.get("/v1/fome-oculta/3550308")
    assert resp.status_code == 404


@pytest.mark.asyncio()
async def test_fome_oculta_404_municipio_invalido(client: AsyncClient, db_pronto: None) -> None:
    resp = await client.get("/v1/fome-oculta/9999999")
    assert resp.status_code == 404
