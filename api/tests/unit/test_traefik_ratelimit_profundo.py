"""Checagem estática do docker-compose: router do tier profundo usa dsab-ratelimit-profundo.

Garante que POST /v1/consultas-lote e GET /v1/quota têm throttle de IP conservador na borda
(separado do dsab-ratelimit das rotas públicas) — ADR-0038.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml


def _achar_compose() -> Path:
    p = Path(__file__).resolve()
    for pai in p.parents:
        candidato = pai / "docker-compose.yml"
        if candidato.exists():
            return candidato
    pytest.skip("docker-compose.yml não encontrado")


def _achar_middlewares_yml() -> Path:
    p = Path(__file__).resolve()
    for pai in p.parents:
        candidato = pai / "infra" / "traefik" / "dynamic" / "middlewares.yml"
        if candidato.exists():
            return candidato
    pytest.skip("middlewares.yml não encontrado")


def _labels_da_api(compose: dict) -> list[str]:
    svc = compose.get("services", {}).get("api", {})
    raw = svc.get("labels", [])
    if isinstance(raw, dict):
        return [f"{k}={v}" for k, v in raw.items()]
    return [str(item) for item in raw]


def test_router_profundo_existe_no_compose() -> None:
    compose = yaml.safe_load(_achar_compose().read_text(encoding="utf-8"))
    labels = _labels_da_api(compose)
    router_labels = [lbl for lbl in labels if "api-profundo" in lbl]
    assert router_labels, "Router 'api-profundo' não encontrado nas labels do serviço api"


def test_router_profundo_usa_ratelimit_conservador() -> None:
    compose = yaml.safe_load(_achar_compose().read_text(encoding="utf-8"))
    labels = _labels_da_api(compose)
    middlewares_label = next((lbl for lbl in labels if "api-profundo.middlewares" in lbl), None)
    assert middlewares_label is not None, (
        "Label de middlewares do router api-profundo não encontrada"
    )
    assert "dsab-ratelimit-profundo" in middlewares_label, (
        "Router api-profundo deve usar dsab-ratelimit-profundo (não o dsab-ratelimit geral)"
    )
    assert "dsab-ratelimit@" not in middlewares_label, (
        "Router api-profundo não deve usar o dsab-ratelimit geral"
    )


def test_router_profundo_tem_prioridade_alta() -> None:
    compose = yaml.safe_load(_achar_compose().read_text(encoding="utf-8"))
    labels = _labels_da_api(compose)
    priority_label = next((lbl for lbl in labels if "api-profundo.priority" in lbl), None)
    assert priority_label is not None, "Label de prioridade do router api-profundo não encontrada"
    priority = int(priority_label.split("=", 1)[1])
    assert priority > 1, "Prioridade do api-profundo deve ser maior que 1 (acima do web catch-all)"


def test_middleware_profundo_mais_conservador_que_geral() -> None:
    mw = yaml.safe_load(_achar_middlewares_yml().read_text(encoding="utf-8"))
    middlewares = mw.get("http", {}).get("middlewares", {})

    assert "dsab-ratelimit" in middlewares, "dsab-ratelimit não encontrado"
    assert "dsab-ratelimit-profundo" in middlewares, "dsab-ratelimit-profundo não encontrado"

    avg_geral = middlewares["dsab-ratelimit"]["rateLimit"]["average"]
    avg_profundo = middlewares["dsab-ratelimit-profundo"]["rateLimit"]["average"]

    assert avg_profundo < avg_geral, (
        f"dsab-ratelimit-profundo ({avg_profundo} req/s) deve ser mais conservador "
        f"que dsab-ratelimit ({avg_geral} req/s)"
    )
