"""Rotação da chave de campo (anel de chaves) — re-cifra as condições sensíveis para a primária.

Roda NO contêiner de consentimento (role_consentimento, rede isolada). Pré-requisito: a chave nova
já é a ``APP_FIELD_KEY`` primária e a antiga está em ``APP_FIELD_KEYS_ANTIGAS``. O pseudônimo
(``contato_hash``) migra sozinho no login (re-chave preguiçoso); este job cuida da cifragem.

  python -m app.consentimento.run_rechave

Ver runbook docs/runbooks/rotacao-de-segredos.md.
"""

from __future__ import annotations

import asyncio

from app.consentimento.db import consent_session, dispose_consent_engine
from app.consentimento.repositorio import recifrar_condicoes
from app.core.observabilidade import configurar_logs, get_logger

_log = get_logger("rechave")


async def _run() -> int:
    try:
        async with consent_session() as session:
            return await recifrar_condicoes(session)
    finally:
        await dispose_consent_engine()


def main() -> None:  # pragma: no cover - entrypoint CLI
    configurar_logs()
    n = asyncio.run(_run())
    _log.info("rechave_concluida", recifradas=n)
    print(f"rechave: {n} condição(ões) sensível(eis) re-cifrada(s) para a chave primária")


if __name__ == "__main__":  # pragma: no cover
    main()
