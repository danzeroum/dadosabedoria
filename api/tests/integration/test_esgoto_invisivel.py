"""Testes de integração — EsgotoInvisível (SANE-03)."""

import pytest

pytestmark = pytest.mark.skipif(
    not __import__("os").environ.get("ADMIN_DATABASE_URL"),
    reason="integração requer ADMIN_DATABASE_URL/DATABASE_URL/CONSENT_DATABASE_URL",
)


@pytest.mark.integration
async def test_esgoto_invisivel_404_sem_dado(async_client):
    """Município sem dado SNIS retorna 404."""
    res = await async_client.get("/v1/esgoto-invisivel/9999999")
    assert res.status_code == 404


@pytest.mark.integration
async def test_esgoto_invisivel_404_codigo_invalido(async_client):
    """Código IBGE inválido retorna 404."""
    res = await async_client.get("/v1/esgoto-invisivel/0000000")
    assert res.status_code == 404
