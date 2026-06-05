"""Sessão do serviço de consentimento — conecta como ``role_consentimento`` (única com acesso a
``app``), via ``CONSENT_DATABASE_URL``. Engine SEPARADA da analítica (invariante 2)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def _get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        url = get_settings().consent_database_url
        if not url:
            raise RuntimeError("CONSENT_DATABASE_URL não configurada (serviço de consentimento).")
        _engine = create_async_engine(
            url, pool_pre_ping=True, pool_size=3, max_overflow=3, future=True
        )
    return _engine


def _maker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(_get_engine(), expire_on_commit=False)
    return _sessionmaker


@asynccontextmanager
async def consent_session() -> AsyncIterator[AsyncSession]:
    """Unit-of-work (commit no sucesso, rollback no erro). Usável fora do FastAPI (ex.: CLI)."""
    async with _maker()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_consent_session() -> AsyncIterator[AsyncSession]:
    """Dependency do FastAPI — delega ao unit-of-work ``consent_session``."""
    async with consent_session() as session:
        yield session


async def dispose_consent_engine() -> None:
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _sessionmaker = None
