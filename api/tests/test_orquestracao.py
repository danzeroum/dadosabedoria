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
        schedule_caged_mensal,
        schedule_estban_mensal,
    )

    assert job_caged.name == "job_caged"
    assert job_estban.name == "job_estban"
    assert schedule_caged_mensal.name == "schedule_caged_mensal"
    assert schedule_estban_mensal.name == "schedule_estban_mensal"


def test_schedules_geram_competencia_com_defasagem() -> None:
    from app.orquestracao.definitions import schedule_caged_mensal, schedule_estban_mensal

    ctx = dagster.build_schedule_context(
        scheduled_execution_time=datetime(2026, 6, 5, 6, 0, tzinfo=UTC)
    )
    caged = schedule_caged_mensal(ctx).run_config["ops"]["op_carregar_caged"]["config"]
    estban = schedule_estban_mensal(ctx).run_config["ops"]["op_carregar_estban"]["config"]
    assert caged["competencia"] == "202604"  # CAGED: 2 meses
    assert estban["competencia"] == "202603"  # ESTBAN: 3 meses
