"""Entrypoint do worker (``python -m app.worker``) — reusa a imagem da api.

Nesta fatia o worker apenas valida o ambiente e fica ocioso (a ingestão real e a orquestração
Dagster entram na próxima iteração). Mantido para paridade da imagem e do compose.
"""

from __future__ import annotations

from app.core.config import get_settings
from app.core.observabilidade import configurar_logs, get_logger


def main() -> None:
    configurar_logs()
    log = get_logger("worker")
    settings = get_settings()
    log.info("worker_pronto", servico=settings.service_name, nota="sem jobs nesta fatia")


if __name__ == "__main__":
    main()
