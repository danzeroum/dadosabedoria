"""notificações de alerta (consumo do IVM) no schema app — ADR-0014

Revision ID: 0013
Revises: 0012
Create Date: 2026-06-05

Fecha o ciclo do consentimento: quando o IVM de um território entra em **vermelho**, o serviço de
consentimento (única identidade com acesso ao ``app``) casa o evento com os assinantes daquele
território e grava uma ``app.notificacao`` (entrega *pull*: o cidadão a recupera autenticado — o
contato bruto nunca é guardado, só o pseudônimo). A notificação carrega **proveniência** (fonte,
método) do evento.

Isolamento §8.1: a tabela é isolada como as demais do ``app`` (RLS + policy só p/
role_consentimento; default privileges de 0009 cobrem o REVOKE de role_analitica). A novidade é uma
leitura ESTREITA na direção benigna: role_consentimento ganha ``SELECT`` na MV pública
``ivm_municipio`` (dado público, sem PII) para casar evento×assinante. A direção crítica
(analítica → ``app``) segue NEGADA e testada.
"""

from __future__ import annotations

import re

from alembic import op
from sqlalchemy.engine import make_url

from app.core.config import get_settings

revision = "0013"
down_revision = "0012"
branch_labels = None
depends_on = None

_IDENT = re.compile(r"^[a-z_][a-z0-9_]*$")


def _role(url_str: str | None, papel: str) -> str:
    if not url_str:
        raise RuntimeError(f"DSN da role {papel} ausente na migração 0013.")
    nome = make_url(url_str).username or ""
    if not _IDENT.match(nome):
        raise RuntimeError(f"Nome de role inválido ({papel}): {nome!r}")
    return nome


def upgrade() -> None:
    op.execute(
        """
        CREATE TABLE app.notificacao (
          id           bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
          assinante_id bigint NOT NULL REFERENCES app.assinante_alerta(id) ON DELETE CASCADE,
          periodo      date NOT NULL,
          ivm          numeric(6,2) NOT NULL,
          semaforo     text NOT NULL,
          fonte        text NOT NULL,    -- proveniência (invariante 5)
          metodologia  text NOT NULL,
          criada_em    timestamptz NOT NULL DEFAULT now(),
          lida_em      timestamptz,
          UNIQUE (assinante_id, periodo)  -- idempotência: 1 notificação por assinante/período
        );
        """
    )
    s = get_settings()
    r_cons = _role(s.consent_database_url, "consentimento")

    # Isolamento: RLS + policy só p/ role_consentimento (mesma trava das outras tabelas de app).
    op.execute("ALTER TABLE app.notificacao ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE app.notificacao FORCE ROW LEVEL SECURITY;")
    op.execute("DROP POLICY IF EXISTS p_consent_notificacao ON app.notificacao;")
    op.execute(
        f"""
        CREATE POLICY p_consent_notificacao ON app.notificacao
          USING (current_user = '{r_cons}')
          WITH CHECK (current_user = '{r_cons}');
        """
    )

    # Leitura estreita do evento público (IVM) para casar evento×assinante DENTRO do serviço de
    # consentimento. role_analitica continua SEM qualquer acesso a app (não tocada aqui).
    op.execute(f"GRANT SELECT ON ivm_municipio TO {r_cons};")


def downgrade() -> None:
    s = get_settings()
    r_cons = _role(s.consent_database_url, "consentimento")
    op.execute(f"REVOKE SELECT ON ivm_municipio FROM {r_cons};")
    op.execute("DROP TABLE IF EXISTS app.notificacao;")
