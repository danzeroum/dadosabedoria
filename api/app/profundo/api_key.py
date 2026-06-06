"""Auth do tier profundo (open-core pago): chave de API por cliente.

O acervo é o MESMO público (role_analitica, sem PII) — o que se cobra é a conveniência/escala
(consulta em lote). A chave é apresentada via ``Authorization: Bearer <chave>`` ou ``X-API-Key``;
o servidor guarda só o **SHA-256** das chaves emitidas (``DEEP_API_KEYS``, CSV) — nunca a bruta.
"""

from __future__ import annotations

import hashlib

from fastapi import Request

from app.core.config import get_settings
from app.core.erros import NaoAutorizadoError


def _hashes_validos() -> set[str]:
    return {h.strip() for h in (get_settings().deep_api_keys or "").split(",") if h.strip()}


def _extrair_chave(request: Request) -> str | None:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[len("Bearer ") :].strip()
    return request.headers.get("X-API-Key")


def requer_chave_profunda(request: Request) -> str:
    """Dependency do tier profundo: 401 se a chave faltar ou não constar em ``DEEP_API_KEYS``.

    Devolve um id curto da chave (12 hex do hash) — para correlação/log, sem expor o segredo.
    """
    bruto = _extrair_chave(request)
    if not bruto:
        raise NaoAutorizadoError("chave de API ausente (tier profundo)")
    h = hashlib.sha256(bruto.encode("utf-8")).hexdigest()
    if h not in _hashes_validos():
        raise NaoAutorizadoError("chave de API inválida (tier profundo)")
    return h[:12]
