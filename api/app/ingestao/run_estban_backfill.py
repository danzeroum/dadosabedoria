"""Backfill ESTBAN: carrega um intervalo de competências de uma só vez.

Uso:
  python -m app.ingestao.run_estban_backfill <ano_ini> <mes_ini> <ano_fim> <mes_fim>

Exemplo (últimas 6 competências publicadas — lag ~2 meses, ESTBAN publica T-2):
  python -m app.ingestao.run_estban_backfill 2024 6 2025 12

Cada competência é idempotente: re-rodar não duplica dados.
Requer FetcherEstbanHTTP funcional (URL BCB confirmada — ver diagnostico_estban.py).
"""

from __future__ import annotations

import asyncio
import sys
from datetime import date

from app.core.config import get_settings
from app.core.db import connect
from app.core.observabilidade import configurar_logs
from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.estban import AdaptadorEstban, FetcherEstbanHTTP
from app.ingestao.bronze import construir_store_padrao
from app.ingestao.pipeline import executar_estban


def _janelas(ano_ini: int, mes_ini: int, ano_fim: int, mes_fim: int) -> list[Janela]:
    ini = date(ano_ini, mes_ini, 1)
    fim = date(ano_fim, mes_fim, 1)
    result: list[Janela] = []
    cur = ini
    while cur <= fim:
        result.append(Janela(cur.year, cur.month))
        if cur.month == 12:
            cur = date(cur.year + 1, 1, 1)
        else:
            cur = date(cur.year, cur.month + 1, 1)
    return result


async def _main(ano_ini: int, mes_ini: int, ano_fim: int, mes_fim: int) -> None:  # pragma: no cover
    configurar_logs()
    settings = get_settings()
    from app.indicadores.ivm import refrescar_ivm

    # skip_rows=2: arquivos reais do BCB têm 2 linhas de preâmbulo antes do cabeçalho.
    adaptador = AdaptadorEstban(FetcherEstbanHTTP(), skip_rows=2)
    store = construir_store_padrao()
    janelas = _janelas(ano_ini, mes_ini, ano_fim, mes_fim)
    ini_comp, fim_comp = janelas[0].competencia, janelas[-1].competencia
    print(f"Backfill ESTBAN: {len(janelas)} competências ({ini_comp}..{fim_comp})")

    async with connect(settings.database_url) as conn:
        for j in janelas:
            print(f"  → {j.competencia} ...", end=" ", flush=True)
            try:
                r = await executar_estban(j, conn, adaptador, store, responsavel="backfill")
                print(f"registros={r.registros_carregados} suprimidos={r.suprimidos}")
            except Exception as exc:
                print(f"ERRO: {exc}")

    await refrescar_ivm()
    print("Backfill ESTBAN concluído.")


def main() -> None:  # pragma: no cover
    if len(sys.argv) != 5:
        raise SystemExit(
            "uso: python -m app.ingestao.run_estban_backfill"
            " <ano_ini> <mes_ini> <ano_fim> <mes_fim>"
        )
    asyncio.run(_main(int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])))


if __name__ == "__main__":  # pragma: no cover
    main()
