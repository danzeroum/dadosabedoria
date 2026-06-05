"""Ambiente Alembic — modo ASSÍNCRONO, conectando como SUPERUSUÁRIO (migrator).

A connection string vem de ``ADMIN_DATABASE_URL`` (cai para ``DATABASE_URL`` se ausente, útil
em dev). Autogenerate está desligado: ``target_metadata = None`` — todas as migrações são DDL
escrito à mão a partir do esquema canônico (ADR-0003).
"""

from __future__ import annotations

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import get_settings

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Autogenerate OFF — o schema é definido à mão (fonte da verdade: esquema canônico).
target_metadata = None


def _url() -> str:
    settings = get_settings()
    return settings.admin_database_url or settings.database_url


def do_run_migrations(connection) -> None:  # noqa: ANN001
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    engine = create_async_engine(_url(), future=True)
    async with engine.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await engine.dispose()


def run_migrations_offline() -> None:
    context.configure(url=_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_async_migrations())
