"""dim base_legal + fonte (esquema canônico §3.2, §3.3)

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-05
"""

from __future__ import annotations

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE base_legal (
          id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          codigo        text NOT NULL UNIQUE,
          artigo        text NOT NULL,
          hipotese      text NOT NULL,
          justificativa text NOT NULL
        );
        """
    )
    op.execute(
        """
        CREATE TABLE fonte (
          id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          codigo        text NOT NULL UNIQUE,
          nome          text NOT NULL,
          orgao         text NOT NULL,
          url_doc       text,
          licenca       text NOT NULL,
          permite_uso_comercial   boolean NOT NULL DEFAULT true,
          permite_redistribuicao  boolean NOT NULL DEFAULT true,
          atualizacao   periodicidade NOT NULL,
          lag_tipico_dias smallint,
          base_legal_id bigint NOT NULL REFERENCES base_legal(id),
          observacoes   text
        );
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS fonte;")
    op.execute("DROP TABLE IF EXISTS base_legal;")
