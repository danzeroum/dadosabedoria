# ADR-0020 — Chaves de API do tier profundo: emissão/revogação por cliente (no banco)

- **Status:** aceito
- **Data:** 2026-06-06

## Contexto
O tier profundo (ADR-0019) nasceu validando chaves contra `DEEP_API_KEYS` (hashes em env) — bom para
bootstrap, ruim para operar: não dá para emitir/revogar por cliente. Faltava o ciclo operacional.

## Decisão
- **Tabela `chave_api`** (migração 0014, schema `public`): credencial de **cliente** (B2G/B2B),
  **não PII** — por isso vive no acervo analítico, não no `app`. Guarda-se só o **SHA-256** (a chave
  bruta nunca é gravada); índice parcial nas ativas (`revogada_em IS NULL`).
- **Least-privilege:** a `api` (role_analitica) tem **só SELECT** na tabela (valida); `INSERT/UPDATE/
  DELETE` são **REVOKE** para ela — emissão/revogação são do **admin**. Assim, mesmo um
  comprometimento da api não cunha chaves.
- **Validação em duas fontes** (`api_key.py`): `chave_api` (por cliente, revogável — operacional)
  **ou** `DEEP_API_KEYS` (env, *break-glass*/bootstrap). A dependency devolve o `cliente` (ou
  `env:<8hex>`) para correlação/log, sem o segredo.
- **CLI admin** (`python -m app.profundo.run_chaves emitir "<cliente>" | revogar <id>`): gera a chave
  (`secrets.token_urlsafe`), grava o hash e **exibe a bruta uma vez** (não recuperável); revoga por id.

## Consequências / a evoluir
- O tier profundo passa a ser **operável por cliente** (emitir/revogar), com a chave bruta nunca em
  repouso e a api sem poder de emissão. Verificado: emissão→200, revogação→401, break-glass por env.
- Próximos: **cotas/billing** por cliente, expiração/rotação de chave, e uma UI/admin de gestão; a
  consulta em lote otimizada (1 query) e o rate-limit autenticado no gateway seguem no backlog (ADR-0019).
