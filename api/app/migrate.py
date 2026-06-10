"""Migrator one-shot: ``python -m app.migrate``.

1. Validação de pre-flight: verifica variáveis obrigatórias antes de tentar conectar.
2. ``alembic upgrade head`` como SUPERUSUÁRIO (cria schema, roles, grants, RLS).
3. ``python -m app.seed`` como ``role_analitica`` (exercita os grants de escrita analítica e
   prova, na prática, que a role analítica grava em ``public`` mas não toca ``app``).

O contêiner ``api`` espera este processo concluir (``service_completed_successfully``) antes de
servir — nunca atende sem schema + seed prontos.
"""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

from alembic import command
from alembic.config import Config

from app.seed import main as seed_main

_API_ROOT = Path(__file__).resolve().parent.parent

_REQUIRED = [
    "ADMIN_DATABASE_URL",
    "DATABASE_URL",
]
_PLACEHOLDER = "change_me"


def _preflight() -> None:
    errors: list[str] = []
    for var in _REQUIRED:
        val = os.environ.get(var, "")
        if not val:
            errors.append(f"  {var} — não definida")
        elif _PLACEHOLDER in val:
            errors.append(f"  {var} — ainda tem o valor placeholder; troque pelo valor real")
    if errors:
        print("migrate: ERRO de pre-flight — variáveis obrigatórias inválidas:", file=sys.stderr)  # noqa: T201
        for e in errors:
            print(e, file=sys.stderr)  # noqa: T201
        print("  Corrija o .env e reinicie o contêiner.", file=sys.stderr)  # noqa: T201
        sys.exit(1)


def _alembic_config() -> Config:
    cfg = Config(str(_API_ROOT / "alembic.ini"))
    cfg.set_main_option("script_location", str(_API_ROOT / "alembic"))
    return cfg


def main() -> None:
    _preflight()
    print("migrate: alembic upgrade head ...")  # noqa: T201
    command.upgrade(_alembic_config(), "head")
    print("migrate: seed ...")  # noqa: T201
    asyncio.run(seed_main())
    print("migrate: ok")  # noqa: T201


if __name__ == "__main__":
    main()
