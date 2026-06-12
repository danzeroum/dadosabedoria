"""Teste de integração: endpoint /v1/agua-viva/{ibge} com banco real."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_agua_viva_sem_dado(client: AsyncClient):
    """404 quando município não tem dado SNIS."""
    r = await client.get("/v1/agua-viva/3550308")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_agua_viva_municipio_invalido(client: AsyncClient):
    """404 quando código IBGE não existe."""
    r = await client.get("/v1/agua-viva/0000000")
    assert r.status_code == 404
