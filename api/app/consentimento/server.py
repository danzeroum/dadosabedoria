"""Serviço ISOLADO de consentimento (compose `consent`, rede `net_consentimento`).

Único componente com ``CONSENT_DATABASE_URL`` / ``APP_FIELD_KEY`` (verificado pela checagem estática
do compose). Roda como ``role_consentimento`` — a única role com acesso ao schema ``app``.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.consentimento.db import dispose_consent_engine
from app.consentimento.rotas import router as router_consent
from app.core.config import get_settings
from app.core.erros import instalar_handlers
from app.core.observabilidade import configurar_logs, configurar_otel, get_logger
from app.core.seguranca import configurar_cors

_log = get_logger("consentimento")


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    _log.info("consentimento_startup")
    yield
    await dispose_consent_engine()


def create_consent_app() -> FastAPI:
    configurar_logs()
    settings = get_settings()
    app = FastAPI(
        title="DadoSabedoria — Consentimento (PII isolada)", version="0.1.0", lifespan=lifespan
    )
    configurar_cors(app, settings)
    instalar_handlers(app)
    app.include_router(router_consent)

    @app.get("/health", tags=["infra"])
    async def health() -> dict:
        return {"status": "ok", "servico": "consentimento"}

    configurar_otel(app)
    return app


app = create_consent_app()


def main() -> None:  # pragma: no cover - entrypoint de serviço
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)  # noqa: S104  # nosec B104 - atrás do gateway


if __name__ == "__main__":  # pragma: no cover
    main()
