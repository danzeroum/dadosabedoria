"""schema `app` isolado (dados pessoais, só com consentimento) — esquema canônico §6

Revision ID: 0008
Revises: 0007
Create Date: 2026-06-05
"""

from __future__ import annotations

from alembic import op

revision = "0008"
down_revision = "0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS app;")
    # Dado PESSOAL: base legal = consentimento (Art. 7, I). Contato pseudonimizado (pgcrypto).
    op.execute(
        """
        CREATE TABLE app.assinante_alerta (
          id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          contato_hash    text NOT NULL,
          territorio_id   bigint NOT NULL REFERENCES territorio(id),
          finalidade      text NOT NULL,
          base_legal_id   bigint NOT NULL REFERENCES base_legal(id),
          consentido_em   timestamptz NOT NULL,
          revogado_em     timestamptz
        );
        """
    )
    # Dado SENSÍVEL (saúde): consentimento específico e destacado (Art. 11, I).
    op.execute(
        """
        CREATE TABLE app.condicao_sensivel (
          id              bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          assinante_id    bigint NOT NULL REFERENCES app.assinante_alerta(id) ON DELETE CASCADE,
          tipo            text NOT NULL,
          base_legal_id   bigint NOT NULL REFERENCES base_legal(id),
          consentido_em   timestamptz NOT NULL
        );
        """
    )


def downgrade() -> None:
    op.execute("DROP SCHEMA IF EXISTS app CASCADE;")
