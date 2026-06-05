"""Cache de leitura (Decorator) sobre Redis — só dado público (§8), com degradação graciosa.

Caminhos quentes pré-computados/cacheados (invariante 6). Se o Redis estiver indisponível, a
função original é chamada (servir mesmo degradado). Apenas dado público transita aqui — a camada
pública já é não-pessoal e suprimida.
"""

from __future__ import annotations

import functools
import json
from collections.abc import Awaitable, Callable
from typing import Any, TypeVar, get_type_hints

import redis.asyncio as aioredis
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.observabilidade import get_logger

_log = get_logger("cache")
_cliente: aioredis.Redis | None = None
T = TypeVar("T")


def get_redis() -> aioredis.Redis:
    global _cliente
    if _cliente is None:
        _cliente = aioredis.from_url(get_settings().redis_url, decode_responses=True)
    return _cliente


async def redis_ok() -> bool:
    try:
        return bool(await get_redis().ping())
    except Exception:  # noqa: BLE001 - readiness check
        return False


def _chave(prefixo: str, kwargs: dict[str, Any]) -> str:
    partes = [f"{k}={kwargs[k]}" for k in sorted(kwargs)]
    return f"{prefixo}:" + ":".join(partes)


def cache_leitura(
    prefixo: str, ttl: int | None = None
) -> Callable[[Callable[..., Awaitable[T]]], Callable[..., Awaitable[T]]]:
    """Cacheia o retorno (BaseModel ou JSON-serializável) de uma corrotina chamada por kwargs."""

    def deco(fn: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        tipo_retorno = get_type_hints(fn).get("return")

        @functools.wraps(fn)
        async def wrapper(*args: Any, **kwargs: Any) -> T:
            settings = get_settings()
            chave = _chave(prefixo, kwargs)
            r = get_redis()
            try:
                bruto = await r.get(chave)
                if bruto is not None:
                    if isinstance(tipo_retorno, type) and issubclass(tipo_retorno, BaseModel):
                        return tipo_retorno.model_validate_json(bruto)  # type: ignore[return-value]
                    return json.loads(bruto)
            except Exception:  # noqa: BLE001 - cache nunca derruba a leitura
                _log.warning("cache_get_falhou", chave=chave)

            resultado = await fn(*args, **kwargs)

            try:
                payload = (
                    resultado.model_dump_json()
                    if isinstance(resultado, BaseModel)
                    else json.dumps(resultado, default=str)
                )
                await r.set(chave, payload, ex=ttl or settings.cache_ttl_segundos)
            except Exception:  # noqa: BLE001
                _log.warning("cache_set_falhou", chave=chave)
            return resultado

        return wrapper

    return deco


async def invalidar(prefixo: str) -> None:
    """Remove do cache todas as chaves com o prefixo dado (ex.: após refresh do IVM)."""
    try:
        r = get_redis()
        chaves = [chave async for chave in r.scan_iter(match=f"{prefixo}*")]
        if chaves:
            await r.delete(*chaves)
    except Exception:  # noqa: BLE001 - invalidação nunca derruba a operação
        _log.warning("cache_invalidar_falhou", prefixo=prefixo)


async def fechar_redis() -> None:
    global _cliente
    if _cliente is not None:
        await _cliente.aclose()
    _cliente = None
