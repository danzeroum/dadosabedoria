"""Chaves de API do tier profundo no banco: validação (api) + emissão/revogação (admin).

Guarda-se só o **SHA-256** da chave. ``validar_chave`` roda na sessão da api (role_analitica, só
leitura); ``emitir_chave``/``revogar_chave`` rodam numa conexão **admin** (a role analítica não tem
escrita nesta tabela — migração 0014).
"""

from __future__ import annotations

import hashlib
import secrets

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession


def hash_chave(bruta: str) -> str:
    return hashlib.sha256(bruta.encode("utf-8")).hexdigest()


async def validar_chave(session: AsyncSession, bruta: str) -> str | None:
    """Devolve o cliente da chave ATIVA cujo hash bate, ou None (revogada/inexistente)."""
    return (
        await session.execute(
            text("SELECT cliente FROM chave_api WHERE chave_hash = :h AND revogada_em IS NULL"),
            {"h": hash_chave(bruta)},
        )
    ).scalar_one_or_none()


async def emitir_chave(conn: AsyncConnection, cliente: str) -> tuple[int, str]:
    """Gera uma chave aleatória, grava só o hash e devolve ``(id, chave_bruta)``.

    A chave bruta é exibida UMA vez (para entregar ao cliente) — não é recuperável depois.
    """
    bruta = secrets.token_urlsafe(32)
    cid = (
        await conn.execute(
            text("INSERT INTO chave_api (cliente, chave_hash) VALUES (:c, :h) RETURNING id"),
            {"c": cliente, "h": hash_chave(bruta)},
        )
    ).scalar_one()
    return int(cid), bruta


async def revogar_chave(conn: AsyncConnection, chave_id: int) -> bool:
    res = await conn.execute(
        text("UPDATE chave_api SET revogada_em = now() WHERE id = :i AND revogada_em IS NULL"),
        {"i": chave_id},
    )
    return (res.rowcount or 0) > 0
