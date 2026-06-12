"""Unidade: cobertura_pncp/siconfi() → demo=True quando sem dado, False com dado nacional."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.indicadores.facade import IndicadoresFacade
from app.indicadores.modelos import CoberturaPncp, CoberturaSiconfi

_fn_pncp = IndicadoresFacade.cobertura_pncp.__wrapped__  # type: ignore[attr-defined]
_fn_siconfi = IndicadoresFacade.cobertura_siconfi.__wrapped__  # type: ignore[attr-defined]


def _facade_pncp(n: int) -> IndicadoresFacade:
    repo = MagicMock()
    repo.contar_municipios_pncp = AsyncMock(return_value=n)
    facade = object.__new__(IndicadoresFacade)
    facade._repo = repo
    facade._s = MagicMock()
    return facade


def _facade_siconfi(n: int) -> IndicadoresFacade:
    repo = MagicMock()
    repo.contar_municipios_siconfi = AsyncMock(return_value=n)
    facade = object.__new__(IndicadoresFacade)
    facade._repo = repo
    facade._s = MagicMock()
    return facade


# ----------- PNCP -----------


@pytest.mark.asyncio
async def test_pncp_demo_true_sem_dado() -> None:
    r: CoberturaPncp = await _fn_pncp(_facade_pncp(0))
    assert r.demo is True
    assert r.n_municipios == 0
    assert r.aviso is not None


@pytest.mark.asyncio
async def test_pncp_demo_true_seed() -> None:
    r: CoberturaPncp = await _fn_pncp(_facade_pncp(2))
    assert r.demo is True


@pytest.mark.asyncio
async def test_pncp_demo_false_nacional() -> None:
    r: CoberturaPncp = await _fn_pncp(_facade_pncp(5570))
    assert r.demo is False
    assert r.aviso is None


@pytest.mark.asyncio
async def test_pncp_limiar_49_demo() -> None:
    r: CoberturaPncp = await _fn_pncp(_facade_pncp(49))
    assert r.demo is True


@pytest.mark.asyncio
async def test_pncp_limiar_50_sai_demo() -> None:
    r: CoberturaPncp = await _fn_pncp(_facade_pncp(50))
    assert r.demo is False


# ----------- SICONFI -----------


@pytest.mark.asyncio
async def test_siconfi_demo_true_sem_dado() -> None:
    r: CoberturaSiconfi = await _fn_siconfi(_facade_siconfi(0))
    assert r.demo is True
    assert r.aviso is not None


@pytest.mark.asyncio
async def test_siconfi_demo_true_seed() -> None:
    r: CoberturaSiconfi = await _fn_siconfi(_facade_siconfi(2))
    assert r.demo is True


@pytest.mark.asyncio
async def test_siconfi_demo_false_nacional() -> None:
    r: CoberturaSiconfi = await _fn_siconfi(_facade_siconfi(5541))
    assert r.demo is False
    assert r.aviso is None


@pytest.mark.asyncio
async def test_siconfi_limiar_49_demo() -> None:
    r: CoberturaSiconfi = await _fn_siconfi(_facade_siconfi(49))
    assert r.demo is True


@pytest.mark.asyncio
async def test_siconfi_limiar_50_sai_demo() -> None:
    r: CoberturaSiconfi = await _fn_siconfi(_facade_siconfi(50))
    assert r.demo is False
