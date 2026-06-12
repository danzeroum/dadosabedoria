"""Tier profundo: ``POST /v1/consultas-lote`` e ``GET /v1/quota`` autenticados por chave de API."""

from __future__ import annotations

import hashlib

import pytest

from app.core.config import get_settings

pytestmark = pytest.mark.integration

# Chave de baixa entropia; o HASH é computado em runtime (nada de hash hardcoded no arquivo).
_KEY = "chave-profunda-de-teste"


async def test_consultas_lote_exige_chave_e_processa_lote(client, monkeypatch) -> None:
    corpo_simples = {"consultas": [{"indicador": "trabalho.emprego.saldo_caged"}]}

    # sem chave → 401 (independe da config; nenhuma chave apresentada).
    r = await client.post("/v1/consultas-lote", json=corpo_simples)
    assert r.status_code == 401
    assert r.json()["erro"] == "nao_autorizado"

    monkeypatch.setenv("DEEP_API_KEYS", hashlib.sha256(_KEY.encode()).hexdigest())
    get_settings.cache_clear()
    try:
        # chave inválida → 401.
        r = await client.post(
            "/v1/consultas-lote", json=corpo_simples, headers={"Authorization": "Bearer errada"}
        )
        assert r.status_code == 401

        # chave válida + lote: 1 consulta boa + 1 indicador inexistente (erro no item, não 4xx).
        r = await client.post(
            "/v1/consultas-lote",
            json={
                "consultas": [
                    {"indicador": "trabalho.emprego.saldo_caged", "territorio": "3550308"},
                    {"indicador": "nao.existe"},
                ]
            },
            headers={"Authorization": f"Bearer {_KEY}"},
        )
        assert r.status_code == 200
        body = r.json()
        assert body["total"] == 2
        ok, ruim = body["resultados"]
        assert ok["erro"] is None and ok["dados"] is not None and ok["meta"] is not None
        assert ruim["erro"] is not None and ruim["dados"] is None

        # X-API-Key também é aceito.
        r = await client.post("/v1/consultas-lote", json=corpo_simples, headers={"X-API-Key": _KEY})
        assert r.status_code == 200
    finally:
        monkeypatch.delenv("DEEP_API_KEYS", raising=False)
        get_settings.cache_clear()


async def test_quota_exige_chave_e_retorna_estrutura(client, monkeypatch) -> None:
    # sem chave → 401
    r = await client.get("/v1/quota")
    assert r.status_code == 401
    assert r.json()["erro"] == "nao_autorizado"

    monkeypatch.setenv("DEEP_API_KEYS", hashlib.sha256(_KEY.encode()).hexdigest())
    get_settings.cache_clear()
    try:
        r = await client.get("/v1/quota", headers={"Authorization": f"Bearer {_KEY}"})
        assert r.status_code == 200
        body = r.json()
        assert "limite" in body
        assert "usado" in body
        assert "restante" in body
        assert "reset" in body
        assert body["limite"] > 0
        assert body["usado"] >= 0
        assert body["restante"] >= 0
        assert body["reset"] > 0
        # restante + usado == limite (ou restante == 0 quando usado > limite)
        assert body["restante"] == max(0, body["limite"] - body["usado"])
    finally:
        monkeypatch.delenv("DEEP_API_KEYS", raising=False)
        get_settings.cache_clear()
