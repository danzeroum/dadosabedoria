"""Valida o Degrau 1 do Dagster (definitions carregam; schedule gera a competência correta).

Requer o extra `orquestracao` (Dagster). Pulado onde o runtime não está instalado.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

pytestmark = pytest.mark.orquestracao

dagster = pytest.importorskip("dagster")


def test_definitions_carregam() -> None:
    from app.orquestracao.definitions import job_caged, schedule_caged_mensal

    assert job_caged.name == "job_caged"
    assert schedule_caged_mensal.name == "schedule_caged_mensal"


def test_schedule_gera_competencia_com_defasagem() -> None:
    from app.orquestracao.definitions import schedule_caged_mensal

    ctx = dagster.build_schedule_context(
        scheduled_execution_time=datetime(2026, 6, 5, 6, 0, tzinfo=UTC)
    )
    req = schedule_caged_mensal(ctx)
    competencia = req.run_config["ops"]["op_carregar_caged"]["config"]["competencia"]
    assert competencia == "202604"  # 2 meses de defasagem
