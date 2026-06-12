"""Unidade: verificar_rate_limit() — fixed-window counter, limiar, degradação graciosa."""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.erros import RateLimitError
from app.profundo.rate_limit import JANELA_SEGUNDOS, InfoRateLimit, verificar_rate_limit


def _mock_redis(contagem: int) -> MagicMock:
    r = MagicMock()
    r.incr = AsyncMock(return_value=contagem)
    r.expire = AsyncMock()
    return r


@pytest.mark.asyncio
async def test_primeira_requisicao_ok_e_seta_expire() -> None:
    with patch("app.profundo.rate_limit.get_redis", return_value=_mock_redis(1)):
        info = await verificar_rate_limit("cliente_a")

    assert isinstance(info, InfoRateLimit)
    assert info.limite == 1000  # default Settings
    assert info.restante == 999


@pytest.mark.asyncio
async def test_expire_chamado_apenas_na_primeira_requisicao() -> None:
    r = _mock_redis(1)
    with patch("app.profundo.rate_limit.get_redis", return_value=r):
        await verificar_rate_limit("cliente_a")
    r.expire.assert_called_once()


@pytest.mark.asyncio
async def test_expire_nao_chamado_em_requisicao_subsequente() -> None:
    r = _mock_redis(5)
    with patch("app.profundo.rate_limit.get_redis", return_value=r):
        await verificar_rate_limit("cliente_a")
    r.expire.assert_not_called()


@pytest.mark.asyncio
async def test_exatamente_no_limite_permite_e_restante_zero() -> None:
    with patch("app.profundo.rate_limit.get_redis", return_value=_mock_redis(1000)):
        info = await verificar_rate_limit("cliente_a")

    assert info.restante == 0


@pytest.mark.asyncio
async def test_acima_do_limite_levanta_rate_limit_error() -> None:
    with patch("app.profundo.rate_limit.get_redis", return_value=_mock_redis(1001)):
        with pytest.raises(RateLimitError) as exc_info:
            await verificar_rate_limit("cliente_a")

    exc = exc_info.value
    assert exc.limite == 1000
    assert exc.restante == 0
    assert exc.reset > 0


@pytest.mark.asyncio
async def test_limite_49_ainda_ok() -> None:
    with patch("app.profundo.rate_limit.get_redis", return_value=_mock_redis(49)):
        info = await verificar_rate_limit("cliente_a")

    assert info.restante == 951


@pytest.mark.asyncio
async def test_redis_indisponivel_degrada_graciosamente() -> None:
    r = MagicMock()
    r.incr = AsyncMock(side_effect=ConnectionError("Redis offline"))
    with patch("app.profundo.rate_limit.get_redis", return_value=r):
        info = await verificar_rate_limit("cliente_a")

    assert info.restante == info.limite


@pytest.mark.asyncio
async def test_info_contem_reset_unix_timestamp() -> None:
    with patch("app.profundo.rate_limit.get_redis", return_value=_mock_redis(1)):
        info = await verificar_rate_limit("cliente_a")

    assert info.reset > 0
    assert info.reset % JANELA_SEGUNDOS == 0  # alinhado na hora cheia


@pytest.mark.asyncio
async def test_clientes_diferentes_sao_independentes() -> None:
    with patch("app.profundo.rate_limit.get_redis", return_value=_mock_redis(1001)):
        with pytest.raises(RateLimitError):
            await verificar_rate_limit("cliente_esgotado")

    with patch("app.profundo.rate_limit.get_redis", return_value=_mock_redis(1)):
        info = await verificar_rate_limit("cliente_ok")

    assert info.restante == 999
