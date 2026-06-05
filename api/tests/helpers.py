"""Utilidades de teste."""

from __future__ import annotations

from sqlalchemy.engine import make_url


def asyncpg_dsn(url: str) -> str:
    """Converte uma URL SQLAlchemy (``postgresql+asyncpg://``) em DSN do asyncpg."""
    u = make_url(url)
    return f"postgresql://{u.username}:{u.password}@{u.host}:{u.port or 5432}/{u.database}"
