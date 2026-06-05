# worker — ingestão

O worker **reusa a imagem da `api`** (`build: ./api` no `docker-compose`, com
`command: python -m app.worker`). O entrypoint vive em `api/app/worker.py`.

Nesta fatia é um stub ocioso; a ingestão real (adaptadores de fonte + medallion
bronze→prata→ouro, chamando o mesmo `escrever_ouro`) entra na próxima fatia. Sobe pelo profile
`ingestion`.
