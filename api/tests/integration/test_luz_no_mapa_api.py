"""Teste de integração: endpoint /v1/luz-no-mapa/{ibge} com banco real."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_luz_no_mapa_com_seed(client: AsyncClient) -> None:
    """Seed semeia DEC/FEC para SP (3550308) — espera 200 com níveis confiavel."""
    r = await client.get("/v1/luz-no-mapa/3550308")
    assert r.status_code == 200
    data = r.json()
    assert data["codigo_ibge"] == "3550308"
    assert data["dec"] == pytest.approx(3.52, abs=0.01)
    assert data["nivel_dec"] == "confiavel"
    assert data["nivel_fec"] == "confiavel"
    assert "nota" in data


@pytest.mark.asyncio
async def test_luz_no_mapa_sem_dado(client: AsyncClient) -> None:
    """404 quando município não tem dado ANEEL."""
    r = await client.get("/v1/luz-no-mapa/9999999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_luz_no_mapa_municipio_invalido(client: AsyncClient) -> None:
    """404 quando código IBGE não existe."""
    r = await client.get("/v1/luz-no-mapa/0000000")
    assert r.status_code == 404
