"""Stub do serviço ISOLADO de consentimento (perfil compose ``consent``) — runtime na próxima fatia.

É o ÚNICO serviço que recebe ``CONSENT_DATABASE_URL`` / ``APP_FIELD_KEY`` e roda na rede isolada
``net_consentimento``. Por ora apenas mantém o contêiner vivo. O caminho de escrita de PII
(assinatura de alerta, cifragem de campo, auditoria) será implementado depois.
"""

from __future__ import annotations

import time

from app.core.observabilidade import configurar_logs, get_logger


def main() -> None:  # pragma: no cover - stub de serviço
    configurar_logs()
    get_logger("consentimento").info("consent_stub", nota="serviço de consentimento (PII) futuro")
    while True:
        time.sleep(3600)


if __name__ == "__main__":  # pragma: no cover
    main()
