"""CLI de backfill/execução manual: ``python -m app.ingestao.run_caged <ano> <mes>``."""

from __future__ import annotations

import asyncio
import sys

from app.core.config import get_settings
from app.core.db import connect
from app.core.observabilidade import configurar_logs
from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.caged import AdaptadorCaged, FetcherCagedFTP
from app.ingestao.bronze import construir_store_padrao
from app.ingestao.pipeline import executar_caged


async def _main(ano: int, mes: int) -> None:  # pragma: no cover - rede/S3
    configurar_logs()
    settings = get_settings()
    from app.core.cache import invalidar
    from app.indicadores.ivm import refrescar_ivm

    adaptador = AdaptadorCaged(FetcherCagedFTP())
    store = construir_store_padrao()
    async with connect(settings.database_url) as conn:
        await executar_caged(Janela(ano, mes), conn, adaptador, store, responsavel="cli")
    await refrescar_ivm()
    # Invalida todos os caches dependentes de CAGED (produto e cobertura).
    _CACHES_CAGED = (
        "v1:cobertura:caged",
        "v1:pulso",
        "v1:giro",
        "v1:salario",
        "v1:regiao",
        "v1:panorama",
        "v1:valores",
    )
    for prefixo in _CACHES_CAGED:
        await invalidar(prefixo)


def main() -> None:  # pragma: no cover - entrypoint
    if len(sys.argv) != 3:
        raise SystemExit("uso: python -m app.ingestao.run_caged <ano> <mes>")
    asyncio.run(_main(int(sys.argv[1]), int(sys.argv[2])))


if __name__ == "__main__":  # pragma: no cover
    main()
