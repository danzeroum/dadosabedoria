"""Unidade: cobertura_caged() → demo=True quando sem dado, False com dado nacional."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.indicadores.facade import IndicadoresFacade
from app.indicadores.modelos import CoberturaCAGED

# A lógica real está em cobertura_caged(); testamos via __wrapped__ para não depender do Redis.
_fn = IndicadoresFacade.cobertura_caged.__wrapped__  # type: ignore[attr-defined]


def _facade_com_contagem(n: int) -> IndicadoresFacade:
    repo = MagicMock()
    repo.contar_municipios_caged = AsyncMock(return_value=n)
    facade = object.__new__(IndicadoresFacade)
    facade._repo = repo
    facade._s = MagicMock()
    return facade


@pytest.mark.asyncio
async def test_demo_true_sem_dado() -> None:
    resultado: CoberturaCAGED = await _fn(_facade_com_contagem(0))
    assert resultado.demo is True
    assert resultado.n_municipios == 0
    assert resultado.aviso is not None
    assert "0" in resultado.aviso


@pytest.mark.asyncio
async def test_demo_true_com_seed_dois_municipios() -> None:
    resultado: CoberturaCAGED = await _fn(_facade_com_contagem(2))
    assert resultado.demo is True
    assert resultado.n_municipios == 2
    assert resultado.aviso is not None


@pytest.mark.asyncio
async def test_demo_false_com_dado_nacional() -> None:
    resultado: CoberturaCAGED = await _fn(_facade_com_contagem(5570))
    assert resultado.demo is False
    assert resultado.n_municipios == 5570
    assert resultado.aviso is None


@pytest.mark.asyncio
async def test_limiar_49_ainda_demo() -> None:
    resultado: CoberturaCAGED = await _fn(_facade_com_contagem(49))
    assert resultado.demo is True


@pytest.mark.asyncio
async def test_limiar_50_sai_do_demo() -> None:
    resultado: CoberturaCAGED = await _fn(_facade_com_contagem(50))
    assert resultado.demo is False
