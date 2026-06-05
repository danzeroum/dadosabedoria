"""CLI: ``python -m app.ingestao.run_ibge <UF>`` — carrega municípios + geometrias do IBGE."""

from __future__ import annotations

import asyncio
import sys

from app.core.config import get_settings
from app.core.db import connect
from app.core.observabilidade import configurar_logs
from app.ingestao.adaptadores.ibge import AdaptadorIbge, FetcherIbgeHTTP
from app.ingestao.territorios import executar_ibge


async def _main(uf: str) -> None:  # pragma: no cover - rede
    configurar_logs()
    adaptador = AdaptadorIbge(FetcherIbgeHTTP())
    async with connect(get_settings().database_url) as conn:
        resumo = await executar_ibge(conn, adaptador, uf.upper())
    print(f"ibge {uf}: {resumo}")  # noqa: T201


def main() -> None:  # pragma: no cover - entrypoint
    if len(sys.argv) != 2:
        raise SystemExit("uso: python -m app.ingestao.run_ibge <UF>")
    asyncio.run(_main(sys.argv[1]))


if __name__ == "__main__":  # pragma: no cover
    main()
