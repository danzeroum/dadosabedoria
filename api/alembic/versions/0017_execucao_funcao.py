"""execucao_funcao — execução orçamentária por função (OndeFoi/TRANSP-06) — ADR-0029

Revision ID: 0017
Revises: 0016
Create Date: 2026-06-07

Fato **dedicado** da execução por função (Anexo I-E da DCA/SICONFI): território×período×função, com
Empenhado e Liquidado. É **agregado público sem PII** (confirmado no #0/ADR-0028: a fonte não tem
campo de sigilo) → **não** é a fato ``valor`` e **não** passa pela supressão k-anon. A **função é
dimensão** (coluna ``funcao_cod``/``funcao_nome``), não indicador codificado (ADR-0026 §Modelagem).
A role analítica recebe escrita por DEFAULT PRIVILEGES (migração 0009).
"""

from __future__ import annotations

from alembic import op

revision = "0017"
down_revision = "0016"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE execucao_funcao (
          id            bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          territorio_id bigint NOT NULL REFERENCES territorio(id),
          periodo       date   NOT NULL,
          funcao_cod    text   NOT NULL,   -- código Portaria MOG 42/1999 (ex.: '10')
          funcao_nome   text   NOT NULL,   -- nome como a fonte rotula (ex.: 'Saúde')
          empenhado     numeric,
          liquidado     numeric,
          fonte_id      bigint NOT NULL REFERENCES fonte(id),
          carregado_em  timestamptz NOT NULL DEFAULT now(),
          UNIQUE (territorio_id, periodo, funcao_cod)
        );
        """
    )
    op.execute(
        "CREATE INDEX idx_execucao_funcao_terr_per ON execucao_funcao (territorio_id, periodo);"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS execucao_funcao;")
