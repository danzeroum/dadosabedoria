"""IVM municipal — view materializada (O(1) leitura) — ADR-0008

Revision ID: 0010
Revises: 0009
Create Date: 2026-06-05

Índice de Vulnerabilidade Municipal v1: subíndices de emprego (CAGED) e finanças (ESTBAN),
normalizados (min-max por período) e ponderados (50/50). Maior IVM = mais vulnerável. Semáforo:
< 33 verde, 33–66 amarelo, > 66 vermelho.

Pré-computado como MATERIALIZED VIEW (recomputo eliminado, invariante 6). É **aditivo**
(expand-and-contract). Owner = role_analitica para permitir REFRESH pela role de runtime.
"""

from __future__ import annotations

import re

from alembic import op
from sqlalchemy.engine import make_url

from app.core.config import get_settings

revision = "0010"
down_revision = "0009"
branch_labels = None
depends_on = None

_IDENT = re.compile(r"^[a-z_][a-z0-9_]*$")

_MV = """
CREATE MATERIALIZED VIEW ivm_municipio AS
WITH base AS (
  SELECT v.territorio_id, v.periodo,
         max(v.valor) FILTER (WHERE i.codigo = 'trabalho.emprego.saldo_caged') AS saldo_caged,
         max(v.valor) FILTER (WHERE i.codigo = 'credito.operacoes.saldo_total') AS credito
  FROM valor v
  JOIN indicador i ON i.id = v.indicador_id AND i.publico = true
  JOIN territorio t ON t.id = v.territorio_id AND t.nivel = 'municipio'
  WHERE i.codigo IN ('trabalho.emprego.saldo_caged','credito.operacoes.saldo_total')
    AND v.suprimido = false
  GROUP BY v.territorio_id, v.periodo
),
filtrado AS (
  SELECT * FROM base WHERE saldo_caged IS NOT NULL AND credito IS NOT NULL
),
norm AS (
  SELECT territorio_id, periodo,
    CASE WHEN max(saldo_caged) OVER w = min(saldo_caged) OVER w THEN 50.0
         ELSE 100.0 * (saldo_caged - min(saldo_caged) OVER w)
                    / (max(saldo_caged) OVER w - min(saldo_caged) OVER w) END AS n_emprego,
    CASE WHEN max(credito) OVER w = min(credito) OVER w THEN 50.0
         ELSE 100.0 * (credito - min(credito) OVER w)
                    / (max(credito) OVER w - min(credito) OVER w) END AS n_financas
  FROM filtrado
  WINDOW w AS (PARTITION BY periodo)
)
SELECT territorio_id, periodo,
       round((100 - n_emprego)::numeric, 2) AS v_emprego,
       round((100 - n_financas)::numeric, 2) AS v_financas,
       round((0.5*(100-n_emprego) + 0.5*(100-n_financas))::numeric, 2) AS ivm,
       CASE WHEN (0.5*(100-n_emprego) + 0.5*(100-n_financas)) < 33 THEN 'verde'
            WHEN (0.5*(100-n_emprego) + 0.5*(100-n_financas)) <= 66 THEN 'amarelo'
            ELSE 'vermelho' END AS semaforo
FROM norm;
"""


def _role_analitica() -> str:
    nome = make_url(get_settings().database_url).username or ""
    if not _IDENT.match(nome):
        raise RuntimeError(f"Nome de role inválido: {nome!r}")
    return nome


def upgrade() -> None:
    op.execute(_MV)
    # UNIQUE index é requisito do REFRESH ... CONCURRENTLY.
    op.execute("CREATE UNIQUE INDEX idx_ivm_municipio ON ivm_municipio (territorio_id, periodo);")
    # Owner = role_analitica para que o runtime possa dar REFRESH (sem superusuário).
    op.execute(f"ALTER MATERIALIZED VIEW ivm_municipio OWNER TO {_role_analitica()};")


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS ivm_municipio;")
