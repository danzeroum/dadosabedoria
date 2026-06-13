"""Valida o Degrau 2 do Dagster (assets com partições carregam; schedules geram a partição correta).

Requer o extra `orquestracao` (Dagster). Pulado onde o runtime não está instalado.
"""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

pytestmark = pytest.mark.orquestracao

dagster = pytest.importorskip("dagster")


# ------------------------------------------------------------------ Utilitários puros


def test_comp_de_mensal() -> None:
    from app.orquestracao.definitions import _comp_de_mensal

    assert _comp_de_mensal("2024-01-01") == "202401"
    assert _comp_de_mensal("2026-06-01") == "202606"


def test_comp_de_anual() -> None:
    from app.orquestracao.definitions import _comp_de_anual

    assert _comp_de_anual("2024") == "202401"
    assert _comp_de_anual("2020") == "202001"


# ------------------------------------------------------------------ Definições carregam


def test_assets_carregam() -> None:
    from app.orquestracao.definitions import (
        defs,
        execucao_siconfi,
        valores_ana,
        valores_aneel,
        valores_caged,
        valores_datasus,
        valores_estban,
        valores_inep,
        valores_pam,
        valores_pncp,
        valores_siconfi,
        valores_sinan,
        valores_sisvan,
        valores_sisvan_gestante,
        valores_snis,
    )

    assert list(valores_caged.key.path) == ["valores_caged"]
    assert list(valores_estban.key.path) == ["valores_estban"]
    assert list(valores_siconfi.key.path) == ["valores_siconfi"]
    assert list(execucao_siconfi.key.path) == ["execucao_siconfi"]
    assert list(valores_inep.key.path) == ["valores_inep"]
    assert list(valores_pncp.key.path) == ["valores_pncp"]
    assert list(valores_datasus.key.path) == ["valores_datasus"]
    assert list(valores_snis.key.path) == ["valores_snis"]
    assert list(valores_aneel.key.path) == ["valores_aneel"]
    assert list(valores_ana.key.path) == ["valores_ana"]
    assert list(valores_pam.key.path) == ["valores_pam"]
    assert list(valores_sisvan.key.path) == ["valores_sisvan"]
    assert list(valores_sisvan_gestante.key.path) == ["valores_sisvan_gestante"]
    assert list(valores_sinan.key.path) == ["valores_sinan"]
    # 14 assets no acervo
    assert len(list(defs.assets)) == 14


def test_jobs_carregam() -> None:
    from app.orquestracao.definitions import (
        job_execucao_siconfi,
        job_valores_ana,
        job_valores_aneel,
        job_valores_caged,
        job_valores_datasus,
        job_valores_estban,
        job_valores_inep,
        job_valores_pam,
        job_valores_pncp,
        job_valores_siconfi,
        job_valores_sinan,
        job_valores_sisvan,
        job_valores_sisvan_gestante,
        job_valores_snis,
    )

    assert job_valores_caged.name == "job_valores_caged"
    assert job_valores_estban.name == "job_valores_estban"
    assert job_valores_siconfi.name == "job_valores_siconfi"
    assert job_execucao_siconfi.name == "job_execucao_siconfi"
    assert job_valores_inep.name == "job_valores_inep"
    assert job_valores_pncp.name == "job_valores_pncp"
    assert job_valores_datasus.name == "job_valores_datasus"
    assert job_valores_snis.name == "job_valores_snis"
    assert job_valores_aneel.name == "job_valores_aneel"
    assert job_valores_ana.name == "job_valores_ana"
    assert job_valores_pam.name == "job_valores_pam"
    assert job_valores_sisvan.name == "job_valores_sisvan"
    assert job_valores_sisvan_gestante.name == "job_valores_sisvan_gestante"
    assert job_valores_sinan.name == "job_valores_sinan"


def test_schedules_carregam() -> None:
    from app.orquestracao.definitions import (
        schedule_ana_anual,
        schedule_aneel_anual,
        schedule_caged_mensal,
        schedule_datasus_mensal,
        schedule_estban_mensal,
        schedule_inep_anual,
        schedule_pam_anual,
        schedule_pncp_anual,
        schedule_siconfi_anual,
        schedule_siconfi_funcoes_anual,
        schedule_sinan_anual,
        schedule_sisvan_anual,
        schedule_sisvan_gestante_anual,
        schedule_snis_anual,
    )

    assert schedule_caged_mensal.name == "schedule_caged_mensal"
    assert schedule_estban_mensal.name == "schedule_estban_mensal"
    assert schedule_siconfi_anual.name == "schedule_siconfi_anual"
    assert schedule_siconfi_funcoes_anual.name == "schedule_siconfi_funcoes_anual"
    assert schedule_inep_anual.name == "schedule_inep_anual"
    assert schedule_pncp_anual.name == "schedule_pncp_anual"
    assert schedule_datasus_mensal.name == "schedule_datasus_mensal"
    assert schedule_snis_anual.name == "schedule_snis_anual"
    assert schedule_aneel_anual.name == "schedule_aneel_anual"
    assert schedule_ana_anual.name == "schedule_ana_anual"
    assert schedule_pam_anual.name == "schedule_pam_anual"
    assert schedule_sisvan_anual.name == "schedule_sisvan_anual"
    assert schedule_sisvan_gestante_anual.name == "schedule_sisvan_gestante_anual"
    assert schedule_sinan_anual.name == "schedule_sinan_anual"


# ------------------------------------------------------------------ Partições nos schedules


def test_schedule_caged_gera_particao_com_defasagem() -> None:
    from app.orquestracao.definitions import schedule_caged_mensal, schedule_estban_mensal

    ctx = dagster.build_schedule_context(
        scheduled_execution_time=datetime(2026, 6, 5, 6, 0, tzinfo=UTC)
    )
    # CAGED: 2 meses de defasagem em 05/06/2026 → competência 202604 → partição "2026-04-01"
    assert schedule_caged_mensal(ctx).partition_key == "2026-04-01"
    # ESTBAN: 3 meses → competência 202603 → partição "2026-03-01"
    assert schedule_estban_mensal(ctx).partition_key == "2026-03-01"


def test_schedule_siconfi_usa_exercicio_anterior() -> None:
    from app.orquestracao.definitions import schedule_siconfi_anual

    ctx = dagster.build_schedule_context(
        scheduled_execution_time=datetime(2026, 6, 1, 8, 0, tzinfo=UTC)
    )
    # DCA anual → exercício anterior → partição "2025"
    assert schedule_siconfi_anual(ctx).partition_key == "2025"


def test_schedule_siconfi_funcoes_usa_exercicio_anterior() -> None:
    from app.orquestracao.definitions import schedule_siconfi_funcoes_anual

    ctx = dagster.build_schedule_context(
        scheduled_execution_time=datetime(2026, 6, 1, 9, 0, tzinfo=UTC)
    )
    # Anexo I-E (OndeFoi) → exercício anterior → partição "2025"
    assert schedule_siconfi_funcoes_anual(ctx).partition_key == "2025"


def test_schedule_inep_usa_ano_anterior() -> None:
    from app.orquestracao.definitions import schedule_inep_anual

    ctx = dagster.build_schedule_context(
        scheduled_execution_time=datetime(2026, 11, 1, 9, 0, tzinfo=UTC)
    )
    # Censo Escolar: microdados saem ~out → exercício anterior → partição "2025"
    assert schedule_inep_anual(ctx).partition_key == "2025"


def test_schedule_pncp_usa_ano_anterior() -> None:
    from app.orquestracao.definitions import schedule_pncp_anual

    ctx = dagster.build_schedule_context(
        scheduled_execution_time=datetime(2026, 1, 15, 8, 0, tzinfo=UTC)
    )
    # Contratos consolidados do exercício anterior → partição "2025"
    assert schedule_pncp_anual(ctx).partition_key == "2025"


def test_schedule_datasus_gera_particao_com_defasagem() -> None:
    from app.orquestracao.definitions import schedule_datasus_mensal

    ctx = dagster.build_schedule_context(
        scheduled_execution_time=datetime(2026, 6, 12, 7, 0, tzinfo=UTC)
    )
    # DATASUS: 4 meses de defasagem em 12/06/2026 → competência 202602 → partição "2026-02-01"
    assert schedule_datasus_mensal(ctx).partition_key == "2026-02-01"


# ------------------------------------------------------------------ Grupos corretos


def test_grupos_por_dominio() -> None:
    from app.orquestracao.definitions import (
        execucao_siconfi,
        valores_ana,
        valores_aneel,
        valores_caged,
        valores_datasus,
        valores_estban,
        valores_inep,
        valores_pam,
        valores_pncp,
        valores_siconfi,
        valores_snis,
    )

    assert valores_caged.group_names_by_key[valores_caged.key] == "trabalho"
    assert valores_estban.group_names_by_key[valores_estban.key] == "trabalho"
    assert valores_siconfi.group_names_by_key[valores_siconfi.key] == "financas"
    assert execucao_siconfi.group_names_by_key[execucao_siconfi.key] == "financas"
    assert valores_inep.group_names_by_key[valores_inep.key] == "educacao"
    assert valores_pncp.group_names_by_key[valores_pncp.key] == "compras"
    assert valores_datasus.group_names_by_key[valores_datasus.key] == "saude"
    assert valores_snis.group_names_by_key[valores_snis.key] == "saneamento"
    assert valores_aneel.group_names_by_key[valores_aneel.key] == "energia"
    assert valores_ana.group_names_by_key[valores_ana.key] == "saneamento"
    assert valores_pam.group_names_by_key[valores_pam.key] == "alimentacao"
