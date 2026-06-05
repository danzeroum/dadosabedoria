"""fato valor (grão território×período; sem chave de pessoa) — esquema canônico §3.6

Revision ID: 0005
Revises: 0004
Create Date: 2026-06-05
"""

from __future__ import annotations

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE valor (
          id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          indicador_id  bigint NOT NULL REFERENCES indicador(id),
          territorio_id bigint NOT NULL REFERENCES territorio(id),
          periodo       date    NOT NULL,
          atualizacao   periodicidade NOT NULL,
          valor         numeric,

          -- Privacy by Design
          n_amostra     integer,
          suprimido     boolean NOT NULL DEFAULT false,
          motivo_supressao text,

          -- Qualidade / transparência
          confiabilidade smallint CHECK (confiabilidade BETWEEN 1 AND 5),
          ic_inferior   numeric,
          ic_superior   numeric,
          fonte_id      bigint NOT NULL REFERENCES fonte(id),
          versao        smallint NOT NULL DEFAULT 1,
          carregado_em  timestamptz NOT NULL DEFAULT now(),

          UNIQUE (indicador_id, territorio_id, periodo, versao)
        );
        """
    )
    op.execute("CREATE INDEX idx_valor_busca ON valor (indicador_id, territorio_id, periodo);")
    op.execute("CREATE INDEX idx_valor_territorio_periodo ON valor (territorio_id, periodo);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS valor;")
