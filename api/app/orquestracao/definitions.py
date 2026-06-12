# NB: sem `from __future__ import annotations` — o Dagster precisa resolver os tipos de Config
# (annotations reais, não strings) ao construir as definições de asset e op.
"""Dagster Degrau 2 — software-defined assets com linhagem declarada e partições por período.

Cada fonte é um **ativo particionado** (mensal: CAGED/ESTBAN/DATASUS; anual: SICONFI/INEP/PNCP).
O Dagster UI exibe:
  - Grafo de linhagem: produto → fonte (ex.: IVM depende de CAGED + ESTBAN + DATASUS).
  - Partições faltantes: o que ainda não foi carregado para cada competência.
  - Histórico de materializações por período.

Degrau 3 (sensors por chegada de arquivo + backfills automáticos) entra por dor §2.1 — aguarda
acesso FTP na VPS para DATASUS e CAGED.
"""

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

# ------------------------------------------------------------------ Definições de partição

#: Fontes mensais — começa em jan/2024 (dado real mais antigo disponível).
_MENSAL = dg.MonthlyPartitionsDefinition(start_date="2024-01-01")

#: Fontes anuais — exercícios cobertos pelo acervo; acrescentar o ano ao publicar novos dados.
_ANUAL = dg.StaticPartitionsDefinition(["2020", "2021", "2022", "2023", "2024", "2025"])


def _comp_de_mensal(partition_key: str) -> str:
    """Converte chave mensal ("2024-01-01") para competência YYYYMM ("202401")."""
    return partition_key[:7].replace("-", "")


def _comp_de_anual(partition_key: str) -> str:
    """Converte chave anual ("2024") para competência YYYYMM ("202401")."""
    return f"{partition_key}01"


# ------------------------------------------------------------------ Helpers assíncronos


async def _rodar_caged(janela: Janela) -> None:  # pragma: no cover - rede/FTP
    from app.core.cache import invalidar
    from app.indicadores.ivm import refrescar_ivm

    settings = get_settings()
    adaptador = AdaptadorCaged(FetcherCagedFTP())
    async with connect(settings.database_url) as conn:
        await executar_caged(
            janela, conn, adaptador, construir_store_padrao(), responsavel="dagster"
        )
    await refrescar_ivm()
    for prefixo in (
        "v1:cobertura:caged",
        "v1:pulso",
        "v1:giro",
        "v1:salario",
        "v1:regiao",
        "v1:panorama",
        "v1:valores",
    ):
        await invalidar(prefixo)


async def _rodar_estban(janela: Janela) -> None:  # pragma: no cover - rede/HTTP
    from app.indicadores.ivm import refrescar_ivm

    settings = get_settings()
    adaptador = AdaptadorEstban(FetcherEstbanHTTP(), skip_rows=2)
    async with connect(settings.database_url) as conn:
        await executar_estban(
            janela, conn, adaptador, construir_store_padrao(), responsavel="dagster"
        )
    await refrescar_ivm()


async def _rodar_siconfi(janela: Janela) -> None:  # pragma: no cover - rede/HTTP
    settings = get_settings()
    adaptador = AdaptadorSiconfi(FetcherSiconfiHTTP())
    async with connect(settings.database_url) as conn:
        await executar_siconfi(
            janela, conn, adaptador, construir_store_padrao(), responsavel="dagster"
        )


async def _rodar_siconfi_funcoes(janela: Janela) -> None:  # pragma: no cover - rede/HTTP
    settings = get_settings()
    adaptador = AdaptadorSiconfi(FetcherSiconfiFuncoesHTTP())
    async with connect(settings.database_url) as conn:
        await executar_siconfi_funcoes(
            janela, conn, adaptador, construir_store_padrao(), responsavel="dagster"
        )


async def _rodar_inep(janela: Janela) -> None:  # pragma: no cover - rede/HTTP
    settings = get_settings()
    adaptador = AdaptadorInep(FetcherInepHTTP())
    async with connect(settings.database_url) as conn:
        await executar_inep(
            janela, conn, adaptador, construir_store_padrao(), responsavel="dagster"
        )


async def _rodar_pncp(janela: Janela) -> None:  # pragma: no cover - rede/HTTP
    settings = get_settings()
    adaptador = AdaptadorPncp(FetcherPncpHTTP())
    async with connect(settings.database_url) as conn:
        await executar_pncp(
            janela, conn, adaptador, construir_store_padrao(), responsavel="dagster"
        )


async def _rodar_datasus(janela: Janela) -> None:  # pragma: no cover - rede/FTP
    from app.indicadores.ivm import refrescar_ivm

    settings = get_settings()
    adaptador = AdaptadorDatasus(FetcherDatasusFTP())
    async with connect(settings.database_url) as conn:
        await executar_datasus(
            janela, conn, adaptador, construir_store_padrao(), responsavel="dagster"
        )
    await refrescar_ivm()


# ------------------------------------------------------------------ Assets (Degrau 2)


@dg.asset(
    partitions_def=_MENSAL,
    group_name="trabalho",
    description="Saldo mensal de emprego formal do Novo CAGED (CAGEDMOV) por município.",
    metadata={"fonte": "Ministério do Trabalho/MTE", "lag_tipico": "~40 dias"},
)
def valores_caged(context: dg.AssetExecutionContext) -> dg.MaterializeResult:  # pragma: no cover
    comp = _comp_de_mensal(context.partition_key)
    context.log.info(f"CAGED: competência {comp}")
    asyncio.run(_rodar_caged(Janela.de_competencia(comp)))
    return dg.MaterializeResult(metadata={"competencia": comp})


@dg.asset(
    partitions_def=_MENSAL,
    group_name="trabalho",
    description="Saldo mensal de crédito bancário do ESTBAN (BCB/COSIF) por município.",
    metadata={"fonte": "Banco Central do Brasil", "lag_tipico": "~60 dias"},
)
def valores_estban(context: dg.AssetExecutionContext) -> dg.MaterializeResult:  # pragma: no cover
    comp = _comp_de_mensal(context.partition_key)
    context.log.info(f"ESTBAN: competência {comp}")
    asyncio.run(_rodar_estban(Janela.de_competencia(comp)))
    return dg.MaterializeResult(metadata={"competencia": comp})


@dg.asset(
    partitions_def=_ANUAL,
    group_name="financas",
    description="Transferências correntes do SICONFI/STN (Anexo I-C) por município.",
    metadata={"fonte": "Tesouro Nacional/STN", "lag_tipico": "~5 meses (DCA)"},
)
def valores_siconfi(context: dg.AssetExecutionContext) -> dg.MaterializeResult:  # pragma: no cover
    comp = _comp_de_anual(context.partition_key)
    context.log.info(f"SICONFI Anexo I-C: exercício {context.partition_key}")
    asyncio.run(_rodar_siconfi(Janela.de_competencia(comp)))
    return dg.MaterializeResult(metadata={"exercicio": context.partition_key})


@dg.asset(
    partitions_def=_ANUAL,
    group_name="financas",
    description="Despesa por função do SICONFI/STN (Anexo I-E) — base do OndeFoi.",
    metadata={"fonte": "Tesouro Nacional/STN", "lag_tipico": "~5 meses (DCA)"},
)
def execucao_siconfi(context: dg.AssetExecutionContext) -> dg.MaterializeResult:  # pragma: no cover
    comp = _comp_de_anual(context.partition_key)
    context.log.info(f"SICONFI Anexo I-E (funções): exercício {context.partition_key}")
    asyncio.run(_rodar_siconfi_funcoes(Janela.de_competencia(comp)))
    return dg.MaterializeResult(metadata={"exercicio": context.partition_key})


@dg.asset(
    partitions_def=_ANUAL,
    group_name="educacao",
    description="Matrículas do ensino fundamental (Censo Escolar/INEP) por município.",
    metadata={"fonte": "INEP/MEC", "lag_tipico": "~12 meses"},
)
def valores_inep(context: dg.AssetExecutionContext) -> dg.MaterializeResult:  # pragma: no cover
    comp = _comp_de_anual(context.partition_key)
    context.log.info(f"INEP Censo Escolar: ano {context.partition_key}")
    asyncio.run(_rodar_inep(Janela.de_competencia(comp)))
    return dg.MaterializeResult(metadata={"ano": context.partition_key})


@dg.asset(
    partitions_def=_ANUAL,
    group_name="compras",
    description="Valor global de contratos do PNCP por município — base do ObraViva.",
    metadata={"fonte": "PNCP/ME", "lag_tipico": "dias a semanas"},
)
def valores_pncp(context: dg.AssetExecutionContext) -> dg.MaterializeResult:  # pragma: no cover
    comp = _comp_de_anual(context.partition_key)
    context.log.info(f"PNCP contratos: ano {context.partition_key}")
    asyncio.run(_rodar_pncp(Janela.de_competencia(comp)))
    return dg.MaterializeResult(metadata={"ano": context.partition_key})


@dg.asset(
    partitions_def=_MENSAL,
    group_name="saude",
    description=(
        "Internações respiratórias do SIH/DATASUS (grupo J, CID-10) com k-anonimato. "
        "Subíndice de saúde do IVM."
    ),
    metadata={"fonte": "DATASUS/MS", "lag_tipico": "~90 dias"},
)
def valores_datasus(context: dg.AssetExecutionContext) -> dg.MaterializeResult:  # pragma: no cover
    comp = _comp_de_mensal(context.partition_key)
    context.log.info(f"DATASUS SIH: competência {comp}")
    asyncio.run(_rodar_datasus(Janela.de_competencia(comp)))
    return dg.MaterializeResult(metadata={"competencia": comp})


# ------------------------------------------------------------------ Asset jobs

job_valores_caged = dg.define_asset_job("job_valores_caged", selection=["valores_caged"])
job_valores_estban = dg.define_asset_job("job_valores_estban", selection=["valores_estban"])
job_valores_siconfi = dg.define_asset_job("job_valores_siconfi", selection=["valores_siconfi"])
job_execucao_siconfi = dg.define_asset_job("job_execucao_siconfi", selection=["execucao_siconfi"])
job_valores_inep = dg.define_asset_job("job_valores_inep", selection=["valores_inep"])
job_valores_pncp = dg.define_asset_job("job_valores_pncp", selection=["valores_pncp"])
job_valores_datasus = dg.define_asset_job("job_valores_datasus", selection=["valores_datasus"])


# ------------------------------------------------------------------ Schedules


@dg.schedule(job=job_valores_caged, cron_schedule="0 6 5 * *")
def schedule_caged_mensal(context: dg.ScheduleEvaluationContext) -> dg.RunRequest:
    comp = competencia_alvo(context.scheduled_execution_time.date(), defasagem_meses=2)
    return dg.RunRequest(partition_key=f"{comp[:4]}-{comp[4:6]}-01")


@dg.schedule(job=job_valores_estban, cron_schedule="0 7 10 * *")
def schedule_estban_mensal(context: dg.ScheduleEvaluationContext) -> dg.RunRequest:
    comp = competencia_alvo(context.scheduled_execution_time.date(), defasagem_meses=3)
    return dg.RunRequest(partition_key=f"{comp[:4]}-{comp[4:6]}-01")


@dg.schedule(
    job=job_valores_siconfi, cron_schedule="0 8 1 6 *"
)  # 1º jun — DCA do exercício anterior
def schedule_siconfi_anual(context: dg.ScheduleEvaluationContext) -> dg.RunRequest:
    ano = context.scheduled_execution_time.year - 1
    return dg.RunRequest(partition_key=str(ano))


@dg.schedule(
    job=job_execucao_siconfi, cron_schedule="0 9 1 6 *"
)  # 1º jun, 09h — Anexo I-E (OndeFoi), exercício anterior
def schedule_siconfi_funcoes_anual(context: dg.ScheduleEvaluationContext) -> dg.RunRequest:
    ano = context.scheduled_execution_time.year - 1
    return dg.RunRequest(partition_key=str(ano))


@dg.schedule(
    job=job_valores_inep, cron_schedule="0 9 1 11 *"
)  # 1º nov — microdados do Censo Escolar do ano anterior
def schedule_inep_anual(context: dg.ScheduleEvaluationContext) -> dg.RunRequest:
    ano = context.scheduled_execution_time.year - 1
    return dg.RunRequest(partition_key=str(ano))


@dg.schedule(
    job=job_valores_pncp, cron_schedule="0 8 15 1 *"
)  # 15 jan — contratos do exercício anterior consolidado
def schedule_pncp_anual(context: dg.ScheduleEvaluationContext) -> dg.RunRequest:
    ano = context.scheduled_execution_time.year - 1
    return dg.RunRequest(partition_key=str(ano))


@dg.schedule(job=job_valores_datasus, cron_schedule="0 7 12 * *")
def schedule_datasus_mensal(context: dg.ScheduleEvaluationContext) -> dg.RunRequest:
    comp = competencia_alvo(context.scheduled_execution_time.date(), defasagem_meses=4)
    return dg.RunRequest(partition_key=f"{comp[:4]}-{comp[4:6]}-01")


# ------------------------------------------------------------------ Definições

defs = dg.Definitions(
    assets=[
        valores_caged,
        valores_estban,
        valores_siconfi,
        execucao_siconfi,
        valores_inep,
        valores_pncp,
        valores_datasus,
    ],
    jobs=[
        job_valores_caged,
        job_valores_estban,
        job_valores_siconfi,
        job_execucao_siconfi,
        job_valores_inep,
        job_valores_pncp,
        job_valores_datasus,
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
