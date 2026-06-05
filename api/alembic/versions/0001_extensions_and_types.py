"""extensions + enums (esquema canônico §3.1)

Revision ID: 0001
Revises:
Create Date: 2026-06-05
"""

from __future__ import annotations

from alembic import op

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None

# NB: CREATE TYPE não tem IF NOT EXISTS nativo no Postgres → cada ENUM vai num bloco DO guardado
# por pg_type, para a migração ser re-run-safe.
_ENUMS = {
    "periodicidade": "'diaria','semanal','mensal','trimestral','anual','irregular'",
    "nivel_territorial": (
        "'pais','regiao','uf','mesorregiao','microrregiao',"
        "'municipio','distrito','bairro','setor_censitario','bacia'"
    ),
    "classificacao_dado": "'nao_pessoal','pessoal','sensivel'",
    "polaridade": "'maior_melhor','menor_melhor','neutra'",
}


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis;")
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
    for nome, valores in _ENUMS.items():
        op.execute(
            f"""
            DO $$ BEGIN
              IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{nome}') THEN
                CREATE TYPE {nome} AS ENUM ({valores});
              END IF;
            END $$;
            """
        )


def downgrade() -> None:
    for nome in _ENUMS:
        op.execute(f"DROP TYPE IF EXISTS {nome};")
    # extensões não são removidas (podem ser compartilhadas).
