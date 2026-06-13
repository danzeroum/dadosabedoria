"""Testes unitários para a lógica de status de frescor."""

from __future__ import annotations

import pytest

from app.frescor.rotas import _status


@pytest.mark.parametrize(
    ("periodicidade", "dias", "esperado"),
    [
        # sem dado
        ("mensal", None, "sem_dado"),
        ("anual", None, "sem_dado"),
        # mensal: ok ≤ 45
        ("mensal", 0, "ok"),
        ("mensal", 44, "ok"),
        ("mensal", 45, "ok"),
        # mensal: atenção 46–90
        ("mensal", 46, "atencao"),
        ("mensal", 90, "atencao"),
        # mensal: atrasado > 90
        ("mensal", 91, "atrasado"),
        ("mensal", 180, "atrasado"),
        # anual: ok ≤ 400
        ("anual", 0, "ok"),
        ("anual", 365, "ok"),
        ("anual", 400, "ok"),
        # anual: atenção 401–700
        ("anual", 401, "atencao"),
        ("anual", 700, "atencao"),
        # anual: atrasado > 700
        ("anual", 701, "atrasado"),
        # outros valores de periodicidade → tratados como anual
        ("trimestral", 400, "ok"),
        ("irregular", 701, "atrasado"),
    ],
)
def test_status(periodicidade: str, dias: int | None, esperado: str) -> None:
    assert _status(periodicidade, dias) == esperado
