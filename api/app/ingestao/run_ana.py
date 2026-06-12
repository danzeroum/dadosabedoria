"""CLI de ingestão: ``python -m app.ingestao.run_ana <ano>`` (ANA Monitor de Secas, anual).

Vivo-pronto: a esteira completa existe; a 1ª busca real requer ``monitordesecas.ana.gov.br``
no allowlist do ambiente (VPS). Sem isso, o fetcher real retornará erro de rede.
"""

from __future__ import annotations

import asyncio
import sys

from app.core.config import get_settings
from app.core.db import connect
from app.core.observabilidade import configurar_logs
from app.ingestao.adaptadores.ana import AdaptadorAna, FetcherAnaHTTP
from app.ingestao.adaptadores.base import Janela
from app.ingestao.bronze import construir_store_padrao
from app.ingestao.pipeline import executar_ana


async def _main(ano: int) -> None:  # pragma: no cover - rede
    configurar_logs()
    settings = get_settings()
    adaptador = AdaptadorAna(FetcherAnaHTTP())
    store = construir_store_padrao()
    async with connect(settings.database_url) as conn:
        resumo = await executar_ana(Janela(ano, 1), conn, adaptador, store, responsavel="cli")
    print(f"ANA {ano}: {resumo.registros_carregados} células gravadas.")  # noqa: T201


def main() -> None:  # pragma: no cover - entrypoint
    if len(sys.argv) != 2:
        raise SystemExit("uso: python -m app.ingestao.run_ana <ano>")
    asyncio.run(_main(int(sys.argv[1])))


if __name__ == "__main__":  # pragma: no cover
    main()
