"""Unidade: consultar_quota() — leitura da cota sem incremento."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.profundo.rate_limit import InfoQuota, consultar_quota


def _mock_redis_get(valor: str | None) -> MagicMock:
    r = MagicMock()
    r.get = AsyncMock(return_value=valor)
    return r


@pytest.mark.asyncio
async def test_sem_uso_retorna_zero_usado() -> None:
    with patch("app.profundo.rate_limit.get_redis", return_value=_mock_redis_get(None)):
        q = await consultar_quota("cliente_a")

    assert isinstance(q, InfoQuota)
    assert q.usado == 0
    assert q.restante == q.limite


@pytest.mark.asyncio
async def test_com_uso_parcial_retorna_valores_corretos() -> None:
    with patch("app.profundo.rate_limit.get_redis", return_value=_mock_redis_get("300")):
        q = await consultar_quota("cliente_a")

    assert q.usado == 300
    assert q.restante == q.limite - 300


@pytest.mark.asyncio
async def test_exatamente_no_limite_restante_zero() -> None:
    with patch("app.profundo.rate_limit.get_redis", return_value=_mock_redis_get("1000")):
        q = await consultar_quota("cliente_a")

    assert q.usado == 1000
    assert q.restante == 0


@pytest.mark.asyncio
async def test_acima_do_limite_restante_zero_e_usado_real() -> None:
    """usado pode superar o limite (requisições acumuladas antes do bloqueio)."""
    with patch("app.profundo.rate_limit.get_redis", return_value=_mock_redis_get("1005")):
        q = await consultar_quota("cliente_a")

    assert q.usado == 1005
    assert q.restante == 0


@pytest.mark.asyncio
async def test_nao_chama_incr() -> None:
    r = _mock_redis_get("10")
    r.incr = AsyncMock()
    with patch("app.profundo.rate_limit.get_redis", return_value=r):
        await consultar_quota("cliente_a")

    r.incr.assert_not_called()


@pytest.mark.asyncio
async def test_redis_indisponivel_degrada_graciosamente() -> None:
    r = MagicMock()
    r.get = AsyncMock(side_effect=ConnectionError("Redis offline"))
    with patch("app.profundo.rate_limit.get_redis", return_value=r):
        q = await consultar_quota("cliente_a")

    assert q.usado == 0
    assert q.restante == q.limite


@pytest.mark.asyncio
async def test_reset_alinhado_na_hora_cheia() -> None:
    from app.profundo.rate_limit import JANELA_SEGUNDOS

    with patch("app.profundo.rate_limit.get_redis", return_value=_mock_redis_get(None)):
        q = await consultar_quota("cliente_a")

    assert q.reset > 0
    assert q.reset % JANELA_SEGUNDOS == 0


@pytest.mark.asyncio
async def test_clientes_diferentes_sao_independentes() -> None:
    with patch("app.profundo.rate_limit.get_redis", return_value=_mock_redis_get("999")):
        q_a = await consultar_quota("cliente_a")

    with patch("app.profundo.rate_limit.get_redis", return_value=_mock_redis_get("0")):
        q_b = await consultar_quota("cliente_b")

    assert q_a.usado == 999
    assert q_b.usado == 0
