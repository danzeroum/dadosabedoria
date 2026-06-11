"""Unidade de _janelas(): geração de intervalo de competências para backfill."""

from __future__ import annotations

from app.ingestao.adaptadores.base import Janela
from app.ingestao.run_caged import _janelas


def test_competencia_unica() -> None:
    assert _janelas(2026, 4, 2026, 4) == [Janela(2026, 4)]


def test_tres_meses_sem_virada() -> None:
    assert _janelas(2026, 2, 2026, 4) == [Janela(2026, 2), Janela(2026, 3), Janela(2026, 4)]


def test_virada_de_ano() -> None:
    assert _janelas(2025, 11, 2026, 2) == [
        Janela(2025, 11),
        Janela(2025, 12),
        Janela(2026, 1),
        Janela(2026, 2),
    ]


def test_fim_antes_do_inicio_retorna_vazio() -> None:
    assert _janelas(2026, 4, 2026, 3) == []


def test_intervalo_ano_completo() -> None:
    janelas = _janelas(2025, 1, 2025, 12)
    assert len(janelas) == 12
    assert janelas[0] == Janela(2025, 1)
    assert janelas[-1] == Janela(2025, 12)
