"""Fixtures de teste.

Os testes de unidade (supressão, single-call-site, compose) NÃO precisam de banco. Os de
integração exigem Postgres+PostGIS vivo via ``ADMIN_DATABASE_URL`` / ``DATABASE_URL`` /
``CONSENT_DATABASE_URL`` — se ausentes, são pulados.
"""

from __future__ import annotations

import contextlib
import os
from collections.abc import AsyncIterator, Iterator

import pytest


@pytest.fixture(scope="session")
def db_pronto() -> Iterator[None]:
    """Roda migrações (admin) + seed (role_analitica) uma vez por sessão de testes."""
    if not os.getenv("ADMIN_DATABASE_URL"):
        pytest.skip("integração requer ADMIN_DATABASE_URL/DATABASE_URL/CONSENT_DATABASE_URL")
    from app.core.config import get_settings

    get_settings.cache_clear()
    from app.migrate import main as migrate_main

    migrate_main()
    yield


@pytest.fixture
async def client(db_pronto: None) -> AsyncIterator[object]:
    from httpx import ASGITransport, AsyncClient

    from app.core.cache import fechar_redis, get_redis
    from app.core.db import dispose_engine
    from app.main import app

    with contextlib.suppress(Exception):  # começa com cache limpo (determinismo)
        await get_redis().flushdb()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

    # ASGITransport não roda o lifespan: liberar engine/redis (singletons) por teste evita
    # reuso de conexões presas a um event loop já fechado.
    await dispose_engine()
    await fechar_redis()


@pytest.fixture
async def consent_client(db_pronto: None) -> AsyncIterator[object]:
    """Cliente do serviço ISOLADO de consentimento (role_consentimento)."""
    from httpx import ASGITransport, AsyncClient

    from app.consentimento.db import dispose_consent_engine
    from app.consentimento.server import app as consent_app

    async with AsyncClient(transport=ASGITransport(app=consent_app), base_url="http://test") as c:
        yield c
    await dispose_consent_engine()
