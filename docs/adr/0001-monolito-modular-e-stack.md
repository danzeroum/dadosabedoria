# ADR-0001 — Monólito modular plugável + stack

- **Status:** aceito
- **Data:** 2026-06-05

## Contexto
Construímos a *versão fundacional permanente* (não um MVP descartável): uma base durável para
rodar anos numa VPS e evoluir sem reescrita, escalando por necessidade medida (gatilhos do doc
técnico §1.1). Precisa do menor número de processos no ar pelo maior tempo possível (invariante 6).

## Decisão
- **Monólito modular** em FastAPI (Python 3.12 + Pydantic v2): um processo `api` com módulos de
  domínio plugáveis (contrato `ModuloDominio`, §6). Extrair serviço só por dor (gatilho objetivo).
- **PostgreSQL 16 + PostGIS auto-hospedado** em docker-compose — **não** um Postgres gerenciado
  (Supabase): preserva "sem lock-in / VPS" e permite a política de isolamento de PII §8.1 (roles,
  pg_hba, redes dedicadas).
- Redis 7 (cache + eventos), MinIO (object storage, futuro), Traefik v3 (gateway), DuckDB/Polars
  (engine analítica, quando a ingestão chegar). OpenTelemetry + Prometheus/Grafana/Loki/Tempo.
- Leitura via **SQLAlchemy Core** (sem ORM declarativo); migrações via **Alembic** (ADR-0003).

## Consequências
- Operação barata e simples agora; pontos de extração já definidos pelo contrato de plugin.
- Reuso de imagem entre `api`/`worker`/`ai`/`migrator` (um Dockerfile).
- A escolha por Postgres auto-hospedado nos dá controle total do isolamento de PII (ADR-0002).
