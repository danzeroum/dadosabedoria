"""trilha de auditoria do schema app (§8.1.5)

Revision ID: 0011
Revises: 0010
Create Date: 2026-06-05

Toda operação no schema ``app`` (assinar/listar/revogar/eliminar) é registrada aqui. A tabela é
isolada como as demais do ``app``: RLS + policy só para ``role_consentimento``; ``role_analitica``
não tem acesso (default privileges revogados em 0009 cobrem a tabela nova automaticamente).
"""

from __future__ import annotations

import re

from alembic import op
from sqlalchemy.engine import make_url

from app.core.config import get_settings

revision = "0011"
down_revision = "0010"
branch_labels = None
depends_on = None

_IDENT = re.compile(r"^[a-z_][a-z0-9_]*$")


def _role_consentimento() -> str:
    settings = get_settings()
    if not settings.consent_database_url:
        raise RuntimeError("CONSENT_DATABASE_URL é obrigatória para a migração 0011.")
    nome = make_url(settings.consent_database_url).username or ""
    if not _IDENT.match(nome):
        raise RuntimeError(f"Nome de role inválido: {nome!r}")
    return nome


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE app.auditoria_acesso (
          id       bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          quando   timestamptz NOT NULL DEFAULT now(),
          ator     text NOT NULL,   -- hash do cidadão ou 'sistema'
          acao     text NOT NULL,   -- 'assinar','listar','revogar','eliminar'
          recurso  text NOT NULL,
          detalhe  text
        );
        """
    )
    r_cons = _role_consentimento()
    op.execute("ALTER TABLE app.auditoria_acesso ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE app.auditoria_acesso FORCE ROW LEVEL SECURITY;")
    op.execute("DROP POLICY IF EXISTS p_consent_auditoria ON app.auditoria_acesso;")
    op.execute(
        f"""
        CREATE POLICY p_consent_auditoria ON app.auditoria_acesso
          USING (current_user = '{r_cons}')
          WITH CHECK (current_user = '{r_cons}');
        """
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS app.auditoria_acesso;")
