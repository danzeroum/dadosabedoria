"""CLI de backfill/execução manual.

Uso:
  python -m app.ingestao.run_caged <ano> <mes>                    # competência única
  python -m app.ingestao.run_caged <ano_ini> <mes_ini> <ano_fim> <mes_fim>  # intervalo inclusivo
"""

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


def _janelas(ano_ini: int, mes_ini: int, ano_fim: int, mes_fim: int) -> list[Janela]:
    """Gera todas as competências no intervalo [ini, fim] inclusive."""
    result: list[Janela] = []
    ano, mes = ano_ini, mes_ini
    while (ano, mes) <= (ano_fim, mes_fim):
        result.append(Janela(ano, mes))
        mes += 1
        if mes > 12:
            mes = 1
            ano += 1
    return result


async def _main(janelas: list[Janela]) -> None:  # pragma: no cover - rede/S3
    configurar_logs()
    settings = get_settings()
    from app.core.cache import invalidar
    from app.indicadores.ivm import refrescar_ivm

    adaptador = AdaptadorCaged(FetcherCagedFTP())
    store = construir_store_padrao()
    async with connect(settings.database_url) as conn:
        for janela in janelas:
            await executar_caged(janela, conn, adaptador, store, responsavel="cli")
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
    if len(sys.argv) == 3:
        ano, mes = int(sys.argv[1]), int(sys.argv[2])
        janelas = _janelas(ano, mes, ano, mes)
    elif len(sys.argv) == 5:
        janelas = _janelas(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4]))
    else:
        raise SystemExit("uso: python -m app.ingestao.run_caged <ano> <mes> [<ano_fim> <mes_fim>]")
    asyncio.run(_main(janelas))


if __name__ == "__main__":  # pragma: no cover
    main()
