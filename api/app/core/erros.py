"""Envelope de erro padronizado (§7): ``{erro, mensagem, doc_url, trace_id}`` sem vazar interno.

500 retorna mensagem genérica; o detalhe real só vai para o log, correlacionado por ``trace_id``.
"""

from __future__ import annotations

import time
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from opentelemetry import trace

from app.core.config import get_settings
from app.core.observabilidade import get_logger

_log = get_logger("erros")


class NaoEncontradoError(Exception):
    """Recurso de domínio inexistente → 404."""

    def __init__(self, recurso: str) -> None:
        self.recurso = recurso
        super().__init__(recurso)


class ValidacaoError(Exception):
    """Entrada inválida de domínio → 400."""

    def __init__(self, mensagem: str) -> None:
        self.mensagem = mensagem
        super().__init__(mensagem)


class NaoAutorizadoError(Exception):
    """Autenticação ausente ou inválida → 401."""

    def __init__(self, mensagem: str = "não autenticado") -> None:
        self.mensagem = mensagem
        super().__init__(mensagem)


class RateLimitError(Exception):
    """Limite de requisições atingido → 429."""

    def __init__(self, limite: int, restante: int, reset: int) -> None:
        self.limite = limite
        self.restante = restante
        self.reset = reset  # Unix timestamp da próxima janela
        super().__init__(f"limite de {limite} req/h atingido")


def _trace_id() -> str:
    span = trace.get_current_span()
    ctx = span.get_span_context() if span else None
    return format(ctx.trace_id, "032x") if ctx and ctx.is_valid else "-"


def _envelope(erro: str, mensagem: str, http_status: int) -> JSONResponse:
    base = get_settings().doc_url_base
    return JSONResponse(
        status_code=http_status,
        content={
            "erro": erro,
            "mensagem": mensagem,
            "doc_url": f"{base}#{erro}",
            "trace_id": _trace_id(),
        },
    )


def instalar_handlers(app: FastAPI) -> None:
    @app.exception_handler(NaoEncontradoError)
    async def _nao_encontrado(_req: Request, exc: NaoEncontradoError) -> JSONResponse:
        return _envelope(
            "nao_encontrado", f"{exc.recurso} não encontrado.", status.HTTP_404_NOT_FOUND
        )

    @app.exception_handler(ValidacaoError)
    async def _validacao(_req: Request, exc: ValidacaoError) -> JSONResponse:
        return _envelope("validacao", exc.mensagem, status.HTTP_400_BAD_REQUEST)

    @app.exception_handler(NaoAutorizadoError)
    async def _nao_autorizado(_req: Request, exc: NaoAutorizadoError) -> JSONResponse:
        return _envelope("nao_autorizado", exc.mensagem, status.HTTP_401_UNAUTHORIZED)

    @app.exception_handler(RateLimitError)
    async def _rate_limit(_req: Request, exc: RateLimitError) -> JSONResponse:
        resp = _envelope(
            "rate_limit",
            f"Limite de {exc.limite} requisições/hora atingido.",
            status.HTTP_429_TOO_MANY_REQUESTS,
        )
        resp.headers["X-RateLimit-Limit"] = str(exc.limite)
        resp.headers["X-RateLimit-Remaining"] = "0"
        resp.headers["X-RateLimit-Reset"] = str(exc.reset)
        resp.headers["Retry-After"] = str(max(0, exc.reset - int(time.time())))
        return resp

    @app.exception_handler(RequestValidationError)
    async def _req_validacao(_req: Request, exc: RequestValidationError) -> JSONResponse:
        # Não ecoa o corpo inteiro do erro (pode vazar interno); resume.
        campos = ", ".join(".".join(str(p) for p in e.get("loc", [])) for e in exc.errors())
        return _envelope(
            "validacao", f"Parâmetros inválidos: {campos}", status.HTTP_400_BAD_REQUEST
        )

    @app.exception_handler(Exception)
    async def _interno(_req: Request, exc: Exception) -> JSONResponse:
        # Detalhe real só no log; resposta genérica (sem vazamento).
        _log.error("erro_interno", erro_tipo=type(exc).__name__)
        return _envelope("interno", "Erro interno.", status.HTTP_500_INTERNAL_SERVER_ERROR)


def cabecalho_erro(_app: Any) -> None:  # pragma: no cover - placeholder de extensão
    pass
