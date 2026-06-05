# Orquestrador (Dagster) — Degrau 1 chega na próxima fatia (Seção 2.1 do doc técnico).
# Imagem mínima válida que mantém o contêiner vivo até a implementação dos jobs/schedules.
FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1
WORKDIR /app
COPY . /app
CMD ["python", "-c", "import time; print('orchestrator (Dagster): proxima fatia'); \
import itertools; [time.sleep(3600) for _ in itertools.repeat(None)]"]
