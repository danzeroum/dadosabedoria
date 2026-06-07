"""IVM: supressão aditiva — acrescenta v_saude_estado à MV (ADR-0026 refino)

Revision ID: 0016
Revises: 0015
Create Date: 2026-06-07

Padrão `*_estado` (igual ao `exe_estado` do OndeFoi, ADR-0026): além de `v_saude` (que é NULL quando
não há valor), a MV passa a expor **`v_saude_estado`** distinguindo, por município×período:
- ``"valor"`` — há célula de saúde não suprimida (v_saude calculado);
- ``"suprimido"`` — há célula, mas k-anon a suprimiu (PII por baixo, ADR-0002 — cadeado legítimo);
- ``"sem_cobertura"`` — não há célula de saúde no período.

Assim a tela distingue *null-por-supressão* de *null-por-cobertura* (supressão honesta). O `base` da
MV filtra ``suprimido = false`` (exclui a célula suprimida), então a distinção vem de um CTE extra
(`saude_cobertura`) que olha as células de saúde **sem** o filtro de supressão.

Aditivo (expand-and-contract, ADR-0003): mantém todas as colunas; ACRESCENTA `v_saude_estado`. MV
recomputada do zero (não há série a preservar). Owner = role_analitica p/ o REFRESH pelo runtime.
"""

from __future__ import annotations

import re

from alembic import op
from sqlalchemy.engine import make_url

from app.core.config import get_settings

revision = "0016"
down_revision = "0015"
branch_labels = None
depends_on = None

_IDENT = re.compile(r"^[a-z_][a-z0-9_]*$")

_MV = """
CREATE MATERIALIZED VIEW ivm_municipio AS
WITH base AS (
  SELECT v.territorio_id, v.periodo,
         max(v.valor) FILTER (WHERE i.codigo = 'trabalho.emprego.saldo_caged') AS saldo_caged,
         max(v.valor) FILTER (WHERE i.codigo = 'credito.operacoes.saldo_total') AS credito,
         max(v.valor) FILTER (WHERE i.codigo = 'saude.resp.internacoes_j')      AS internacoes
  FROM valor v
  JOIN indicador i ON i.id = v.indicador_id AND i.publico = true
  JOIN territorio t ON t.id = v.territorio_id AND t.nivel = 'municipio'
  WHERE i.codigo IN ('trabalho.emprego.saldo_caged','credito.operacoes.saldo_total',
                     'saude.resp.internacoes_j')
    AND v.suprimido = false
  GROUP BY v.territorio_id, v.periodo
),
-- cobertura de saúde SEM o filtro de supressão: distingue "suprimido" (célula k-anon) de
-- "sem_cobertura" (não há célula) — fronteira honesta do v_saude_estado.
saude_cobertura AS (
  SELECT v.territorio_id, v.periodo, bool_or(v.suprimido) AS tem_suprimido
  FROM valor v
  JOIN indicador i ON i.id = v.indicador_id AND i.codigo = 'saude.resp.internacoes_j'
  JOIN territorio t ON t.id = v.territorio_id AND t.nivel = 'municipio'
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
                    / (max(credito) OVER w - min(credito) OVER w) END AS n_financas,
    CASE WHEN internacoes IS NULL THEN NULL
         WHEN max(internacoes) OVER w = min(internacoes) OVER w THEN 50.0
         ELSE 100.0 * (internacoes - min(internacoes) OVER w)
                    / (max(internacoes) OVER w - min(internacoes) OVER w) END AS n_saude
  FROM filtrado
  WINDOW w AS (PARTITION BY periodo)
),
comp AS (
  SELECT territorio_id, periodo,
         (100 - n_emprego) AS v_emprego,
         (100 - n_financas) AS v_financas,
         n_saude AS v_saude
  FROM norm
),
indice AS (
  SELECT territorio_id, periodo, v_emprego, v_financas, v_saude,
         (v_emprego + v_financas + coalesce(v_saude, 0))
           / (2 + (v_saude IS NOT NULL)::int) AS ivm
  FROM comp
)
SELECT indice.territorio_id, indice.periodo,
       round(v_emprego::numeric, 2) AS v_emprego,
       round(v_financas::numeric, 2) AS v_financas,
       round(v_saude::numeric, 2) AS v_saude,
       CASE WHEN indice.v_saude IS NOT NULL THEN 'valor'
            WHEN sc.tem_suprimido THEN 'suprimido'
            ELSE 'sem_cobertura' END AS v_saude_estado,
       round(ivm::numeric, 2) AS ivm,
       CASE WHEN ivm < 33 THEN 'verde'
            WHEN ivm <= 66 THEN 'amarelo'
            ELSE 'vermelho' END AS semaforo
FROM indice
LEFT JOIN saude_cobertura sc
       ON sc.territorio_id = indice.territorio_id AND sc.periodo = indice.periodo;
"""

# MV 0015 (ADR-0025) — restaurada no downgrade (com v_saude, sem v_saude_estado).
_MV_0015 = """
CREATE MATERIALIZED VIEW ivm_municipio AS
WITH base AS (
  SELECT v.territorio_id, v.periodo,
         max(v.valor) FILTER (WHERE i.codigo = 'trabalho.emprego.saldo_caged') AS saldo_caged,
         max(v.valor) FILTER (WHERE i.codigo = 'credito.operacoes.saldo_total') AS credito,
         max(v.valor) FILTER (WHERE i.codigo = 'saude.resp.internacoes_j')      AS internacoes
  FROM valor v
  JOIN indicador i ON i.id = v.indicador_id AND i.publico = true
  JOIN territorio t ON t.id = v.territorio_id AND t.nivel = 'municipio'
  WHERE i.codigo IN ('trabalho.emprego.saldo_caged','credito.operacoes.saldo_total',
                     'saude.resp.internacoes_j')
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
                    / (max(credito) OVER w - min(credito) OVER w) END AS n_financas,
    CASE WHEN internacoes IS NULL THEN NULL
         WHEN max(internacoes) OVER w = min(internacoes) OVER w THEN 50.0
         ELSE 100.0 * (internacoes - min(internacoes) OVER w)
                    / (max(internacoes) OVER w - min(internacoes) OVER w) END AS n_saude
  FROM filtrado
  WINDOW w AS (PARTITION BY periodo)
),
comp AS (
  SELECT territorio_id, periodo,
         (100 - n_emprego) AS v_emprego,
         (100 - n_financas) AS v_financas,
         n_saude AS v_saude
  FROM norm
),
indice AS (
  SELECT territorio_id, periodo, v_emprego, v_financas, v_saude,
         (v_emprego + v_financas + coalesce(v_saude, 0))
           / (2 + (v_saude IS NOT NULL)::int) AS ivm
  FROM comp
)
SELECT territorio_id, periodo,
       round(v_emprego::numeric, 2) AS v_emprego,
       round(v_financas::numeric, 2) AS v_financas,
       round(v_saude::numeric, 2) AS v_saude,
       round(ivm::numeric, 2) AS ivm,
       CASE WHEN ivm < 33 THEN 'verde'
            WHEN ivm <= 66 THEN 'amarelo'
            ELSE 'vermelho' END AS semaforo
FROM indice;
"""


def _role(url_str: str | None, papel: str) -> str:
    nome = make_url(url_str or "").username or ""
    if not _IDENT.match(nome):
        raise RuntimeError(f"Nome de role inválido ({papel}): {nome!r}")
    return nome


def _criar(mv_sql: str) -> None:
    s = get_settings()
    r_ana = _role(s.database_url, "analitica")
    r_cons = _role(s.consent_database_url, "consentimento")
    op.execute(mv_sql)
    op.execute("CREATE UNIQUE INDEX idx_ivm_municipio ON ivm_municipio (territorio_id, periodo);")
    op.execute(f"ALTER MATERIALIZED VIEW ivm_municipio OWNER TO {r_ana};")
    op.execute(f"GRANT SELECT ON ivm_municipio TO {r_cons};")


def upgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS ivm_municipio;")
    _criar(_MV)


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS ivm_municipio;")
    _criar(_MV_0015)
