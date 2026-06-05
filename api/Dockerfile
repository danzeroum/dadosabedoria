# Imagem única compartilhada por api, worker, ai e migrator (comandos diferentes no compose).
FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# asyncpg traz wheels manylinux (sem build). Sem libpq necessário.
COPY pyproject.toml ./
COPY app ./app
COPY alembic ./alembic
COPY alembic.ini ./alembic.ini
COPY scripts ./scripts

RUN pip install -U pip && pip install .

# Usuário não-root (least privilege).
RUN useradd --create-home --uid 10001 dsab && chown -R dsab:dsab /app
USER dsab

EXPOSE 8000

# Default = servir a API. worker/ai/migrator sobrescrevem o command no compose.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
