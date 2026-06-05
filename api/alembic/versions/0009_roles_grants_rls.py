"""roles + grants + RLS — política de isolamento de PII (§8.1)

Revision ID: 0009
Revises: 0008
Create Date: 2026-06-05

Coração do isolamento de PII. Cria duas roles distintas e tranca o schema ``app``:

- ``role_analitica`` (api/worker/ai): USAGE + SELECT/INSERT/UPDATE em ``public``; **REVOKE ALL**
  em ``app`` (não tem nem USAGE — não consegue resolver ``app.*``).
- ``role_consentimento`` (serviço de consentimento): ÚNICA com acesso a ``app``; só leitura nas
  dimensões que referencia; sem escrita no acervo analítico.

Os nomes e senhas das roles vêm das connection strings (``DATABASE_URL`` / ``CONSENT_DATABASE_URL``)
— as DSNs são a fonte única, evitando divergência. Roles são globais ao cluster, então CREATE é
guardado por ``pg_roles`` (re-run-safe). Rodado pelo migrator como superusuário.
"""

from __future__ import annotations

import re

from alembic import op
from sqlalchemy.engine import make_url

from app.core.config import get_settings

revision = "0009"
down_revision = "0008"
branch_labels = None
depends_on = None

_IDENT = re.compile(r"^[a-z_][a-z0-9_]*$")


def _role_e_senha(url_str: str, papel: str) -> tuple[str, str]:
    url = make_url(url_str)
    nome = url.username or ""
    senha = url.password or ""
    if not _IDENT.match(nome):
        raise RuntimeError(f"Nome de role inválido em {papel}: {nome!r}")
    if not senha:
        raise RuntimeError(f"Senha ausente na connection string de {papel} ({papel}).")
    return nome, senha


def upgrade() -> None:
    settings = get_settings()
    if not settings.consent_database_url:
        raise RuntimeError(
            "CONSENT_DATABASE_URL é obrigatória para a migração 0009 (política de PII §8.1)."
        )
    r_anal, s_anal = _role_e_senha(settings.database_url, "analitica")
    r_cons, s_cons = _role_e_senha(settings.consent_database_url, "consentimento")

    s_anal_q = s_anal.replace("'", "''")
    s_cons_q = s_cons.replace("'", "''")

    # --- criação idempotente das roles (globais ao cluster) ---
    op.execute(  # nosec B608 — DDL de bootstrap; identificador validado, senha de env e escapada
        f"""
        DO $$ BEGIN
          IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{r_anal}') THEN
            CREATE ROLE {r_anal} LOGIN PASSWORD '{s_anal_q}';
          END IF;
          IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{r_cons}') THEN
            CREATE ROLE {r_cons} LOGIN PASSWORD '{s_cons_q}';
          END IF;
        END $$;
        """
    )

    # --- role_analitica: leitura/escrita só no acervo analítico (public) ---
    op.execute(f"GRANT USAGE ON SCHEMA public TO {r_anal};")
    op.execute(f"GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO {r_anal};")
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA public "
        f"GRANT SELECT, INSERT, UPDATE ON TABLES TO {r_anal};"
    )

    # --- ISOLAMENTO DURO de role_analitica do schema app (explícito + testado) ---
    op.execute(f"REVOKE ALL ON ALL TABLES IN SCHEMA app FROM {r_anal};")
    op.execute(f"REVOKE ALL ON SCHEMA app FROM {r_anal};")
    op.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA app REVOKE ALL ON TABLES FROM {r_anal};")
    # Defesa em profundidade: nada de grant implícito a PUBLIC no schema app.
    op.execute("REVOKE ALL ON ALL TABLES IN SCHEMA app FROM PUBLIC;")
    op.execute("REVOKE ALL ON SCHEMA app FROM PUBLIC;")

    # --- role_consentimento: ÚNICA com acesso a app; só leitura nas dimensões que referencia ---
    op.execute(f"GRANT USAGE ON SCHEMA app TO {r_cons};")
    op.execute(f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA app TO {r_cons};")
    op.execute(
        f"ALTER DEFAULT PRIVILEGES IN SCHEMA app "
        f"GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {r_cons};"
    )
    op.execute(f"GRANT USAGE ON SCHEMA public TO {r_cons};")
    op.execute(f"GRANT SELECT ON territorio, base_legal TO {r_cons};")

    # --- RLS nas tabelas de app (segunda camada; USAGE é a tranca primária) ---
    for tabela in ("assinante_alerta", "condicao_sensivel"):
        op.execute(f"ALTER TABLE app.{tabela} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE app.{tabela} FORCE ROW LEVEL SECURITY;")
        op.execute(f"DROP POLICY IF EXISTS p_consent_{tabela} ON app.{tabela};")
        op.execute(
            f"""
            CREATE POLICY p_consent_{tabela} ON app.{tabela}
              USING (current_user = '{r_cons}')
              WITH CHECK (current_user = '{r_cons}');
            """
        )


def downgrade() -> None:
    settings = get_settings()
    for tabela in ("assinante_alerta", "condicao_sensivel"):
        op.execute(f"DROP POLICY IF EXISTS p_consent_{tabela} ON app.{tabela};")
    # Não removemos roles globais nem revogamos grants num downgrade (poderiam ser compartilhadas);
    # o downgrade do schema app (0008) já remove as tabelas.
    _ = settings
