"""CLI para ingestão manual do ANA Monitor de Secas.

Uso:
  python -m app.ingestao.run_ana <ano>
  python -m app.ingestao.run_ana 2023
"""

from __future__ import annotations

import asyncio
import sys

from app.core.db import get_async_engine
from app.core.minio import get_store
from app.ingestao.adaptadores.ana import AdaptadorAna, FetcherAnaHTTP
from app.ingestao.adaptadores.base import Janela
from app.ingestao.pipeline import executar_ana


async def _run(ano: int) -> None:
    janela = Janela(ano=str(ano), mes=None)
    adaptador = AdaptadorAna(FetcherAnaHTTP())
    store = get_store()
    engine = get_async_engine()
    async with engine.connect() as conn:
        resumo = await executar_ana(janela, conn, adaptador, store)
        await conn.commit()
    print(f"ANA {ano}: {resumo.gravados} células gravadas, {resumo.ignorados} ignoradas.")  # noqa: T201


if __name__ == "__main__":
    if len(sys.argv) < 2:  # noqa: PLR2004
        print("Uso: python -m app.ingestao.run_ana <ano>")  # noqa: T201
        sys.exit(1)
    asyncio.run(_run(int(sys.argv[1])))
