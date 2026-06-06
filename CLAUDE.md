# CLAUDE.md — guia da sessão

**DadoSabedoria**: plataforma de inteligência de dados públicos brasileiros (Valor Triplo /
Open-Core Cívico). O ativo é a **confiança** — privacidade, proveniência e qualidade comprovada a
cada commit.

## O plano vive no repo
- **`docs/roadmap.md` é a fonte única do plano.** No início da sessão, leia-o e **execute o próximo
  item `[ ]` de cima para baixo**. Marque `[x]` ao mergear. Itens `[B]`/`[A]` não se re-perguntam;
  itens `🟡` têm *default proposto* — siga o default salvo se a decisão for irreversível/cara.

## Fluxo de trabalho (cada fatia)
1. Branch nova a partir de `origin/main` (o contêiner é efêmero e **reseta**; sempre
   `git fetch origin main` e ramifique de `origin/main`, não do checkout local).
2. Implementar **com teste** (TDD nas regras puras; integração contra Postgres real).
3. `git push -u origin <branch>` → abrir **PR** → acompanhar **CI** → **merge só com CI verde** →
   marcar `[x]` no roadmap → seguir para o próximo item.
4. Commits/PRs em PT-BR; trailer `https://claude.ai/code/...`; nunca o ID do modelo em artefatos.

## Invariantes inegociáveis (nunca afrouxar — ADR-0002)
1. Privacidade estrutural (grão território×período; sem chave de pessoa; supressão antes de gravar).
2. **Isolamento de PII**: dado pessoal só no schema `app`; a role analítica **não** o lê (teste que
   reprova o build). Só o serviço de consentimento (role_consentimento, rede isolada) acessa `app`.
3. IA ancorada (só afirma o recuperado, cita a fonte, abstém-se sem dado, não inventa número).
4. API aditiva (`/v1`) + migração expand-and-contract. 5. Proveniência sempre (fonte/método/lag).
6. Economia de recurso (pré-computar/cachear). 7. Quality gate verde p/ merge. 8. Segredo só em env.

## Quality gate (precisa passar p/ merge)
`ruff check . && ruff format --check . && mypy app && bandit -r app && shellcheck scripts/*.sh`;
`pytest` (cobertura global ≥85%, supressão+ouro =100%); contrato OpenAPI (`scripts/export_openapi.py`
sem diff); pip-audit; gitleaks; web (lint/typecheck/vitest/build); orquestração (Dagster).

## Dev local (contêiner novo)
- `sudo pg_ctlcluster 16 main start; redis-server --daemonize yes`; PostGIS via apt.
- DSNs (exporte) → `python -m app.migrate` (migra + semeia). Reinstale deps se o venv estiver velho:
  `cd api && uv pip install -e ".[dev]"`. Detalhe das DSNs/roles no `README.md` §Como testar.
- Se a role já existir com outra senha, `ALTER ROLE ... PASSWORD` (a migração 0009 não rotaciona).
