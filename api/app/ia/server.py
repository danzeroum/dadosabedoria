"""Serviço ISOLADO de IA ancorada (compose `ai`, ponto de extração do monólito).

Reusa o router de IA. Roda como ``role_analitica`` — **sem** credencial do schema ``app``
(invariante 2; verificado pela checagem estática do compose). Por ora a IA também é servida pelo
monólito (api); este processo separado é a fronteira de extração quando bater a dor (§1.1).
"""

from __future__ import annotations

from fastapi import FastAPI

from app.core.erros import instalar_handlers
from app.core.observabilidade import configurar_logs, configurar_otel
from app.ia.rotas import router as router_ia


def create_ai_app() -> FastAPI:
    configurar_logs()
    app = FastAPI(title="DadoSabedoria — IA ancorada", version="0.1.0")
    instalar_handlers(app)
    app.include_router(router_ia)

    @app.get("/health", tags=["infra"])
    async def health() -> dict:
        return {"status": "ok", "servico": "ia"}

    configurar_otel(app)
    return app


app = create_ai_app()


def main() -> None:  # pragma: no cover - entrypoint de serviço
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)  # noqa: S104  # nosec B104 - atrás do gateway


if __name__ == "__main__":  # pragma: no cover
    main()
