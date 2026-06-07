"""CLI de backfill/execução: ``python -m app.ingestao.run_pncp <ano>`` (contratos PNCP, anual).

Vivo-pronto: a esteira completa roda; a 1ª busca real (host ``pncp.gov.br`` no allowlist) confirma a
forma. Sem isso, o fetcher real responde 403 (contêiner github-only).
"""

from __future__ import annotations

import asyncio
import sys

from app.core.config import get_settings
from app.core.db import connect
from app.core.observabilidade import configurar_logs
from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.pncp import AdaptadorPncp, FetcherPncpHTTP
from app.ingestao.bronze import construir_store_padrao
from app.ingestao.pipeline import executar_pncp


async def _main(ano: int) -> None:  # pragma: no cover - rede/S3
    configurar_logs()
    settings = get_settings()
    adaptador = AdaptadorPncp(FetcherPncpHTTP())
    store = construir_store_padrao()
    async with connect(settings.database_url) as conn:
        await executar_pncp(Janela(ano, 1), conn, adaptador, store, responsavel="cli")


def main() -> None:  # pragma: no cover - entrypoint
    if len(sys.argv) != 2:
        raise SystemExit("uso: python -m app.ingestao.run_pncp <ano>")
    asyncio.run(_main(int(sys.argv[1])))


if __name__ == "__main__":  # pragma: no cover
    main()
