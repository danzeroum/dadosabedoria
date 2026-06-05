# orchestrator — Dagster

Orquestração das esteiras de ingestão (bronze→prata→ouro). **Próxima fatia.**

Adoção em degraus (doc técnico §2.1):

1. **Degrau 1 (Onda 1):** jobs agendados (schedule mensal) por fonte, com retry e logs.
2. **Degrau 2:** indicadores como *assets* (linhagem fonte → indicador → IVM).
3. **Degrau 3:** *sensors* + *partições* por período/domínio.
4. **Degrau 4:** *backfills* gerenciados e SLAs/alertas de frescor.

Sobe pelo profile `ingestion` do `docker-compose`.
