# ADR-0005 — Economia de recurso na VPS (4 vCPU / 16 GB)

- **Status:** aceito
- **Data:** 2026-06-05

## Contexto
A plataforma roda numa VPS de ~4 vCPU / 16 GB. Invariante 6 (economia de recurso) e a própria
filosofia de gatilhos (§1.1) valem para nós mesmos: não manter serviço ocioso de pé, e medir antes
de escalar.

## Decisão
1. **Stack mínima default = `proxy/api/db/redis` + `migrator`** (one-shot). `docker compose up` sobe
   só isto. Isso **enxuga conscientemente** a lista literal de stack mínima do doc técnico §9 (que
   incluía MinIO) por economia: na fundação nada escreve bronze/parquet.
2. **MinIO entra com a ingestão** (profile `ingestion`, junto de `worker`/`orchestrator`).
3. **Postgres tunado para 16 GB** (`infra/postgres/postgresql.conf`: `shared_buffers≈4GB`,
   `effective_cache_size≈12GB`, etc.) — para o p95 refletir carga real, não default conservador
   (mantém honesto o gatilho "migrar Postgres" a p95 > 300 ms).
4. **`/metrics` é interno** — nunca roteado pelo entrypoint público do Traefik (evita vazar
   cardinalidade/throughput).
5. **Observabilidade é opt-in** (profile `observability`). São 5 serviços pesados; **não** devem
   co-residir com api + ingestão na VPS em produção — usar retenção curta (Loki/Tempo a 7 dias) ou
   um agente leve (ex.: Grafana Alloy) exportando para fora. Item de capacidade conhecido.

## Consequências
- Menor RAM fixa e operação mais simples na fundação.
- A telemetria pesada é ligada sob demanda; a estratégia de produção para observabilidade fica
  registrada como próximo passo de capacidade.
