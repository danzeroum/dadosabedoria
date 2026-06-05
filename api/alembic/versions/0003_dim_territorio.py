"""dim territorio (PostGIS, hierárquico) — esquema canônico §3.4

Revision ID: 0003
Revises: 0002
Create Date: 2026-06-05
"""

from __future__ import annotations

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE territorio (
          id          bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          codigo_ibge text NOT NULL UNIQUE,
          nome        text NOT NULL,
          nivel       nivel_territorial NOT NULL,
          pai_id      bigint REFERENCES territorio(id),
          uf          char(2),
          populacao   integer,
          geom        geometry(MultiPolygon, 4674)   -- SIRGAS 2000 (malhas IBGE)
        );
        """
    )
    op.execute("CREATE INDEX idx_territorio_geom ON territorio USING gist (geom);")
    op.execute("CREATE INDEX idx_territorio_nivel ON territorio (nivel);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS territorio;")
