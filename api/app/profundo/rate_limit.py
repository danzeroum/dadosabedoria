"""Rate-limiting por chave de API — fixed-window counter no Redis (tier profundo).

Janela: 1 hora. Limite padrão: 1.000 req/h (configurável via ``RATE_LIMIT_PROFUNDO``).
Degradação graciosa: se o Redis estiver indisponível, permite a requisição e loga o aviso.
"""

from __future__ import annotations

from datetime import UTC, datetime
from typing import NamedTuple

from app.core.cache import get_redis
from app.core.config import get_settings
from app.core.erros import RateLimitError
from app.core.observabilidade import get_logger

_log = get_logger("rate_limit")

JANELA_SEGUNDOS = 3600  # 1 hora


class InfoRateLimit(NamedTuple):
    limite: int
    restante: int
    reset: int  # Unix timestamp da próxima janela


async def verificar_rate_limit(cliente: str) -> InfoRateLimit:
    """Incrementa o contador do cliente e retorna InfoRateLimit.

    Levanta ``RateLimitError`` se o limite foi atingido nesta janela.
    Degrada graciosamente se o Redis estiver indisponível (permite a requisição).
    """
    limite = get_settings().rate_limit_profundo
    agora = datetime.now(UTC)
    janela = agora.strftime("%Y%m%d%H")  # ex.: 2026061216
    chave = f"rl:hora:{cliente}:{janela}"
    reset = int(agora.replace(minute=0, second=0, microsecond=0).timestamp()) + JANELA_SEGUNDOS

    try:
        r = get_redis()
        contagem = int(await r.incr(chave))
        if contagem == 1:
            await r.expire(chave, JANELA_SEGUNDOS)

        if contagem > limite:
            raise RateLimitError(limite=limite, restante=0, reset=reset)

        return InfoRateLimit(limite=limite, restante=max(0, limite - contagem), reset=reset)

    except RateLimitError:
        raise
    except Exception:  # noqa: BLE001 — Redis indisponível: degrada graciosamente
        _log.warning("rate_limit_redis_falhou", cliente=cliente)
        return InfoRateLimit(limite=limite, restante=limite, reset=reset)
