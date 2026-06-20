"""Testes das funções puras auxiliares do ``facade`` (sem DB).

Fixa o contrato honesto do ``_liquidado_ou_zero``: para os 11 produtos SICONFI
per-capita, ``SUM(liquidado)`` NULL (função sem linhas, mas município COM execução
SICONFI — garantido pelo guard ``periodo is None → 404``) mapeia para **R$ 0**, que
classifica como crítico/incipiente e NÃO como ``sem_dado``. Sem este teste, alguém
poderia "consertar" o ``else 0.0`` para ``None`` e silenciosamente quebrar a intenção.
"""

from typing import cast

from sqlalchemy import RowMapping

from app.produtos.facade import _liquidado_ou_zero


def _row(valor: float | None) -> RowMapping:
    return cast(RowMapping, {"liquidado": valor})


def test_liquidado_ou_zero_sem_resultado() -> None:
    # Nenhuma linha (row None) → 0.0.
    assert _liquidado_ou_zero(None) == 0.0


def test_liquidado_ou_zero_sum_nulo_vira_zero() -> None:
    # SUM() de uma função sem linhas devolve NULL → 0.0 (R$0 honesto, não sem_dado).
    assert _liquidado_ou_zero(_row(None)) == 0.0


def test_liquidado_ou_zero_preserva_valor() -> None:
    assert _liquidado_ou_zero(_row(1234.5)) == 1234.5
    assert _liquidado_ou_zero(_row(0)) == 0.0
