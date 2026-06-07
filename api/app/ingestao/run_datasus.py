"""CLI de backfill/execução: ``python -m app.ingestao.run_datasus <ano> <mes>`` (SIH/SUS, mensal).

Origem SENSÍVEL: a contagem de AIH é o ``n_amostra`` → k-anon no caminho ouro protege contagens
pequenas. Saúde é subíndice do IVM → refresca a MV após a carga. Vivo-pronto: a 1ª busca real (host
``ftp.datasus.gov.br`` no allowlist) confirma a forma; sem isso o fetcher responde 403/timeout.
"""

from __future__ import annotations

import asyncio
import sys

from app.core.config import get_settings
from app.core.db import connect
from app.core.observabilidade import configurar_logs
from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.datasus import AdaptadorDatasus, FetcherDatasusFTP
from app.ingestao.bronze import construir_store_padrao
from app.ingestao.pipeline import executar_datasus


async def _main(ano: int, mes: int) -> None:  # pragma: no cover - rede/dbc
    configurar_logs()
    settings = get_settings()
    from app.indicadores.ivm import refrescar_ivm

    adaptador = AdaptadorDatasus(FetcherDatasusFTP())
    store = construir_store_padrao()
    async with connect(settings.database_url) as conn:
        await executar_datasus(Janela(ano, mes), conn, adaptador, store, responsavel="cli")
    await refrescar_ivm()  # saúde é subíndice do IVM completo (ADR-0025)


def main() -> None:  # pragma: no cover - entrypoint
    if len(sys.argv) != 3:
        raise SystemExit("uso: python -m app.ingestao.run_datasus <ano> <mes>")
    asyncio.run(_main(int(sys.argv[1]), int(sys.argv[2])))


if __name__ == "__main__":  # pragma: no cover
    main()
