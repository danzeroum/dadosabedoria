"""Dagster Degrau 1 — job agendado (mensal) que dispara a esteira CAGED bronze→prata→ouro.

Retry e logs já ligados (suficiente para operar). Degraus 2–4 (assets, sensors, partições,
backfills) entram por dor, conforme §2.1.
"""
# NB: sem `from __future__ import annotations` — o Dagster precisa resolver os tipos de Config
# (annotations reais, não strings) ao construir os ops.

import asyncio

import dagster as dg

from app.core.config import get_settings
from app.core.db import connect
from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.caged import AdaptadorCaged, FetcherCagedFTP
from app.ingestao.agenda import competencia_alvo
from app.ingestao.bronze import construir_store_padrao
from app.ingestao.pipeline import executar_caged


class ConfigCaged(dg.Config):
    competencia: str  # "YYYYMM"


async def _carregar(janela: Janela) -> None:  # pragma: no cover - rede/S3
    settings = get_settings()
    adaptador = AdaptadorCaged(FetcherCagedFTP())
    async with connect(settings.database_url) as conn:
        await executar_caged(
            janela, conn, adaptador, construir_store_padrao(), responsavel="dagster"
        )


@dg.op(retry_policy=dg.RetryPolicy(max_retries=3, delay=30))
def op_carregar_caged(context: dg.OpExecutionContext, config: ConfigCaged) -> None:
    context.log.info(f"CAGED: carregando competência {config.competencia}")
    asyncio.run(_carregar(Janela.de_competencia(config.competencia)))  # pragma: no cover


@dg.job
def job_caged() -> None:
    op_carregar_caged()


@dg.schedule(job=job_caged, cron_schedule="0 6 5 * *")  # dia 5, 06h UTC
def schedule_caged_mensal(context: dg.ScheduleEvaluationContext) -> dg.RunRequest:
    comp = competencia_alvo(context.scheduled_execution_time.date())
    return dg.RunRequest(
        run_config={"ops": {"op_carregar_caged": {"config": {"competencia": comp}}}}
    )


defs = dg.Definitions(jobs=[job_caged], schedules=[schedule_caged_mensal])
