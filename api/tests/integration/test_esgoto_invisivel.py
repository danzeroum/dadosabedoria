"""Testes de integração — EsgotoInvisível (SANE-03)."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_esgoto_invisivel_404_sem_dado(client: AsyncClient):
    """Município sem dado SNIS retorna 404."""
    r = await client.get("/v1/esgoto-invisivel/9999999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_esgoto_invisivel_404_codigo_invalido(client: AsyncClient):
    """Código IBGE inválido retorna 404."""
    r = await client.get("/v1/esgoto-invisivel/0000000")
    assert r.status_code == 404
