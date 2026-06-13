"""CLI de ingestão: ``python -m app.ingestao.run_sisvan <ano>`` (SISVAN, anual).

Vivo-pronto: a esteira completa existe; a 1ª busca real requer
``s3.sa-east-1.amazonaws.com`` no allowlist do ambiente (VPS).
"""

from __future__ import annotations

import asyncio
import sys

from app.core.config import get_settings
from app.core.db import connect
from app.core.observabilidade import configurar_logs
from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.sisvan import AdaptadorSisvan, FetcherSisvanHTTP
from app.ingestao.bronze import construir_store_padrao
from app.ingestao.pipeline import executar_sisvan


async def _main(ano: int) -> None:  # pragma: no cover - rede
    configurar_logs()
    settings = get_settings()
    adaptador = AdaptadorSisvan(FetcherSisvanHTTP())
    store = construir_store_padrao()
    async with connect(settings.database_url) as conn:
        await executar_sisvan(Janela(ano, 1), conn, adaptador, store, responsavel="cli")


def main() -> None:  # pragma: no cover - entrypoint
    if len(sys.argv) != 2:
        raise SystemExit("uso: python -m app.ingestao.run_sisvan <ano>")
    asyncio.run(_main(int(sys.argv[1])))


if __name__ == "__main__":  # pragma: no cover
    main()
