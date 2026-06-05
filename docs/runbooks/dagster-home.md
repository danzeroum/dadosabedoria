# Runbook — Persistência do `DAGSTER_HOME`

> O `orchestrator` (Dagster Degrau 1, profile `ingestion`) guarda **histórico de runs, logs de
> eventos e estado dos agendamentos** no `DAGSTER_HOME`. Sem um volume persistente, isso vive no
> contêiner efêmero e some a cada `up`/`down` — perde-se a auditoria do que rodou e quando.

## Como está configurado

No `docker-compose.yml`, o `orchestrator` tem:

```yaml
environment:
  - DAGSTER_HOME=/dagster_home
volumes: ["dagster_home:/dagster_home"]
```

e o volume nomeado `dagster_home` na seção `volumes:`. Com o `DAGSTER_HOME` definido, o Dagster usa o
armazenamento padrão (SQLite) **dentro** desse caminho — que agora persiste entre reinícios.

## Operação

- **Inspecionar:** `docker compose --profile ingestion exec orchestrator ls -la /dagster_home`.
- **Backup do histórico (opcional):** é estado operacional, não dado de cidadão — não entra no
  runbook de PII. Se quiser retê-lo, faça `docker run --rm -v dadosabedoria_dagster_home:/d -v
  $PWD:/out alpine tar czf /out/dagster_home.tgz -C /d .` (ajuste o prefixo do projeto).
- **Reset (descartar histórico):** `docker compose down` **sem** `-v` preserva o volume; use
  `docker volume rm dadosabedoria_dagster_home` para zerar de propósito.

## Limites / evolução

- O padrão SQLite serve ao Degrau 1 (um agendador, baixa concorrência). Ao escalar (executores
  paralelos, retenção longa), migre o storage do Dagster para **Postgres** via um
  `infra/dagster/dagster.yaml` montado em `DAGSTER_HOME` (run/event/schedule storage apontando para
  um banco) — sem co-residir com o acervo analítico de produção (ADR-0005). Sinalizado.
