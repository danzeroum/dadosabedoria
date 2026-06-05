"""Teste OBRIGATÓRIO do quality gate (§8.1): a role analítica NÃO pode ler ``app.*``.

Se o SELECT da ``role_analitica`` em ``app`` tiver sucesso, o build REPROVA. O controle positivo
(``role_consentimento`` CONSEGUE ler) garante que a negação não passa por motivo trivial
(ex.: tabela inexistente) — o que muda é o privilégio, não a existência do objeto.
"""

from __future__ import annotations

import os

import asyncpg
import pytest

from tests.helpers import asyncpg_dsn

pytestmark = pytest.mark.integration


async def test_role_analitica_negada_no_schema_app(db_pronto: None) -> None:
    conn = await asyncpg.connect(asyncpg_dsn(os.environ["DATABASE_URL"]))
    try:
        with pytest.raises(asyncpg.InsufficientPrivilegeError):
            await conn.fetch("SELECT * FROM app.assinante_alerta LIMIT 1")
        with pytest.raises(asyncpg.InsufficientPrivilegeError):
            await conn.fetch("SELECT * FROM app.condicao_sensivel LIMIT 1")
    finally:
        await conn.close()


async def test_role_consentimento_le_app_controle_positivo(db_pronto: None) -> None:
    conn = await asyncpg.connect(asyncpg_dsn(os.environ["CONSENT_DATABASE_URL"]))
    try:
        # Não deve levantar: prova que o schema/tabelas existem e o privilégio é a única diferença.
        await conn.fetch("SELECT * FROM app.assinante_alerta LIMIT 1")
        await conn.fetch("SELECT * FROM app.condicao_sensivel LIMIT 1")
    finally:
        await conn.close()


async def test_role_analitica_le_acervo_analitico(db_pronto: None) -> None:
    # Sanidade: a role analítica PRECISA ler o acervo público.
    conn = await asyncpg.connect(asyncpg_dsn(os.environ["DATABASE_URL"]))
    try:
        n = await conn.fetchval("SELECT count(*) FROM indicador")
        assert n >= 3
    finally:
        await conn.close()
