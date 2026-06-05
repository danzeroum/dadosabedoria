"""Migrator one-shot: ``python -m app.migrate``.

1. ``alembic upgrade head`` como SUPERUSUÁRIO (cria schema, roles, grants, RLS).
2. ``python -m app.seed`` como ``role_analitica`` (exercita os grants de escrita analítica e
   prova, na prática, que a role analítica grava em ``public`` mas não toca ``app``).

O contêiner ``api`` espera este processo concluir (``service_completed_successfully``) antes de
servir — nunca atende sem schema + seed prontos.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.seed import main as seed_main

_API_ROOT = Path(__file__).resolve().parent.parent


def _alembic_config() -> Config:
    cfg = Config(str(_API_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(_API_ROOT / "alembic"))
    return cfg


def main() -> None:
    print("migrate: alembic upgrade head ...")  # noqa: T201
    command.upgrade(_alembic_config(), "head")
    print("migrate: seed ...")  # noqa: T201
    asyncio.run(seed_main())
    print("migrate: ok")  # noqa: T201


if __name__ == "__main__":
    main()
