"""leitura das sequences (existentes/futuras) p/ backup como role de menor privilégio

Revision ID: 0012
Revises: 0011
Create Date: 2026-06-05

O runbook roda cada ``pg_dump`` COMO a role de menor privilégio daquela classe (defesa em
profundidade):
- acervo analítico → ``role_analitica`` (que estruturalmente NÃO lê ``app``);
- PII (schema ``app``) → ``role_consentimento`` (única identidade com acesso a ``app``).

Para um dump consistente, o pg_dump lê o estado das sequences das colunas ``GENERATED ALWAYS AS
IDENTITY`` (``SELECT last_value …``), o que exige ``SELECT`` na sequence. Concede SÓ leitura — nas
sequences existentes e futuras — de cada role no SEU schema. Nada cruza a fronteira §8.1:
``role_analitica`` segue sem qualquer acesso a ``app`` (continua testado).
"""

from __future__ import annotations

import re

from alembic import op
from sqlalchemy.engine import make_url

from app.core.config import get_settings

revision = "0012"
down_revision = "0011"
branch_labels = None
depends_on = None

_IDENT = re.compile(r"^[a-z_][a-z0-9_]*$")


def _role(url_str: str | None, papel: str) -> str:
    if not url_str:
        raise RuntimeError(f"DSN da role {papel} ausente na migração 0012.")
    nome = make_url(url_str).username or ""
    if not _IDENT.match(nome):
        raise RuntimeError(f"Nome de role inválido ({papel}): {nome!r}")
    return nome


def upgrade() -> None:
    s = get_settings()
    r_anal = _role(s.database_url, "analitica")
    r_cons = _role(s.consent_database_url, "consentimento")

    # role_analitica lê as sequences de `public` (acervo analítico) — nada de `app`.
    op.execute(f"GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO {r_anal};")
    op.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON SEQUENCES TO {r_anal};")

    # role_consentimento lê as sequences de `app` (PII) — segue isolada do acervo analítico.
    op.execute(f"GRANT SELECT ON ALL SEQUENCES IN SCHEMA app TO {r_cons};")
    op.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT SELECT ON SEQUENCES TO {r_cons};")


def downgrade() -> None:
    s = get_settings()
    r_anal = _role(s.database_url, "analitica")
    r_cons = _role(s.consent_database_url, "consentimento")

    op.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA app REVOKE SELECT ON SEQUENCES FROM {r_cons};")
    op.execute(f"REVOKE SELECT ON ALL SEQUENCES IN SCHEMA app FROM {r_cons};")
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA public REVOKE SELECT ON SEQUENCES FROM {r_anal};"
    )
    op.execute(f"REVOKE SELECT ON ALL SEQUENCES IN SCHEMA public FROM {r_anal};")
