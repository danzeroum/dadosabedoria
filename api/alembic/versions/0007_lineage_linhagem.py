"""linhagem (proveniência / auditoria) — esquema canônico §3.7

Revision ID: 0007
Revises: 0006
Create Date: 2026-06-05
"""

from __future__ import annotations

from alembic import op

revision = "0007"
down_revision = "0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE linhagem (
          id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          fonte_id      bigint NOT NULL REFERENCES fonte(id),
          indicador_id  bigint REFERENCES indicador(id),
          executado_em  timestamptz NOT NULL DEFAULT now(),
          url_extracao  text,
          hash_origem   text,
          transformacoes text,
          registros_carregados integer,
          responsavel   text
        );
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS linhagem;")
