# DadoSabedoria

Plataforma de inteligência de **dados públicos brasileiros** que transforma dado governamental
aberto em ação cívica (conceito **Valor Triplo**; modelo **Open-Core Cívico**). O ativo do negócio
é a **confiança** — privacidade estrutural, proveniência e qualidade comprovada existem para
protegê-la a cada commit.

Este repositório contém a **versão fundacional permanente**: a primeira base operacional durável
(não um MVP descartável). Esta fatia entrega a fundação executável + a API de leitura.

## O que já existe nesta fatia

- Esquema canônico de indicadores (`indicador × território × período → valor`) com PostGIS, mais o
  **schema `app` isolado** para PII (roles, grants, RLS, rede).
- **Regra única de supressão (k-anonimato)** aplicada **antes** de gravar, num **único** ponto de
  escrita (camada ouro) — usada igualmente por *seeds* e (futuramente) pela ingestão.
- **API pública de leitura** (`/v1/indicadores`, `/v1/valores`, `/v1/territorios`) com **proveniência
  no `meta`** (fonte, método, lag, licença), paginação e envelope de erro padronizado.
- **Teste de isolamento de PII** que **reprova o build** se a role analítica conseguir ler `app.*`.
- Observabilidade (logs JSON sem PII, traces OTel, `/metrics` interno, `/health`) e **quality gate**
  no CI (lint, mypy, bandit, testes, cobertura, contrato OpenAPI, scan de deps/segredos).

A **Onda 1 está completa**: ingestão real de **CAGED**, **BCB/ESTBAN** e **IBGE** (malhas), o
**IVM** (view materializada), o **frontend** Next.js com **coropleta geográfica** + drill-down, e a
**IA ancorada** (`POST /v1/ia/perguntar`, isolada do schema `app`; narrador real opcional —
**DeepSeek** ou **Ollama** via API OpenAI-compatível, só por config, sempre ancorado)
e o **runtime de consentimento** — serviço ISOLADO que escreve PII no schema `app` via
`role_consentimento` (rede isolada), com cifragem de campo, trilha de auditoria, auth do cidadão
(JWT em cookie HttpOnly) e o ciclo LGPD completo (`/v1/alertas`, `/v1/eu`). O ciclo fecha com o
**consumo dos alertas**: quando o IVM de um território entra em **vermelho**, o serviço de
consentimento casa o evento (IVM público) com os assinantes e grava uma notificação — entrega
**pull** (`GET /v1/notificacoes`, autenticado; o contato bruto nunca é guardado). Veja os ADRs
0006–0015. O **plano de execução** (ondas, backlog e decisões pendentes) vive em
[`docs/roadmap.md`](docs/roadmap.md); próximos passos imediatos: anel de chaves p/ rotação da
`APP_FIELD_KEY`; agendamento do consumo após o REFRESH do IVM; OIDC real do cidadão. Veja também
`docs/adr/` e o documento técnico.

## Invariantes inegociáveis

1. Privacidade estrutural — grão território×período; sem chave de pessoa; supressão antes de gravar.
2. Isolamento de PII — dado pessoal só no schema `app`; role analítica não o acessa (testado).
3. IA ancorada — só afirma o recuperado, com citação (fatia futura).
4. Não quebrar o passado — API aditiva; migração expand-and-contract.
5. Proveniência sempre — todo valor/resposta carrega fonte, método e lag.
6. Economia de recurso — pré-computar/cachear/incremental; medir antes de otimizar.
7. Qualidade comprovada — nada faz merge sem o quality gate verde.
8. Segredo nunca no código — tudo por variável de ambiente.

## Como rodar (docker-compose)

Pré-requisitos: Docker + Docker Compose.

```bash
cp .env.example .env      # troque os segredos (CHANGE_ME). As senhas das DSNs criam as roles.
docker compose up --build # sobe a stack MÍNIMA: proxy, api, db, redis (+ migrator one-shot)
```

O `migrator` aplica as migrações (como superusuário) e semeia (como `role_analitica`); a `api` só
atende depois disso. Então:

```bash
curl http://localhost/health
curl "http://localhost/v1/indicadores?dominio=trabalho"
curl "http://localhost/v1/valores?indicador=trabalho.emprego.saldo_caged&territorio=3550308"
curl http://localhost/v1/territorios/3550308
```

> `/metrics` é **interno** (não roteado pelo proxy público).

### Profiles (opt-in)

| Profile          | Sobe                                              | Quando                     |
|------------------|---------------------------------------------------|----------------------------|
| _(default)_      | proxy, api, db, redis, migrator                   | sempre                     |
| `ingestion`      | minio, worker, orchestrator                       | ao iniciar a ingestão      |
| `ai`             | ai (IA ancorada)                                  | fatia de IA                |
| `consent`        | consentimento (PII, rede isolada)                 | fatia de alertas/consent.  |
| `observability`  | otel-collector, prometheus, grafana, loki, tempo  | depuração/observação       |

```bash
docker compose --profile observability up
```

## Ingestão (Onda 1 — CAGED + BCB/ESTBAN)

Esteiras **bronze→prata→ouro** que passam pela MESMA regra de supressão da fundação e gravam
`linhagem` (URL de origem + hash do bruto). Adaptadores com fetcher injetável (testáveis sem rede),
transform em Polars, bronze em MinIO. O *tail* de carga é compartilhado entre as fontes.

- **CAGED** → `trabalho.emprego.saldo_caged` (saldo de emprego por município/mês). ADR-0006.
- **BCB/ESTBAN** → `credito.operacoes.saldo_total` (crédito por município/mês). ADR-0007.

```bash
# execução manual / backfill
python -m app.ingestao.run_caged <ano> <mes>     # ex.: 2026 4
python -m app.ingestao.run_estban <ano> <mes>
python -m app.ingestao.run_ibge <UF>             # ex.: SP — municípios + geometrias (coropleta)

# agendada (Dagster Degrau 1): jobs/schedules mensais no serviço orchestrator
docker compose --profile ingestion up            # minio + worker + orchestrator (Dagster, UI interna :3000)
```

Os fetchers reais baixam do FTP público do PDET (CAGED) e do BCB (ESTBAN); parse/agregação são
cobertos por fixture.

## IVM (Índice de Vulnerabilidade Municipal)

A vista de topo que agrega os domínios (TRANSP-01): combina os subíndices de **emprego** (CAGED) e
**finanças** (ESTBAN), normalizados e ponderados, num índice 0–100 por município/mês — maior = mais
vulnerável; semáforo verde/amarelo/vermelho. É uma **view materializada** (leitura O(1)), recomputada
após cada ingestão. Metodologia v1 em ADR-0008.

- `GET /v1/ivm?periodo=YYYY-MM` — IVM de todos os municípios no período (base do **mapa semafórico**;
  padrão = período mais recente).
- `GET /v1/ivm/{codigo_ibge}` — série do IVM de um município (**drill-down**).

## Como testar

```bash
cd api
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# unidade (rápido, sem banco): supressão, single-call-site, isolamento de creds no compose
pytest -m "not integration"

# integração (precisa de Postgres+PostGIS e Redis); exporte as DSNs e rode:
export ADMIN_DATABASE_URL=postgresql+asyncpg://postgres:PWD@localhost:5432/dadosabedoria
export DATABASE_URL=postgresql+asyncpg://role_analitica:PWD@localhost:5432/dadosabedoria
export CONSENT_DATABASE_URL=postgresql+asyncpg://role_consentimento:PWD@localhost:5432/dadosabedoria
export REDIS_URL=redis://localhost:6379/0
pytest --cov=app           # roda migra+seed via fixture, depois integração + cobertura
```

Qualidade local: `ruff check . && ruff format --check . && mypy app && bandit -r app`.
Exportar o contrato: `python scripts/export_openapi.py` (gera `docs/openapi.yaml`).

## A garantia de isolamento de PII

Dado pessoal vive **só** no schema `app`, acessível **só** pela `role_consentimento`, em rede
isolada. A `role_analitica` (api/worker/ai) tem `REVOKE ALL` em `app`. Um teste de integração
assume a role analítica e tenta ler `app.*`: **deve falhar com permissão negada**; um controle
positivo prova que a `role_consentimento` consegue. Se a leitura analítica tiver sucesso, **o build
reprova**. Veja `docs/adr/0002-isolamento-de-pii.md`.

## Operação (runbooks)

Procedimentos operacionais em `docs/runbooks/` (ADR-0013):

- **Backup & restauração** (`backup-restore.md`, `scripts/backup.sh` + `scripts/restore.sh`) — o
  backup do **`app` (PII)** é **separado** do analítico e **cifrado** (gpg AES256), com retenção
  própria mais curta (minimização LGPD). O dump analítico roda como `role_analitica` — que não lê
  `app` — então não pode conter PII (testado, estático + vivo no CI). Dumps são só de dados; o
  esquema vem de `alembic upgrade head`.
- **Rotação de segredos** (`rotacao-de-segredos.md`) — senhas de role e `JWT_SECRET` (diretos);
  `APP_FIELD_KEY` exige anel de chaves (re-chaveamento) — sinalizado.
- **Persistência do Dagster** (`dagster-home.md`) — volume `dagster_home` guarda o histórico de runs.

```bash
DATABASE_URL=… CONSENT_DATABASE_URL=… BACKUP_PASSPHRASE=… scripts/backup.sh
```

## Estrutura

```
api/            backend FastAPI (monólito modular) + alembic + testes
  app/core/       config, db, cache, observabilidade, erros, registro de plugins, tables
  app/indicadores/ serviço de leitura (Facade + Repository) + rotas + modelos
  app/ingestao/    supressao.py (regra única) + ouro.py (único ponto de escrita)
                   + adaptadores/ (CAGED), bronze.py, pipeline.py (medallion)
  app/orquestracao/ Dagster Degrau 1 (job + schedule da esteira CAGED)
  app/domains/trabalho/  primeiro plugin de domínio (contrato ModuloDominio)
  app/seed/        seed pela MESMA regra de supressão da ingestão
  app/ia, app/consentimento  fronteiras isoladas (stubs nesta fatia)
docs/           ADRs, openapi.yaml, arquitetura.md, modelo_dados.md, runbooks/
infra/          traefik, postgres (tuning + pg_hba), observabilidade
web/            frontend Next.js (mapa semafórico do IVM + drill-down) — profile `app`
worker/ orchestrator/   ingestão: worker + Dagster Degrau 1 (profile `ingestion`)
scripts/        runbooks executáveis (backup.sh, restore.sh — separação de PII)
docker-compose.yml  .env.example  .github/workflows/ci.yml
```

## Contribuir

- Cada PR deve mapear a uma seção da documentação; divergência exige um **ADR** em `docs/adr/`.
- TDD nas regras puras (supressão), BDD nos cenários de domínio; mais cobertura onde há mais risco
  (supressão e caminho ouro: 100%).
- Sem quebrar o passado: API aditiva, migração expand-and-contract.
- O quality gate (CI) precisa estar verde para merge.
