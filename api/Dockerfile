# Imagem única compartilhada por api, worker, ai e migrator (comandos diferentes no compose).
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# asyncpg traz wheels manylinux (sem build). Sem libpq necessário.
# build-essential necessário para compilar a extensão C do pysus (datasus-dbc/DBC decoder).
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
COPY scripts ./scripts

# INSTALL_EXTRAS="" para api/worker/ai/migrator; "[orquestracao]" para o orchestrator (Dagster).
ARG INSTALL_EXTRAS=""
RUN pip install -U pip && pip install ".${INSTALL_EXTRAS}"

# Usuário não-root (least privilege) + DAGSTER_HOME gravável (orchestrator).
RUN useradd --create-home --uid 10001 dsab \
    && mkdir -p /opt/dagster/home \
    && chown -R dsab:dsab /app /opt/dagster
ENV DAGSTER_HOME=/opt/dagster/home
USER dsab

EXPOSE 8000

# Default = servir a API. worker/ai/migrator sobrescrevem o command no compose.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
