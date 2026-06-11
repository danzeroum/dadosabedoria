"""Dagster Degrau 1 — jobs agendados das esteiras CAGED, BCB/ESTBAN (mensais) e SICONFI (anual).

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
from app.ingestao.adaptadores.datasus import AdaptadorDatasus, FetcherDatasusFTP
from app.ingestao.adaptadores.estban import AdaptadorEstban, FetcherEstbanHTTP
from app.ingestao.adaptadores.inep import AdaptadorInep, FetcherInepHTTP
from app.ingestao.adaptadores.pncp import AdaptadorPncp, FetcherPncpHTTP
from app.ingestao.adaptadores.siconfi import (
    AdaptadorSiconfi,
    FetcherSiconfiFuncoesHTTP,
    FetcherSiconfiHTTP,
)
from app.ingestao.agenda import competencia_alvo
from app.ingestao.bronze import construir_store_padrao
from app.ingestao.pipeline import (
    executar_caged,
    executar_datasus,
    executar_estban,
    executar_inep,
    executar_pncp,
    executar_siconfi,
    executar_siconfi_funcoes,
)


class ConfigIngestao(dg.Config):
    competencia: str  # "YYYYMM"


async def _rodar_caged(janela: Janela) -> None:  # pragma: no cover - rede/S3
    from app.core.cache import invalidar
    from app.indicadores.ivm import refrescar_ivm

    settings = get_settings()
    adaptador = AdaptadorCaged(FetcherCagedFTP())
    async with connect(settings.database_url) as conn:
        await executar_caged(
            janela, conn, adaptador, construir_store_padrao(), responsavel="dagster"
        )
    await refrescar_ivm()
    _CACHES_CAGED = (
        "v1:cobertura:caged",
        "v1:pulso",
        "v1:giro",
        "v1:salario",
        "v1:regiao",
        "v1:panorama",
        "v1:valores",
    )
    for prefixo in _CACHES_CAGED:
        await invalidar(prefixo)


async def _rodar_estban(janela: Janela) -> None:  # pragma: no cover - rede/S3
    from app.indicadores.ivm import refrescar_ivm

    settings = get_settings()
    adaptador = AdaptadorEstban(FetcherEstbanHTTP(), skip_rows=2)
    async with connect(settings.database_url) as conn:
        await executar_estban(
            janela, conn, adaptador, construir_store_padrao(), responsavel="dagster"
        )
    await refrescar_ivm()


async def _rodar_siconfi(janela: Janela) -> None:  # pragma: no cover - rede/S3
    # SICONFI alimenta um indicador de PRODUTO (OndeFoi), não o IVM → sem refrescar_ivm.
    settings = get_settings()
    adaptador = AdaptadorSiconfi(FetcherSiconfiHTTP())
    async with connect(settings.database_url) as conn:
        await executar_siconfi(
            janela, conn, adaptador, construir_store_padrao(), responsavel="dagster"
        )


async def _rodar_siconfi_funcoes(janela: Janela) -> None:  # pragma: no cover - rede/S3
    # OndeFoi (execução por função, Anexo I-E) — fato dedicada `execucao_funcao`, fora do IVM.
    settings = get_settings()
    adaptador = AdaptadorSiconfi(FetcherSiconfiFuncoesHTTP())
    async with connect(settings.database_url) as conn:
        await executar_siconfi_funcoes(
            janela, conn, adaptador, construir_store_padrao(), responsavel="dagster"
        )


async def _rodar_inep(janela: Janela) -> None:  # pragma: no cover - rede/S3
    # INEP alimenta um indicador DESCRITIVO (educacao), fora do IVM → sem refrescar_ivm.
    settings = get_settings()
    adaptador = AdaptadorInep(FetcherInepHTTP())
    async with connect(settings.database_url) as conn:
        await executar_inep(
            janela, conn, adaptador, construir_store_padrao(), responsavel="dagster"
        )


async def _rodar_pncp(janela: Janela) -> None:  # pragma: no cover - rede/S3
    # PNCP alimenta um indicador DESCRITIVO (compras), fora do IVM → sem refrescar_ivm.
    settings = get_settings()
    adaptador = AdaptadorPncp(FetcherPncpHTTP())
    async with connect(settings.database_url) as conn:
        await executar_pncp(
            janela, conn, adaptador, construir_store_padrao(), responsavel="dagster"
        )


async def _rodar_datasus(janela: Janela) -> None:  # pragma: no cover - rede/dbc
    # DATASUS/SIH alimenta a SAÚDE, subíndice do IVM → refresca a MV após a carga (como CAGED).
    from app.indicadores.ivm import refrescar_ivm

    settings = get_settings()
    adaptador = AdaptadorDatasus(FetcherDatasusFTP())
    async with connect(settings.database_url) as conn:
        await executar_datasus(
            janela, conn, adaptador, construir_store_padrao(), responsavel="dagster"
        )
    await refrescar_ivm()


@dg.op(retry_policy=dg.RetryPolicy(max_retries=3, delay=30))
def op_carregar_caged(context: dg.OpExecutionContext, config: ConfigIngestao) -> None:
    context.log.info(f"CAGED: carregando competência {config.competencia}")
    asyncio.run(_rodar_caged(Janela.de_competencia(config.competencia)))  # pragma: no cover


@dg.op(retry_policy=dg.RetryPolicy(max_retries=3, delay=30))
def op_carregar_estban(context: dg.OpExecutionContext, config: ConfigIngestao) -> None:
    context.log.info(f"ESTBAN: carregando competência {config.competencia}")
    asyncio.run(_rodar_estban(Janela.de_competencia(config.competencia)))  # pragma: no cover


@dg.op(retry_policy=dg.RetryPolicy(max_retries=3, delay=30))
def op_carregar_siconfi(context: dg.OpExecutionContext, config: ConfigIngestao) -> None:
    context.log.info(f"SICONFI: carregando exercício {config.competencia}")
    asyncio.run(_rodar_siconfi(Janela.de_competencia(config.competencia)))  # pragma: no cover


@dg.op(retry_policy=dg.RetryPolicy(max_retries=3, delay=30))
def op_carregar_siconfi_funcoes(context: dg.OpExecutionContext, config: ConfigIngestao) -> None:
    context.log.info(f"SICONFI funções: carregando exercício {config.competencia}")
    asyncio.run(
        _rodar_siconfi_funcoes(Janela.de_competencia(config.competencia))
    )  # pragma: no cover


@dg.op(retry_policy=dg.RetryPolicy(max_retries=3, delay=30))
def op_carregar_inep(context: dg.OpExecutionContext, config: ConfigIngestao) -> None:
    context.log.info(f"INEP: carregando ano {config.competencia}")
    asyncio.run(_rodar_inep(Janela.de_competencia(config.competencia)))  # pragma: no cover


@dg.op(retry_policy=dg.RetryPolicy(max_retries=3, delay=30))
def op_carregar_pncp(context: dg.OpExecutionContext, config: ConfigIngestao) -> None:
    context.log.info(f"PNCP: carregando ano {config.competencia}")
    asyncio.run(_rodar_pncp(Janela.de_competencia(config.competencia)))  # pragma: no cover


@dg.op(retry_policy=dg.RetryPolicy(max_retries=3, delay=30))
def op_carregar_datasus(context: dg.OpExecutionContext, config: ConfigIngestao) -> None:
    context.log.info(f"DATASUS: carregando competência {config.competencia}")
    asyncio.run(_rodar_datasus(Janela.de_competencia(config.competencia)))  # pragma: no cover


@dg.job
def job_caged() -> None:
    op_carregar_caged()


@dg.job
def job_estban() -> None:
    op_carregar_estban()


@dg.job
def job_siconfi() -> None:
    op_carregar_siconfi()


@dg.job
def job_siconfi_funcoes() -> None:
    op_carregar_siconfi_funcoes()


@dg.job
def job_inep() -> None:
    op_carregar_inep()


@dg.job
def job_pncp() -> None:
    op_carregar_pncp()


@dg.job
def job_datasus() -> None:
    op_carregar_datasus()


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


@dg.schedule(
    job=job_siconfi, cron_schedule="0 8 1 6 *"
)  # 1º jun, 08h UTC — DCA do exercício anterior
def schedule_siconfi_anual(context: dg.ScheduleEvaluationContext) -> dg.RunRequest:
    # DCA é publicada no ano seguinte (prazo ~abr/mai) → ingere o exercício anterior.
    ano = context.scheduled_execution_time.year - 1
    return dg.RunRequest(
        run_config={"ops": {"op_carregar_siconfi": {"config": {"competencia": f"{ano:04d}01"}}}}
    )


@dg.schedule(
    job=job_siconfi_funcoes, cron_schedule="0 9 1 6 *"
)  # 1º jun, 09h UTC — DCA Anexo I-E (execução por função), exercício anterior
def schedule_siconfi_funcoes_anual(context: dg.ScheduleEvaluationContext) -> dg.RunRequest:
    ano = context.scheduled_execution_time.year - 1
    return dg.RunRequest(
        run_config={
            "ops": {"op_carregar_siconfi_funcoes": {"config": {"competencia": f"{ano:04d}01"}}}
        }
    )


@dg.schedule(
    job=job_inep, cron_schedule="0 9 1 11 *"
)  # 1º nov, 09h UTC — Censo Escolar do ano anterior (microdados saem ~out)
def schedule_inep_anual(context: dg.ScheduleEvaluationContext) -> dg.RunRequest:
    # Microdados do Censo Escolar saem no ano seguinte → ingere o ano anterior.
    ano = context.scheduled_execution_time.year - 1
    return dg.RunRequest(
        run_config={"ops": {"op_carregar_inep": {"config": {"competencia": f"{ano:04d}01"}}}}
    )


@dg.schedule(
    job=job_pncp, cron_schedule="0 8 15 1 *"
)  # 15 jan, 08h UTC — contratos do ano anterior (consolidado)
def schedule_pncp_anual(context: dg.ScheduleEvaluationContext) -> dg.RunRequest:
    # Consolida os contratos do ano anterior já fechado.
    ano = context.scheduled_execution_time.year - 1
    return dg.RunRequest(
        run_config={"ops": {"op_carregar_pncp": {"config": {"competencia": f"{ano:04d}01"}}}}
    )


@dg.schedule(job=job_datasus, cron_schedule="0 7 12 * *")  # dia 12, 07h UTC (lag SIH ~90d)
def schedule_datasus_mensal(context: dg.ScheduleEvaluationContext) -> dg.RunRequest:
    comp = competencia_alvo(context.scheduled_execution_time.date(), defasagem_meses=4)
    return dg.RunRequest(
        run_config={"ops": {"op_carregar_datasus": {"config": {"competencia": comp}}}}
    )


defs = dg.Definitions(
    jobs=[
        job_caged,
        job_estban,
        job_siconfi,
        job_siconfi_funcoes,
        job_inep,
        job_pncp,
        job_datasus,
    ],
    schedules=[
        schedule_caged_mensal,
        schedule_estban_mensal,
        schedule_siconfi_anual,
        schedule_siconfi_funcoes_anual,
        schedule_inep_anual,
        schedule_pncp_anual,
        schedule_datasus_mensal,
    ],
)
