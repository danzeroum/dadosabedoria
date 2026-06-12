"""CLI de ingestão: ``python -m app.ingestao.run_aneel <ano>`` (ANEEL DEC/FEC, anual).

Vivo-pronto: a esteira completa existe; a 1ª busca real requer ``dadosabertos.aneel.gov.br``
no allowlist do ambiente (VPS). Sem isso, o fetcher real retornará erro de rede.
"""

from __future__ import annotations

import asyncio
import sys

from app.core.config import get_settings
from app.core.db import connect
from app.core.observabilidade import configurar_logs
from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.energia import AdaptadorAneel, FetcherAneelHTTP
from app.ingestao.bronze import construir_store_padrao
from app.ingestao.pipeline import executar_aneel


async def _main(ano: int) -> None:  # pragma: no cover - rede
    configurar_logs()
    settings = get_settings()
    adaptador = AdaptadorAneel(FetcherAneelHTTP())
    store = construir_store_padrao()
    async with connect(settings.database_url) as conn:
        await executar_aneel(Janela(ano, 1), conn, adaptador, store, responsavel="cli")


def main() -> None:  # pragma: no cover - entrypoint
    if len(sys.argv) != 2:
        raise SystemExit("uso: python -m app.ingestao.run_aneel <ano>")
    asyncio.run(_main(int(sys.argv[1])))


if __name__ == "__main__":  # pragma: no cover
    main()
