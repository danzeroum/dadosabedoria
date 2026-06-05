"""view valor_publico (Privacy by Default + open-core) — esquema canônico §3.6

Revision ID: 0006
Revises: 0005
Create Date: 2026-06-05
"""

from __future__ import annotations

from alembic import op

revision = "0006"
down_revision = "0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Só agregado, indicador publico=true e não suprimido. Privacy by Default estrutural.
    op.execute(
        """
        CREATE OR REPLACE VIEW valor_publico AS
        SELECT v.indicador_id, v.territorio_id, v.periodo, v.valor,
               v.confiabilidade, v.suprimido, v.motivo_supressao
        FROM   valor v
        JOIN   indicador i ON i.id = v.indicador_id
        WHERE  i.publico = true
          AND  v.suprimido = false;
        """
    )


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS valor_publico;")
