"""Stub do servidor de IA ancorada (perfil compose ``ai``) — runtime chega na próxima fatia.

Mantém o contêiner vivo e ocioso. Recebe ``DATABASE_URL`` (role_analitica) — NUNCA credencial do
schema ``app`` (invariante 2). O serviço real (recuperação + guardrails + citação) virá depois.
"""

from __future__ import annotations

import time

from app.core.observabilidade import configurar_logs, get_logger


def main() -> None:  # pragma: no cover - stub de serviço
    configurar_logs()
    get_logger("ia").info("ia_stub", nota="serviço de IA ancorada chega na próxima fatia")
    while True:
        time.sleep(3600)


if __name__ == "__main__":  # pragma: no cover
    main()
