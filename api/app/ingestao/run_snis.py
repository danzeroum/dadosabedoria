"""CLI de ingestão: ``python -m app.ingestao.run_snis <ano>`` (SNIS, anual).

Vivo-pronto: a esteira completa existe; a 1ª busca real requer ``app4.mdr.gov.br``
no allowlist do ambiente (VPS). Sem isso, o fetcher real retornará erro de rede.
"""

from __future__ import annotations

import asyncio
import sys

from app.core.config import get_settings
from app.core.db import connect
from app.core.observabilidade import configurar_logs
from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.saneamento import AdaptadorSnis, FetcherSnisHTTP
from app.ingestao.bronze import construir_store_padrao
from app.ingestao.pipeline import executar_snis


async def _main(ano: int) -> None:  # pragma: no cover - rede
    configurar_logs()
    settings = get_settings()
    adaptador = AdaptadorSnis(FetcherSnisHTTP())
    store = construir_store_padrao()
    async with connect(settings.database_url) as conn:
        await executar_snis(Janela(ano, 1), conn, adaptador, store, responsavel="cli")


def main() -> None:  # pragma: no cover - entrypoint
    if len(sys.argv) != 2:
        raise SystemExit("uso: python -m app.ingestao.run_snis <ano>")
    asyncio.run(_main(int(sys.argv[1])))


if __name__ == "__main__":  # pragma: no cover
    main()
