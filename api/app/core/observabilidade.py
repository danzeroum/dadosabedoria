"""Observabilidade (§13): logs estruturados SEM PII, traces OTel, correlação por ``trace_id``.

- Logs: structlog → JSON em stdout (12-factor), com um *scrubber* de PII (denylist) e o
  ``trace_id`` injetado do contexto OTel.
- Traces: OpenTelemetry auto-instrumenta FastAPI + SQLAlchemy + Redis. Exporta via OTLP só quando
  ``OTEL_EXPORTER_OTLP_ENDPOINT`` está setado (perfil ``observability``); senão, no-op.
- Métricas Prometheus: expostas em ``/metrics`` (rota INTERNA — nunca roteada pelo entrypoint
  público do Traefik), mais as métricas de domínio em ``app.core.metricas``.
"""

from __future__ import annotations

import contextlib
import logging
from collections.abc import MutableMapping
from typing import Any

import structlog
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app.core.config import Settings, get_settings

#: Chaves que NUNCA podem aparecer em log (defesa em profundidade; a camada pública não tem PII).
_NEGADAS_PII = frozenset(
    {"contato", "contato_hash", "email", "e-mail", "telefone", "phone", "cpf", "nome_titular"}
)


def _scrubber_pii(
    _logger: Any, _metodo: str, evento: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    for chave in list(evento.keys()):
        if chave.lower() in _NEGADAS_PII:
            evento[chave] = "[REMOVIDO-PII]"
    return evento


def _injeta_trace_id(
    _logger: Any, _metodo: str, evento: MutableMapping[str, Any]
) -> MutableMapping[str, Any]:
    span = trace.get_current_span()
    ctx = span.get_span_context() if span else None
    if ctx and ctx.is_valid:
        evento["trace_id"] = format(ctx.trace_id, "032x")
        evento["span_id"] = format(ctx.span_id, "016x")
    return evento


def configurar_logs() -> None:
    logging.basicConfig(format="%(message)s", level=logging.INFO)
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            _injeta_trace_id,
            _scrubber_pii,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        cache_logger_on_first_use=True,
    )


def get_logger(nome: str = "dadosabedoria") -> Any:
    return structlog.get_logger(nome)


def configurar_otel(app: Any, settings: Settings | None = None) -> None:
    settings = settings or get_settings()
    provider = TracerProvider(resource=Resource.create({SERVICE_NAME: settings.service_name}))
    if settings.otel_exporter_otlp_endpoint:
        provider.add_span_processor(
            BatchSpanProcessor(
                OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint, insecure=True)
            )
        )
    trace.set_tracer_provider(provider)
    FastAPIInstrumentor.instrument_app(app, excluded_urls="health,metrics")
    # Instrumentadores globais: idempotência defensiva (podem já estar ligados no processo).
    for instrumentor in (SQLAlchemyInstrumentor(), RedisInstrumentor()):
        with contextlib.suppress(Exception):  # "already instrumented" não é erro
            instrumentor.instrument()
