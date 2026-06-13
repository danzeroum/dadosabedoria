"""Fábrica do app FastAPI (monólito modular).

Liga: logs estruturados, OTel, CORS por allowlist, envelope de erro, métricas Prometheus
(``/metrics`` — INTERNO, fora do schema e não roteado publicamente), ``/health`` e as rotas de
leitura. O registro de plugins agrega rotas de domínios futuros sem mexer no núcleo.
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text

from app.core.cache import fechar_redis, redis_ok
from app.core.config import get_settings
from app.core.db import dispose_engine, get_engine
from app.core.erros import instalar_handlers
from app.core.observabilidade import configurar_logs, configurar_otel, get_logger
from app.core.registro import registro
from app.core.seguranca import configurar_cors
from app.ia.rotas import router as router_ia
from app.indicadores.rotas import router as router_indicadores
from app.inferencia.rotas import router as router_inferencia
from app.produtos.rotas import router as router_produtos
from app.profundo.rotas import router as router_profundo

_log = get_logger("app")


async def _db_ok() -> bool:
    try:
        async with get_engine().connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception:  # noqa: BLE001 - readiness check
        return False


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    _log.info("startup", servico=get_settings().service_name)
    yield
    await dispose_engine()
    await fechar_redis()
    _log.info("shutdown")


def create_app() -> FastAPI:
    settings = get_settings()
    configurar_logs()

    app = FastAPI(
        title="DadoSabedoria — API pública",
        version="0.1.0",
        description="Leitura de indicadores de dados públicos brasileiros, com proveniência.",
        lifespan=lifespan,
    )

    configurar_cors(app, settings)
    instalar_handlers(app)

    @app.get("/health", include_in_schema=True, tags=["infra"])
    async def health() -> dict:
        db = await _db_ok()
        redis = await redis_ok()
        status = "ok" if (db and redis) else "degraded"
        return {"status": status, "db": db, "redis": redis, "modulos": registro.codigos}

    app.include_router(router_indicadores)
    app.include_router(router_ia)  # IA ancorada no monólito (extraível p/ o serviço `ai`)
    app.include_router(router_profundo)  # tier profundo (consultas-lote, chave de API)
    app.include_router(router_produtos)  # produtos nomeados (OndeFoi/TRANSP-06)
    app.include_router(router_inferencia)  # analytics inferencial (distribuição + perfil)

    # Encaixe de plugins de domínio (nenhum nesta fatia; rotas futuras entram aqui).
    router_dominios = APIRouter(prefix="/v1")
    registro.montar_rotas(router_dominios)
    app.include_router(router_dominios)

    # Observabilidade: OTel + métricas Prometheus internas (/metrics fora do schema público).
    configurar_otel(app, settings)
    Instrumentator().instrument(app).expose(app, endpoint="/metrics", include_in_schema=False)

    return app


app = create_app()
