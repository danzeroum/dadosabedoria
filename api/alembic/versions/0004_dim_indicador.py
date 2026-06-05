"""dim indicador (taxonomia + governança PbD/LGPD) — esquema canônico §3.5

Revision ID: 0004
Revises: 0003
Create Date: 2026-06-05
"""

from __future__ import annotations

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE indicador (
          id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          codigo        text NOT NULL UNIQUE,
          nome          text NOT NULL,
          descricao     text NOT NULL,
          dominio       text NOT NULL,
          subdominio    text NOT NULL,
          unidade       text NOT NULL,
          polaridade    polaridade NOT NULL DEFAULT 'neutra',
          atualizacao   periodicidade NOT NULL,

          -- Privacy by Design embutido
          nivel_minimo_agregacao nivel_territorial NOT NULL,
          n_minimo      integer NOT NULL DEFAULT 0,
          classificacao classificacao_dado NOT NULL DEFAULT 'nao_pessoal',
          origem_sensivel boolean NOT NULL DEFAULT false,
          publico       boolean NOT NULL DEFAULT true,

          -- Transparência / proveniência
          base_legal_id bigint NOT NULL REFERENCES base_legal(id),
          fonte_id      bigint NOT NULL REFERENCES fonte(id),
          codigo_externo text,
          metodologia   text NOT NULL,
          versao_metodologia text NOT NULL DEFAULT 'v1'
        );
        """
    )
    op.execute("CREATE INDEX idx_indicador_dominio ON indicador (dominio, subdominio);")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS indicador;")
