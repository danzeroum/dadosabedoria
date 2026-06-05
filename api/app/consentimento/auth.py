"""Autenticação do cidadão — JWT curto em cookie HttpOnly (proposta v1, ADR-0012).

OIDC real é plugue futuro: aqui um login simples emite o JWT cujo ``sub`` é o ``contato_hash``
(pseudônimo do cidadão). Token nunca em localStorage (§8): só cookie HttpOnly+SameSite.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import jwt
from fastapi import Request, Response

from app.core.config import get_settings
from app.core.erros import NaoAutorizadoError

COOKIE = "dsab_sessao"
_ALGO = "HS256"
_TTL_MIN = 30


def emitir_token(sub: str) -> str:
    agora = datetime.now(UTC)
    payload = {"sub": sub, "iat": agora, "exp": agora + timedelta(minutes=_TTL_MIN)}
    return jwt.encode(payload, get_settings().jwt_secret, algorithm=_ALGO)


def definir_cookie(resposta: Response, token: str) -> None:
    resposta.set_cookie(
        COOKIE,
        token,
        httponly=True,
        secure=get_settings().is_prod,
        samesite="strict",  # mitigação CSRF (mutações); token anti-CSRF é hardening futuro
        max_age=_TTL_MIN * 60,
        path="/",
    )


def limpar_cookie(resposta: Response) -> None:
    resposta.delete_cookie(COOKIE, path="/")


def cidadao_atual(request: Request) -> str:
    """Dependency: devolve o ``contato_hash`` do cidadão autenticado, ou 401."""
    token = request.cookies.get(COOKIE)
    if not token:
        raise NaoAutorizadoError("não autenticado")
    try:
        payload = jwt.decode(token, get_settings().jwt_secret, algorithms=[_ALGO])
    except jwt.PyJWTError as exc:
        raise NaoAutorizadoError("sessão inválida ou expirada") from exc
    return str(payload["sub"])
