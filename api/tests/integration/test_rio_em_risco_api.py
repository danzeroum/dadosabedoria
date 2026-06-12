"""Testes de integração do endpoint GET /v1/rio-em-risco/{codigo_ibge} (SANE-02)."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio()
async def test_rio_em_risco_200_com_seed(client: AsyncClient) -> None:
    resp = await client.get("/v1/rio-em-risco/3550308")
    assert resp.status_code == 200
    body = resp.json()
    assert body["codigo_ibge"] == "3550308"
    assert body["nome"] == "São Paulo"
    # seca_indice pode ser o valor do seed (0.0) ou do pipeline ANA (2.0) dependendo da ordem
    assert body["seca_indice"] is not None
    assert 0.0 <= body["seca_indice"] <= 5.0
    assert body["nivel"] in ("normal", "atencao", "critico")
    assert body["nota"] != ""
    assert "meta" in body


@pytest.mark.asyncio()
async def test_rio_em_risco_200_campinas(client: AsyncClient) -> None:
    resp = await client.get("/v1/rio-em-risco/3509502")
    assert resp.status_code == 200
    body = resp.json()
    assert body["codigo_ibge"] == "3509502"
    assert body["seca_indice"] == pytest.approx(1.0)
    assert body["nivel"] == "atencao"


@pytest.mark.asyncio()
async def test_rio_em_risco_404_sem_dado(client: AsyncClient) -> None:
    resp = await client.get("/v1/rio-em-risco/5300108")  # Brasília: sem dado no seed
    assert resp.status_code == 404


@pytest.mark.asyncio()
async def test_rio_em_risco_404_ibge_invalido(client: AsyncClient) -> None:
    resp = await client.get("/v1/rio-em-risco/9999999")
    assert resp.status_code == 404
