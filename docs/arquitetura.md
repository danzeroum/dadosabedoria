# Arquitetura — versão fundacional

Stack mínima (default) em contêineres na VPS, com serviços opt-in por profile. Detalhes em
ADR-0001 (stack), ADR-0002 (isolamento de PII) e ADR-0005 (economia de recurso).

```mermaid
flowchart TB
  subgraph EXT[Externo]
    LLMP[Provedor de LLM]
    FON[Fontes públicas: IBGE, CAGED, BCB ...]
  end

  subgraph HOST[VPS - docker-compose]
    subgraph CORE[rede net_core - stack mínima default]
      PX[proxy Traefik: TLS, rate-limit, CORS]
      API[api FastAPI - monólito modular]
      RD[(redis: cache + eventos)]
      DB[(Postgres + PostGIS)]
      MIG[migrator one-shot: migra + semeia]
    end

    subgraph OPT[opt-in por profile]
      WK[worker - ingestão]
      ORQ[orchestrator - Dagster]
      OBJ[(MinIO: bronze + parquet)]
      AI[ai: IA ancorada]
      OBS[observability: otel/prometheus/grafana/loki/tempo]
    end

    subgraph CONS[rede net_consentimento - ISOLADA]
      CSV[consentimento - PII]
      APP[(schema app)]
    end
  end

  WEB[web Next.js - próxima fatia] --> PX --> API
  API --> DB
  API --> RD
  MIG --> DB
  FON -. próxima fatia .-> WK --> OBJ
  WK --> DB
  ORQ --> WK
  AI --> DB
  AI --> LLMP
  CSV --> APP
  DB --- APP

  classDef future stroke-dasharray: 4 4;
  class WK,ORQ,OBJ,AI,OBS,WEB,CSV,APP future;
```

Notas:
- `api`/`worker`/`ai` usam `role_analitica` (sem acesso a `app`). `/metrics` é interno (não roteado
  publicamente).
- O serviço de consentimento é o único com `CONSENT_DATABASE_URL`/`APP_FIELD_KEY`, em rede isolada;
  a `ai` não compartilha rede com ele.
- Tudo tracejado é fronteira pronta mas implementada em fatias seguintes.
