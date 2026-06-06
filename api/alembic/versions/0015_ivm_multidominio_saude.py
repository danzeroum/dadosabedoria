"""IVM multidomínio — incorpora o subíndice de saúde à view materializada — ADR-0025

Revision ID: 0015
Revises: 0014
Create Date: 2026-06-06

Eleva o IVM (ADR-0008/0018) de 2 para 3 subíndices, somando **saúde** (internações respiratórias,
SIH/DATASUS) aos de **emprego** (CAGED) e **finanças** (crédito ESTBAN). O produto-âncora TRANSP-01
passa de básico a multidomínio (``versao_metodologia = "v1.1"``).

Decisões de método (ADR-0025; honestidade técnica — o ativo é a confiança):
- **Normalização min-max por período mantida** (não z-score): com poucos municípios o z-score é
  degenerado (ADR-0018); o gatilho da v2 (z-score) segue sendo **cobertura nacional**.
- **Polaridade correta por subíndice:** mais emprego/crédito → MENOS vulnerável (inverte: 100−n);
  mais internações → MAIS vulnerável (não inverte: v_saude = n_saude).
- **Peso dinâmico:** o IVM é a média dos subíndices DISPONÍVEIS. Emprego+crédito são o núcleo
  (exigidos, como na v1); **saúde é opcional** (entra quando há dado não suprimido no período),
  então município sem saúde não é diluído por um valor neutro nem some do índice.

Aditivo (expand-and-contract): mantém ``v_emprego``/``v_financas``/``ivm``/``semaforo`` e ACRESCENTA
``v_saude`` (pode ser NULL). A MV é recomputada do zero (não há série a preservar — ADR-0018).
Owner = role_analitica para o REFRESH pelo runtime.
"""

from __future__ import annotations

import re

from alembic import op
from sqlalchemy.engine import make_url

from app.core.config import get_settings

revision = "0015"
down_revision = "0014"
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
filtrado AS (
  -- núcleo exige emprego + crédito (como na v1); saúde é subíndice OPCIONAL.
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
         (100 - n_emprego) AS v_emprego,    -- maior emprego  → menor vulnerabilidade
         (100 - n_financas) AS v_financas,  -- maior crédito  → menor vulnerabilidade
         n_saude AS v_saude                 -- mais internações → maior vulnerabilidade
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

# MV v1 (ADR-0008) — restaurada no downgrade (emprego + finanças, sem saúde).
_MV_V1 = """
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
    # Owner = role_analitica → REFRESH pelo runtime sem superusuário.
    op.execute(f"ALTER MATERIALIZED VIEW ivm_municipio OWNER TO {r_ana};")
    # Recria o GRANT que o DROP apagou: consentimento lê o IVM (evento público, sem PII) para casar
    # evento×assinante em `processar_alertas` (ADR-0013). role_analitica segue sem acesso a `app`.
    op.execute(f"GRANT SELECT ON ivm_municipio TO {r_cons};")


def upgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS ivm_municipio;")
    _criar(_MV)


def downgrade() -> None:
    op.execute("DROP MATERIALIZED VIEW IF EXISTS ivm_municipio;")
    _criar(_MV_V1)
