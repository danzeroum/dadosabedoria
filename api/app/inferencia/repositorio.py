"""Repositório para analytics inferencial — consultas sobre ``execucao_funcao``."""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from app.core.tables import execucao_funcao as t_ef
from app.core.tables import territorio as t_terr


async def obter_territorio(session: AsyncSession, codigo_ibge: str) -> dict | None:
    row = (
        (
            await session.execute(
                select(t_terr).where(
                    t_terr.c.codigo_ibge == codigo_ibge,
                    t_terr.c.nivel == "municipio",
                )
            )
        )
        .mappings()
        .first()
    )
    return dict(row) if row else None


async def distribuicao_funcao(session: AsyncSession, funcao_cod: str) -> dict | None:
    """Estatísticas nacionais de valor_por_hab para uma função SICONFI."""
    sql = text("""
        WITH periodo_max AS (
            SELECT MAX(periodo) AS periodo
            FROM execucao_funcao
            WHERE funcao_cod = :funcao_cod
        ),
        municipios AS (
            SELECT
                ef.territorio_id,
                MAX(ef.funcao_nome) AS funcao_nome,
                SUM(ef.liquidado) / NULLIF(MAX(t.populacao)::numeric, 0) AS valor_por_hab
            FROM execucao_funcao ef
            JOIN territorio t ON t.id = ef.territorio_id
            CROSS JOIN periodo_max pm
            WHERE ef.funcao_cod = :funcao_cod
              AND ef.periodo = pm.periodo
              AND t.nivel = 'municipio'
              AND t.populacao > 0
            GROUP BY ef.territorio_id
            HAVING SUM(ef.liquidado) IS NOT NULL
        )
        SELECT
            MAX(funcao_nome)                                                   AS funcao_nome,
            EXTRACT(YEAR FROM (SELECT periodo FROM periodo_max))::int          AS ano,
            COUNT(*)::int                                                       AS n,
            ROUND(AVG(valor_por_hab)::numeric, 2)                              AS media,
            ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP
                  (ORDER BY valor_por_hab)::numeric, 2)                        AS mediana,
            ROUND(STDDEV_POP(valor_por_hab)::numeric, 2)                       AS desvio,
            ROUND(PERCENTILE_CONT(0.10) WITHIN GROUP
                  (ORDER BY valor_por_hab)::numeric, 2)                        AS p10,
            ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP
                  (ORDER BY valor_por_hab)::numeric, 2)                        AS p25,
            ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP
                  (ORDER BY valor_por_hab)::numeric, 2)                        AS p75,
            ROUND(PERCENTILE_CONT(0.90) WITHIN GROUP
                  (ORDER BY valor_por_hab)::numeric, 2)                        AS p90,
            ROUND(MIN(valor_por_hab)::numeric, 2)                              AS minimo,
            ROUND(MAX(valor_por_hab)::numeric, 2)                              AS maximo
        FROM municipios
    """)
    row = (await session.execute(sql, {"funcao_cod": funcao_cod})).mappings().first()
    if row is None or row["n"] == 0:
        return None
    return dict(row)


async def perfil_orcamentario(session: AsyncSession, territorio_id: int) -> list[dict]:
    """Todas as funções de um município com percentil nacional (mesmo período)."""
    sql = text("""
        WITH target_periodo AS (
            SELECT MAX(ef.periodo) AS periodo
            FROM execucao_funcao ef
            WHERE ef.territorio_id = :territorio_id
        ),
        all_data AS (
            SELECT
                ef.funcao_cod,
                MAX(ef.funcao_nome)                                         AS funcao_nome,
                ef.territorio_id,
                SUM(ef.liquidado)::float                                    AS valor_liquidado,
                SUM(ef.liquidado) / NULLIF(MAX(t.populacao)::numeric, 0)   AS valor_por_hab,
                EXTRACT(YEAR FROM MAX(tp.periodo))::int                     AS ano
            FROM execucao_funcao ef
            JOIN territorio t ON t.id = ef.territorio_id
            CROSS JOIN target_periodo tp
            WHERE ef.periodo = tp.periodo
              AND t.nivel = 'municipio'
              AND t.populacao > 0
            GROUP BY ef.funcao_cod, ef.territorio_id
            HAVING SUM(ef.liquidado) IS NOT NULL
        ),
        with_rank AS (
            SELECT
                funcao_cod,
                funcao_nome,
                territorio_id,
                valor_liquidado,
                valor_por_hab::float,
                ano,
                ROUND(
                    (PERCENT_RANK() OVER (
                        PARTITION BY funcao_cod ORDER BY valor_por_hab
                    ) * 100)::numeric, 1
                ) AS percentil
            FROM all_data
        )
        SELECT funcao_cod, funcao_nome, valor_liquidado, valor_por_hab, percentil, ano
        FROM with_rank
        WHERE territorio_id = :territorio_id
        ORDER BY funcao_cod
    """)
    rows = (await session.execute(sql, {"territorio_id": territorio_id})).mappings().all()
    return [dict(r) for r in rows]


async def funcao_existe(session: AsyncSession, funcao_cod: str) -> bool:
    """Verifica se a função existe na base."""
    row = (
        await session.execute(
            select(t_ef.c.funcao_cod).where(t_ef.c.funcao_cod == funcao_cod).limit(1)
        )
    ).first()
    return row is not None
