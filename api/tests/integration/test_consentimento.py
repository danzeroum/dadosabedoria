"""Consentimento: ciclo LGPD + cifragem de campo + isolamento de PII, contra Postgres real."""

from __future__ import annotations

import os

import asyncpg
import pytest

from tests.helpers import asyncpg_dsn

pytestmark = pytest.mark.integration


async def _login(consent_client, email: str) -> str:
    r = await consent_client.post("/v1/auth/login", json={"email": email})
    assert r.status_code == 200
    return r.json()["sub"]


async def test_ciclo_consentir_acessar_revogar_eliminar(consent_client) -> None:
    await _login(consent_client, "cidadao@exemplo.com")
    await consent_client.delete("/v1/eu")  # começa limpo (idempotência local)

    r = await consent_client.post(
        "/v1/alertas",
        json={
            "territorio": "3550308",
            "finalidade": "alerta_qualidade_ar",
            "condicao_sensivel": "asma",
        },
    )
    assert r.status_code == 201
    aid = r.json()["id"]
    assert r.json()["condicao_sensivel"] is True

    r = await consent_client.get("/v1/alertas")
    assert [a["id"] for a in r.json()] == [aid]

    assert (await consent_client.delete(f"/v1/alertas/{aid}")).status_code == 204
    assert (await consent_client.get("/v1/alertas")).json() == []  # revogado filtrado

    assert (await consent_client.delete("/v1/eu")).status_code == 204


async def test_exige_autenticacao(consent_client) -> None:
    r = await consent_client.post("/v1/alertas", json={"territorio": "3550308", "finalidade": "ar"})
    assert r.status_code == 401
    assert r.json()["erro"] == "nao_autorizado"


async def test_pii_cifrada_e_isolada(consent_client) -> None:
    from app.consentimento.cripto import decifrar

    sub = await _login(consent_client, "asmatico@exemplo.com")
    r = await consent_client.post(
        "/v1/alertas",
        json={"territorio": "3550308", "finalidade": "ar", "condicao_sensivel": "asma"},
    )
    assert r.status_code == 201

    # role_consentimento: contato é hash; condição é cifrada (mas decifrável).
    cons = await asyncpg.connect(asyncpg_dsn(os.environ["CONSENT_DATABASE_URL"]))
    try:
        row = await cons.fetchrow(
            "SELECT a.contato_hash, c.tipo FROM app.assinante_alerta a "
            "JOIN app.condicao_sensivel c ON c.assinante_id = a.id "
            "WHERE a.contato_hash = $1 ORDER BY a.id DESC LIMIT 1",
            sub,
        )
        assert row["contato_hash"] == sub
        assert row["tipo"] != "asma"
        assert decifrar(row["tipo"]) == "asma"
    finally:
        await cons.close()

    # role_analitica: NÃO acessa o schema app (nem a nova tabela de auditoria).
    ana = await asyncpg.connect(asyncpg_dsn(os.environ["DATABASE_URL"]))
    try:
        with pytest.raises(asyncpg.InsufficientPrivilegeError):
            await ana.fetch("SELECT * FROM app.assinante_alerta LIMIT 1")
        with pytest.raises(asyncpg.InsufficientPrivilegeError):
            await ana.fetch("SELECT * FROM app.auditoria_acesso LIMIT 1")
    finally:
        await ana.close()
