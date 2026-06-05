# ADR-0003 — Migrações Alembic (autogenerate OFF) + SQLAlchemy Core para leitura

- **Status:** aceito
- **Data:** 2026-06-05

## Contexto
O esquema canônico (documento *Esquema do repositório de indicadores* §3) é DDL escrito à mão com
recursos específicos do Postgres (ENUMs, `GENERATED ALWAYS AS IDENTITY`, PostGIS, view, RLS). Ele
é a fonte da verdade do modelo de dados e não pode derivar. Mudanças não podem quebrar o passado
(invariante 4).

## Decisão
- **Alembic assíncrono**, com **autogenerate DESLIGADO**: cada migração é DDL escrito à mão
  (`op.execute`) a partir do esquema canônico, em revisões ordenadas `0001`–`0009`.
- **Expand-and-contract** para toda evolução: adicionar coluna nullable → backfill → migrar leitura
  → (deploy separado) restringir/remover. As migrações desta fatia são todas "expand" (criação).
- **Leitura com SQLAlchemy Core** (definições `Table` em `app/core/tables.py` só para montar
  consultas — não autoritativas), **sem ORM declarativo**: consultas parametrizadas, explícitas e
  sem N+1. ENUMs usam tipos PG nativos (`create_type=False`) para ligar valor como enum.
- **Drift test** no quality gate: confere que as colunas de `tables.py` existem no banco vivo.

## Consequências
- Zero divergência entre o esquema canônico e o que o Alembic emite.
- Roles globais ao cluster são criadas por migração guardada (`pg_roles`), rodada pelo migrator
  como superusuário (não por `initdb.d`, que só roda na primeira inicialização do volume).
