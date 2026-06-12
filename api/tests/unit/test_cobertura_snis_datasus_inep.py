"""Unidade: cobertura_snis/datasus/inep() → demo=True quando sem dado, False com dado nacional."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.indicadores.facade import IndicadoresFacade
from app.indicadores.modelos import CoberturaDatasus, CoberturaInep, CoberturaSnis

_fn_snis = IndicadoresFacade.cobertura_snis.__wrapped__  # type: ignore[attr-defined]
_fn_datasus = IndicadoresFacade.cobertura_datasus.__wrapped__  # type: ignore[attr-defined]
_fn_inep = IndicadoresFacade.cobertura_inep.__wrapped__  # type: ignore[attr-defined]


def _facade_snis(n: int) -> IndicadoresFacade:
    repo = MagicMock()
    repo.contar_municipios_snis = AsyncMock(return_value=n)
    facade = object.__new__(IndicadoresFacade)
    facade._repo = repo
    facade._s = MagicMock()
    return facade


def _facade_datasus(n: int) -> IndicadoresFacade:
    repo = MagicMock()
    repo.contar_municipios_datasus = AsyncMock(return_value=n)
    facade = object.__new__(IndicadoresFacade)
    facade._repo = repo
    facade._s = MagicMock()
    return facade


def _facade_inep(n: int) -> IndicadoresFacade:
    repo = MagicMock()
    repo.contar_municipios_inep = AsyncMock(return_value=n)
    facade = object.__new__(IndicadoresFacade)
    facade._repo = repo
    facade._s = MagicMock()
    return facade


# ----------- SNIS -----------


@pytest.mark.asyncio
async def test_snis_demo_true_sem_dado() -> None:
    r: CoberturaSnis = await _fn_snis(_facade_snis(0))
    assert r.demo is True
    assert r.n_municipios == 0
    assert r.aviso is not None


@pytest.mark.asyncio
async def test_snis_demo_true_seed() -> None:
    r: CoberturaSnis = await _fn_snis(_facade_snis(2))
    assert r.demo is True


@pytest.mark.asyncio
async def test_snis_demo_false_nacional() -> None:
    r: CoberturaSnis = await _fn_snis(_facade_snis(5570))
    assert r.demo is False
    assert r.aviso is None


@pytest.mark.asyncio
async def test_snis_limiar_49_demo() -> None:
    r: CoberturaSnis = await _fn_snis(_facade_snis(49))
    assert r.demo is True


@pytest.mark.asyncio
async def test_snis_limiar_50_sai_demo() -> None:
    r: CoberturaSnis = await _fn_snis(_facade_snis(50))
    assert r.demo is False


# ----------- DATASUS -----------


@pytest.mark.asyncio
async def test_datasus_demo_true_sem_dado() -> None:
    r: CoberturaDatasus = await _fn_datasus(_facade_datasus(0))
    assert r.demo is True
    assert r.aviso is not None


@pytest.mark.asyncio
async def test_datasus_demo_false_nacional() -> None:
    r: CoberturaDatasus = await _fn_datasus(_facade_datasus(5570))
    assert r.demo is False
    assert r.aviso is None


@pytest.mark.asyncio
async def test_datasus_limiar_50_sai_demo() -> None:
    r: CoberturaDatasus = await _fn_datasus(_facade_datasus(50))
    assert r.demo is False


# ----------- INEP -----------


@pytest.mark.asyncio
async def test_inep_demo_true_sem_dado() -> None:
    r: CoberturaInep = await _fn_inep(_facade_inep(0))
    assert r.demo is True
    assert r.aviso is not None


@pytest.mark.asyncio
async def test_inep_demo_false_nacional() -> None:
    r: CoberturaInep = await _fn_inep(_facade_inep(5570))
    assert r.demo is False
    assert r.aviso is None


@pytest.mark.asyncio
async def test_inep_limiar_50_sai_demo() -> None:
    r: CoberturaInep = await _fn_inep(_facade_inep(50))
    assert r.demo is False
