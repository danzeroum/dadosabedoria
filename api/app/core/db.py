"""Acesso ao banco — SQLAlchemy 2.0 async (engine/sessão) sobre ``role_analitica``.

Decisão (ADR-0003): leitura via SQLAlchemy **Core** (sem ORM declarativo) — consultas
parametrizadas, explícitas e auditáveis (zero SQL concatenado, §8), sem identity-map/lazy-load
(evita N+1). As definições de schema vivem nas migrações Alembic (fonte da verdade), não aqui.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncConnection,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

_engine: AsyncEngine | None = None
_sessionmaker: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Engine singleton da role analítica (com pool — economia de recurso, invariante 6)."""
    global _engine
    if _engine is None:
        settings = get_settings()
        _engine = create_async_engine(
            settings.database_url,
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=5,
            future=True,
        )
    return _engine


def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    global _sessionmaker
    if _sessionmaker is None:
        _sessionmaker = async_sessionmaker(get_engine(), expire_on_commit=False)
    return _sessionmaker


async def get_session() -> AsyncIterator[AsyncSession]:
    """Dependency FastAPI: uma sessão por request."""
    async with get_sessionmaker()() as session:
        yield session


@asynccontextmanager
async def connect(url: str) -> AsyncIterator[AsyncConnection]:
    """Conexão pontual a uma URL arbitrária (usada por seed/migrator com outra role)."""
    engine = create_async_engine(url, future=True)
    try:
        async with engine.begin() as conn:
            yield conn
    finally:
        await engine.dispose()


async def dispose_engine() -> None:
    global _engine, _sessionmaker
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _sessionmaker = None
