"""CLI: ``python -m app.ingestao.run_siconfi_funcoes <ano>`` — execução por função (DCA anual).

OndeFoi re-ancorado (ADR-0029): Empenhado/Liquidado por função do **Anexo I-E** → fato dedicada
``execucao_funcao``. Fonte aberta (SICONFI), validada no #0 (ADR-0028).
"""

from __future__ import annotations

import asyncio
import sys

from app.core.config import get_settings
from app.core.db import connect
from app.core.observabilidade import configurar_logs
from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.siconfi import AdaptadorSiconfi, FetcherSiconfiFuncoesHTTP
from app.ingestao.bronze import construir_store_padrao
from app.ingestao.pipeline import executar_siconfi_funcoes


async def _main(ano: int) -> None:  # pragma: no cover - rede/S3
    configurar_logs()
    settings = get_settings()
    adaptador = AdaptadorSiconfi(FetcherSiconfiFuncoesHTTP())
    store = construir_store_padrao()
    async with connect(settings.database_url) as conn:
        await executar_siconfi_funcoes(Janela(ano, 1), conn, adaptador, store, responsavel="cli")


def main() -> None:  # pragma: no cover - entrypoint
    if len(sys.argv) != 2:
        raise SystemExit("uso: python -m app.ingestao.run_siconfi_funcoes <ano>")
    asyncio.run(_main(int(sys.argv[1])))


if __name__ == "__main__":  # pragma: no cover
    main()
