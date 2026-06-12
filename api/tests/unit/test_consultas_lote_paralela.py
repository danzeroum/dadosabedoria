"""Unidade: _executar_item() e comportamento paralelo do lote."""

from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.erros import NaoEncontradoError
from app.indicadores.modelos import MetaProveniencia, Paginacao
from app.profundo.modelos import ConsultaItem
from app.profundo.rotas import _executar_item

_META = MetaProveniencia(
    indicador="trabalho.emprego.saldo_caged",
    nome="Saldo CAGED",
    fonte="MTE/CAGED",
    metodologia="somatorio_admissoes_menos_demissoes",
    licenca="CC-BY-4.0",
)
_PAG = Paginacao(pagina=1, por_pagina=100, total=1)


def _make_item(indicador: str, territorio: str | None = None) -> ConsultaItem:
    return ConsultaItem(indicador=indicador, territorio=territorio)


def _mock_facade(dados: list | None = None, erro: Exception | None = None) -> MagicMock:
    facade = MagicMock()
    if erro:
        facade.listar_valores = AsyncMock(side_effect=erro)
    else:
        resultado = MagicMock()
        resultado.dados = dados or []
        resultado.meta = _META
        resultado.paginacao = _PAG
        facade.listar_valores = AsyncMock(return_value=resultado)
    return facade


def _make_session_mock() -> tuple[MagicMock, MagicMock]:
    session_mock = MagicMock()
    session_mock.__aenter__ = AsyncMock(return_value=session_mock)
    session_mock.__aexit__ = AsyncMock(return_value=False)
    sessionmaker_mock = MagicMock(return_value=session_mock)
    return session_mock, sessionmaker_mock


@pytest.mark.asyncio
async def test_item_ok_retorna_resultado_sem_erro() -> None:
    semaforo = asyncio.Semaphore(5)
    item = _make_item("trabalho.emprego.saldo_caged", "3550308")
    _, sessionmaker_mock = _make_session_mock()
    facade_mock = _mock_facade(dados=[])

    with (
        patch("app.profundo.rotas.get_sessionmaker", return_value=sessionmaker_mock),
        patch("app.profundo.rotas.IndicadoresFacade", return_value=facade_mock),
    ):
        resultado = await _executar_item(item, semaforo)

    assert resultado.erro is None
    assert resultado.dados is not None
    assert resultado.indicador == "trabalho.emprego.saldo_caged"
    assert resultado.territorio == "3550308"


@pytest.mark.asyncio
async def test_item_com_indicador_inexistente_retorna_erro_no_item() -> None:
    semaforo = asyncio.Semaphore(5)
    item = _make_item("nao.existe")
    _, sessionmaker_mock = _make_session_mock()
    facade_mock = _mock_facade(erro=NaoEncontradoError("nao.existe"))

    with (
        patch("app.profundo.rotas.get_sessionmaker", return_value=sessionmaker_mock),
        patch("app.profundo.rotas.IndicadoresFacade", return_value=facade_mock),
    ):
        resultado = await _executar_item(item, semaforo)

    assert resultado.erro is not None
    assert resultado.dados is None
    assert resultado.indicador == "nao.existe"


@pytest.mark.asyncio
async def test_lote_paralelo_preserva_ordem() -> None:
    """asyncio.gather preserva a ordem dos resultados, independente da ordem de conclusão."""
    semaforo = asyncio.Semaphore(5)
    itens = [_make_item(f"indicador.{i}") for i in range(4)]

    async def _side_effect(*args: object, **kwargs: object) -> MagicMock:
        resultado = MagicMock()
        resultado.dados = []
        resultado.meta = _META
        resultado.paginacao = _PAG
        return resultado

    _, sessionmaker_mock = _make_session_mock()
    facade_mock = MagicMock()
    facade_mock.listar_valores = AsyncMock(side_effect=_side_effect)

    with (
        patch("app.profundo.rotas.get_sessionmaker", return_value=sessionmaker_mock),
        patch("app.profundo.rotas.IndicadoresFacade", return_value=facade_mock),
    ):
        resultados = await asyncio.gather(*[_executar_item(item, semaforo) for item in itens])

    assert len(resultados) == 4
    for i, r in enumerate(resultados):
        assert r.indicador == f"indicador.{i}"


@pytest.mark.asyncio
async def test_semaforo_limita_concorrencia() -> None:
    """Com semáforo(1), apenas uma consulta roda por vez — verifica serialização."""
    semaforo = asyncio.Semaphore(1)
    em_paralelo_maximo = 0
    em_execucao = 0

    async def _side_effect(*args: object, **kwargs: object) -> MagicMock:
        nonlocal em_paralelo_maximo, em_execucao
        em_execucao += 1
        em_paralelo_maximo = max(em_paralelo_maximo, em_execucao)
        await asyncio.sleep(0)  # cede controle para verificar concorrência
        em_execucao -= 1
        resultado = MagicMock()
        resultado.dados = []
        resultado.meta = _META
        resultado.paginacao = _PAG
        return resultado

    _, sessionmaker_mock = _make_session_mock()
    facade_mock = MagicMock()
    facade_mock.listar_valores = AsyncMock(side_effect=_side_effect)

    itens = [_make_item(f"indicador.{i}") for i in range(5)]

    with (
        patch("app.profundo.rotas.get_sessionmaker", return_value=sessionmaker_mock),
        patch("app.profundo.rotas.IndicadoresFacade", return_value=facade_mock),
    ):
        await asyncio.gather(*[_executar_item(item, semaforo) for item in itens])

    assert em_paralelo_maximo == 1
