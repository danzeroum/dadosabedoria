"""Testes de integração do endpoint GET /v1/prato-frio/{codigo_ibge} (ALIM-01)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio()
async def test_prato_frio_200_sp(client: AsyncClient) -> None:
    resp = await client.get("/v1/prato-frio/3550308")
    assert resp.status_code == 200
    body = resp.json()
    assert body["codigo_ibge"] == "3550308"
    assert body["nome"] == "São Paulo"
    assert body["valor_total"] is not None
    assert body["nivel"] in ("alta", "moderada", "baixa", "sem_dado")
    assert body["nota"] != ""
    assert "meta" in body


@pytest.mark.asyncio()
async def test_prato_frio_200_campinas(client: AsyncClient) -> None:
    resp = await client.get("/v1/prato-frio/3509502")
    assert resp.status_code == 200
    body = resp.json()
    assert body["codigo_ibge"] == "3509502"
    # seed: 10.000.000 BRL
    assert abs(body["valor_total"] - 10_000_000.0) < 1.0
    assert body["nivel"] in ("alta", "moderada", "baixa", "sem_dado")


@pytest.mark.asyncio()
async def test_prato_frio_404_sem_dado(client: AsyncClient) -> None:
    resp = await client.get("/v1/prato-frio/5300108")  # Brasília: sem dado no seed
    assert resp.status_code == 404


@pytest.mark.asyncio()
async def test_prato_frio_404_ibge_invalido(client: AsyncClient) -> None:
    resp = await client.get("/v1/prato-frio/9999999")
    assert resp.status_code == 404
