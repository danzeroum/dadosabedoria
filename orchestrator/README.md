# orchestrator — Dagster (Degrau 1)

Orquestra a esteira de ingestão. **Reusa a imagem da `api`** (`docker-compose` faz
`build: ./api` com `INSTALL_EXTRAS=[orquestracao]`), e roda
`dagster dev -m app.orquestracao.definitions`. As definições vivem em
`api/app/orquestracao/definitions.py` para compartilhar o código de pipeline.

**Degrau 1 (esta fatia):** job agendado (`schedule_caged_mensal`, cron mensal) que dispara a
esteira CAGED bronze→prata→ouro pelo mesmo `escrever_ouro`, com retry e logs.

Próximos degraus (por dor, §2.1): assets com linhagem nativa; sensors + partições; backfills e
SLAs/alertas de frescor. Persistência do `DAGSTER_HOME` (volume + ownership) é hardening de
Degrau 2.

Sobe pelo profile `ingestion` do `docker-compose` (junto de `minio` e `worker`). A UI/daemon fica
na porta 3000, **interna** (não roteada pelo proxy público).
