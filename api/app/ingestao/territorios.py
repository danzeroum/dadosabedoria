"""Carga estrutural de territórios do IBGE: registro de municípios + geometrias (PostGIS).

Não é fato (não passa por ``escrever_ouro``): atualiza a dimensão ``territorio``. Roda como
``role_analitica`` (INSERT/UPDATE em public). Idempotente (upsert / update por código).
"""

from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core import tables as t
from app.core.observabilidade import get_logger
from app.ingestao.adaptadores.ibge import AdaptadorIbge

_log = get_logger("ingestao.ibge")


async def carregar_municipios(conn: AsyncConnection, municipios: list[dict[str, Any]]) -> int:
    ufs = {
        str(r[0]): int(r[1])
        for r in await conn.execute(text("SELECT codigo_ibge, id FROM territorio WHERE nivel='uf'"))
    }
    n = 0
    for m in municipios:
        valores = {
            "codigo_ibge": m["codigo_ibge"],
            "nome": m["nome"],
            "nivel": "municipio",
            "uf": m.get("uf"),
            "pai_id": ufs.get(m.get("uf_id") or ""),
        }
        stmt = pg_insert(t.territorio).values(**valores)
        stmt = stmt.on_conflict_do_update(
            index_elements=["codigo_ibge"],
            set_={
                "nome": stmt.excluded.nome,
                "uf": stmt.excluded.uf,
                "pai_id": stmt.excluded.pai_id,
            },
        )
        await conn.execute(stmt)
        n += 1
    return n


async def carregar_geometrias(conn: AsyncConnection, malha: dict[str, str]) -> int:
    n = 0
    for codigo_ibge, geom in malha.items():
        res = await conn.execute(
            text(
                "UPDATE territorio SET geom = ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(:g), 4674)) "
                "WHERE codigo_ibge = :c"
            ),
            {"g": geom, "c": codigo_ibge},
        )
        n += res.rowcount or 0
    return n


async def executar_ibge(conn: AsyncConnection, adaptador: AdaptadorIbge, uf: str) -> dict[str, int]:
    """Carrega os municípios de uma UF (registro + geometrias)."""
    municipios = [m for m in adaptador.municipios() if m.get("uf") == uf]
    n_mun = await carregar_municipios(conn, municipios)
    n_geom = await carregar_geometrias(conn, adaptador.malha(uf))
    _log.info("ibge_carregado", uf=uf, municipios=n_mun, geometrias=n_geom)
    return {"municipios": n_mun, "geometrias": n_geom}
