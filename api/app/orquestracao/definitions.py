"""Dagster Degrau 1 — jobs agendados (mensais) das esteiras CAGED e BCB/ESTBAN.

Retry e logs já ligados. Degraus 2–4 (assets, sensors, partições, backfills) entram por dor (§2.1).
"""
# NB: sem `from __future__ import annotations` — o Dagster precisa resolver os tipos de Config
# (annotations reais, não strings) ao construir os ops.

import asyncio

import dagster as dg

from app.core.config import get_settings
from app.core.db import connect
from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.caged import AdaptadorCaged, FetcherCagedFTP
from app.ingestao.adaptadores.estban import AdaptadorEstban, FetcherEstbanHTTP
from app.ingestao.agenda import competencia_alvo
from app.ingestao.bronze import construir_store_padrao
from app.ingestao.pipeline import executar_caged, executar_estban


class ConfigIngestao(dg.Config):
    competencia: str  # "YYYYMM"


async def _rodar_caged(janela: Janela) -> None:  # pragma: no cover - rede/S3
    settings = get_settings()
    adaptador = AdaptadorCaged(FetcherCagedFTP())
    async with connect(settings.database_url) as conn:
        await executar_caged(
            janela, conn, adaptador, construir_store_padrao(), responsavel="dagster"
        )


async def _rodar_estban(janela: Janela) -> None:  # pragma: no cover - rede/S3
    settings = get_settings()
    adaptador = AdaptadorEstban(FetcherEstbanHTTP(), skip_rows=2)
    async with connect(settings.database_url) as conn:
        await executar_estban(
            janela, conn, adaptador, construir_store_padrao(), responsavel="dagster"
        )


@dg.op(retry_policy=dg.RetryPolicy(max_retries=3, delay=30))
def op_carregar_caged(context: dg.OpExecutionContext, config: ConfigIngestao) -> None:
    context.log.info(f"CAGED: carregando competência {config.competencia}")
    asyncio.run(_rodar_caged(Janela.de_competencia(config.competencia)))  # pragma: no cover


@dg.op(retry_policy=dg.RetryPolicy(max_retries=3, delay=30))
def op_carregar_estban(context: dg.OpExecutionContext, config: ConfigIngestao) -> None:
    context.log.info(f"ESTBAN: carregando competência {config.competencia}")
    asyncio.run(_rodar_estban(Janela.de_competencia(config.competencia)))  # pragma: no cover


@dg.job
def job_caged() -> None:
    op_carregar_caged()


@dg.job
def job_estban() -> None:
    op_carregar_estban()


@dg.schedule(job=job_caged, cron_schedule="0 6 5 * *")  # dia 5, 06h UTC (lag CAGED ~40d)
def schedule_caged_mensal(context: dg.ScheduleEvaluationContext) -> dg.RunRequest:
    comp = competencia_alvo(context.scheduled_execution_time.date(), defasagem_meses=2)
    return dg.RunRequest(
        run_config={"ops": {"op_carregar_caged": {"config": {"competencia": comp}}}}
    )


@dg.schedule(job=job_estban, cron_schedule="0 7 10 * *")  # dia 10, 07h UTC (lag ESTBAN ~60d)
def schedule_estban_mensal(context: dg.ScheduleEvaluationContext) -> dg.RunRequest:
    comp = competencia_alvo(context.scheduled_execution_time.date(), defasagem_meses=3)
    return dg.RunRequest(
        run_config={"ops": {"op_carregar_estban": {"config": {"competencia": comp}}}}
    )


defs = dg.Definitions(
    jobs=[job_caged, job_estban],
    schedules=[schedule_caged_mensal, schedule_estban_mensal],
)
