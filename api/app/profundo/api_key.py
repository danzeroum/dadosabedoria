"""Auth do tier profundo (open-core pago): chave de API por cliente.

O acervo é o MESMO público (role_analitica, sem PII) — o que se cobra é a conveniência/escala. A
chave vem em ``Authorization: Bearer <chave>`` ou ``X-API-Key``. Validação em duas fontes:
- **banco** (`chave_api`, migração 0014): chaves emitidas por cliente, revogáveis (operacional);
- **env** (`DEEP_API_KEYS`, SHA-256 CSV): chaves estáticas de *break-glass*/bootstrap.
Guarda-se sempre o **hash**, nunca a chave bruta.
"""

from __future__ import annotations

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_session
from app.core.erros import NaoAutorizadoError
from app.profundo.chaves import hash_chave, validar_chave


def _hashes_env() -> set[str]:
    return {h.strip() for h in (get_settings().deep_api_keys or "").split(",") if h.strip()}


def _extrair_chave(request: Request) -> str | None:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[len("Bearer ") :].strip()
    return request.headers.get("X-API-Key")


async def requer_chave_profunda(
    request: Request, session: AsyncSession = Depends(get_session)
) -> str:
    """Dependency do tier profundo: 401 se a chave faltar ou for inválida/revogada.

    Devolve um identificador do chamador (``cliente`` da chave no banco, ou ``env:<8hex>`` no
    break-glass) — para correlação/log, sem expor o segredo.
    """
    bruto = _extrair_chave(request)
    if not bruto:
        raise NaoAutorizadoError("chave de API ausente (tier profundo)")
    if hash_chave(bruto) in _hashes_env():  # break-glass via env (bootstrap/incidente)
        return f"env:{hash_chave(bruto)[:8]}"
    cliente = await validar_chave(session, bruto)
    if cliente is None:
        raise NaoAutorizadoError("chave de API inválida (tier profundo)")
    return cliente
