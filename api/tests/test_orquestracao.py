"""Valida o Degrau 1 do Dagster (definitions carregam; schedule gera a competência correta).

Requer o extra `orquestracao` (Dagster). Pulado onde o runtime não está instalado.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

pytestmark = pytest.mark.orquestracao

dagster = pytest.importorskip("dagster")


def test_definitions_carregam() -> None:
    from app.orquestracao.definitions import (
        job_caged,
        job_estban,
        job_siconfi,
        schedule_caged_mensal,
        schedule_estban_mensal,
        schedule_siconfi_anual,
    )

    assert job_caged.name == "job_caged"
    assert job_estban.name == "job_estban"
    assert job_siconfi.name == "job_siconfi"
    assert schedule_caged_mensal.name == "schedule_caged_mensal"
    assert schedule_estban_mensal.name == "schedule_estban_mensal"
    assert schedule_siconfi_anual.name == "schedule_siconfi_anual"


def test_schedules_geram_competencia_com_defasagem() -> None:
    from app.orquestracao.definitions import schedule_caged_mensal, schedule_estban_mensal

    ctx = dagster.build_schedule_context(
        scheduled_execution_time=datetime(2026, 6, 5, 6, 0, tzinfo=UTC)
    )
    caged = schedule_caged_mensal(ctx).run_config["ops"]["op_carregar_caged"]["config"]
    estban = schedule_estban_mensal(ctx).run_config["ops"]["op_carregar_estban"]["config"]
    assert caged["competencia"] == "202604"  # CAGED: 2 meses
    assert estban["competencia"] == "202603"  # ESTBAN: 3 meses


def test_schedule_siconfi_usa_exercicio_anterior() -> None:
    from app.orquestracao.definitions import schedule_siconfi_anual

    ctx = dagster.build_schedule_context(
        scheduled_execution_time=datetime(2026, 6, 1, 8, 0, tzinfo=UTC)
    )
    cfg = schedule_siconfi_anual(ctx).run_config["ops"]["op_carregar_siconfi"]["config"]
    assert cfg["competencia"] == "202501"  # DCA anual → exercício anterior


def test_definitions_incluem_siconfi_funcoes() -> None:
    from app.orquestracao.definitions import job_siconfi_funcoes, schedule_siconfi_funcoes_anual

    assert job_siconfi_funcoes.name == "job_siconfi_funcoes"
    assert schedule_siconfi_funcoes_anual.name == "schedule_siconfi_funcoes_anual"


def test_schedule_siconfi_funcoes_usa_exercicio_anterior() -> None:
    from app.orquestracao.definitions import schedule_siconfi_funcoes_anual

    ctx = dagster.build_schedule_context(
        scheduled_execution_time=datetime(2026, 6, 1, 9, 0, tzinfo=UTC)
    )
    cfg = schedule_siconfi_funcoes_anual(ctx).run_config["ops"]["op_carregar_siconfi_funcoes"][
        "config"
    ]
    assert cfg["competencia"] == "202501"  # DCA anual (Anexo I-E) → exercício anterior
