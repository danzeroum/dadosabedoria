"""chaves de API do tier profundo (open-core pago) — emissão/revogação por cliente — ADR-0020

Revision ID: 0014
Revises: 0013
Create Date: 2026-06-06

Credencial de CLIENTE (B2G/B2B), **não** PII — vive no acervo analítico (`public`). Guarda-se só o
**SHA-256** da chave. Least-privilege: a `api` (role_analitica) só **lê** para validar; emissão e
revogação são do **admin** (REVOKE de escrita para a role analítica nesta tabela).
"""

from __future__ import annotations

import re

from alembic import op
from sqlalchemy.engine import make_url

from app.core.config import get_settings

revision = "0014"
down_revision = "0013"
branch_labels = None
depends_on = None

_IDENT = re.compile(r"^[a-z_][a-z0-9_]*$")


def _role_analitica() -> str:
    nome = make_url(get_settings().database_url).username or ""
    if not _IDENT.match(nome):
        raise RuntimeError(f"Nome de role inválido: {nome!r}")
    return nome


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE chave_api (
          id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          cliente     text NOT NULL,
          chave_hash  text NOT NULL UNIQUE,   -- SHA-256 hex; a chave bruta nunca é gravada
          criada_em   timestamptz NOT NULL DEFAULT now(),
          revogada_em timestamptz
        );
        """
    )
    op.execute(
        "CREATE INDEX idx_chave_api_ativa ON chave_api (chave_hash) WHERE revogada_em IS NULL;"
    )
    # Least-privilege: a role analítica (api) só SELECT; emissão/revogação são do admin.
    op.execute(f"REVOKE INSERT, UPDATE, DELETE ON chave_api FROM {_role_analitica()};")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS chave_api;")
