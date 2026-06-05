"""Consumo dos alertas — casa eventos de IVM **vermelho** com os assinantes e grava notificações.

Roda NO contêiner de consentimento (role_consentimento, rede isolada): é o único lugar com acesso ao
schema ``app``. Idempotente (rodar de novo não duplica). Agende após cada REFRESH do IVM.

  python -m app.consentimento.run_alertas [YYYY-MM]   # período opcional (padrão: o mais recente)
"""

from __future__ import annotations

import asyncio
import sys
from datetime import date, datetime

from app.consentimento.db import consent_session, dispose_consent_engine
from app.consentimento.repositorio import processar_alertas
from app.core.observabilidade import configurar_logs, get_logger

_log = get_logger("alertas")


def _parse_periodo(arg: str | None) -> date | None:
    if not arg:
        return None
    return datetime.strptime(arg, "%Y-%m").date().replace(day=1)


async def _run(periodo: date | None) -> int:
    try:
        async with consent_session() as session:
            return await processar_alertas(session, periodo)
    finally:
        await dispose_consent_engine()


def main() -> None:  # pragma: no cover - entrypoint CLI
    configurar_logs()
    periodo = _parse_periodo(sys.argv[1] if len(sys.argv) > 1 else None)
    novas = asyncio.run(_run(periodo))
    _log.info("alertas_processados", periodo=str(periodo or "mais_recente"), novas=novas)
    print(f"alertas: {novas} notificação(ões) nova(s)")


if __name__ == "__main__":  # pragma: no cover
    main()
