"""Tier profundo: chaves de API no banco (emissão → valida; revogação → 401), contra DB real."""

from __future__ import annotations

import os

import pytest
from sqlalchemy import text

from app.core.db import connect
from app.profundo.chaves import emitir_chave, revogar_chave

pytestmark = pytest.mark.integration

_CORPO = {"consultas": [{"indicador": "trabalho.emprego.saldo_caged", "territorio": "3550308"}]}


async def test_chave_db_emitida_valida_e_revogada(client) -> None:
    admin = os.environ["ADMIN_DATABASE_URL"]
    cid: int | None = None
    try:
        # emissão (admin) — a chave bruta só existe aqui; o banco guarda o hash.
        async with connect(admin) as conn:
            cid, bruta = await emitir_chave(conn, "cliente-teste")

        # chave válida → 200 (validada pelo banco, sem env).
        r = await client.post(
            "/v1/consultas-lote", json=_CORPO, headers={"Authorization": f"Bearer {bruta}"}
        )
        assert r.status_code == 200
        assert r.json()["resultados"][0]["erro"] is None

        # revogação (admin) → a mesma chave passa a dar 401.
        async with connect(admin) as conn:
            assert await revogar_chave(conn, cid) is True
        r = await client.post(
            "/v1/consultas-lote", json=_CORPO, headers={"Authorization": f"Bearer {bruta}"}
        )
        assert r.status_code == 401
    finally:
        if cid is not None:
            async with connect(admin) as conn:
                await conn.execute(text("DELETE FROM chave_api WHERE id = :i"), {"i": cid})
