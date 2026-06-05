"""Drift test (ADR-0003): as colunas de ``tables.py`` (usadas para montar consultas) precisam
existir no banco vivo. Pega divergência entre o código e o esquema canônico migrado.
"""

from __future__ import annotations

import pytest
from sqlalchemy import text

from app.core.config import get_settings
from app.core.db import connect
from app.core.tables import TABELAS_ANALITICAS

pytestmark = pytest.mark.integration


async def test_colunas_do_codigo_existem_no_banco(db_pronto: None) -> None:
    async with connect(get_settings().database_url) as conn:
        for tabela in TABELAS_ANALITICAS:
            res = await conn.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_schema='public' AND table_name=:t"
                ),
                {"t": tabela.name},
            )
            cols_db = {r[0] for r in res}
            cols_codigo = {c.name for c in tabela.columns}
            faltando = cols_codigo - cols_db
            assert not faltando, f"{tabela.name}: colunas no código ausentes no banco: {faltando}"
