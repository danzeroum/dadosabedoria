# CLAUDE.md — guia da sessão

**DadoSabedoria**: plataforma de inteligência de dados públicos brasileiros (Valor Triplo /
Open-Core Cívico). O ativo é a **confiança** — privacidade, proveniência e qualidade comprovada a
cada commit.

## ⚠️ SESSÃO NOVA — PRIMEIRA tarefa (antes de pegar o próximo item do roadmap): validar o #0 do OndeFoi
O dono **liberou o egress** do SICONFI (`apidatalake.tesouro.gov.br` + IBGE/BCB, modo **Custom**). Pela
plataforma isso **só vale em sessão NOVA** (não em *resume* — resume herda a política antiga e dá falso
negativo). Como a sessão nova começa **sem o contexto da conversa anterior**, este bilhete é o que a
manda **furar a fila**: antes da próxima fatia do roadmap, **valide o OndeFoi contra a fonte real**.
1. **Sonda do #0** (só confiável em sessão nova):
   ```bash
   curl -sS -D - -o /dev/null --max-time 15 https://apidatalake.tesouro.gov.br/ \
     | grep -iE "^HTTP/|x-deny-reason"
   ```
   `x-deny-reason: host_not_allowed` → **bloqueado** (passo 4). Linha `HTTP/...` **sem** `x-deny-reason`
   → **aberto** (passo 2).
2. **Se aberto — a validação real (payoff de várias rodadas), UMA vez:** rode `run_siconfi`/fetcher real
   contra o DCA ao vivo e confirme as **três incógnitas de forma** marcadas no ADR-0026: (a) **nomes de
   campo** reais (vs. os do mock); (b) **classificação de função** = os *membros* da dimensão — promova
   o vocabulário **da fonte**, nunca do mock; (c) como o SICONFI sinaliza função **ausente vs. retida** →
   confirme a hipótese **válido = `{valor, sem_cobertura}`, sem `suprimido`**. Promova a fixture de
   **fiel-ao-contrato → fiel-à-forma** (capture um fixture real). Des-arrisca todas as esteiras de uma vez.
3. **Feche o loop NO PAPEL:** grave a **forma confirmada no ADR-0026** (ou ADR-filho) — as marcas
   "confirmar no #0" viram "confirmado: X". Senão a validação vira evento perdido no próximo reset.
4. **Se bloqueado mesmo em sessão nova:** a config não pegou — peça ao dono conferir no editor do
   ambiente (claude.ai/code): Network = **Custom** (não só "Trusted"), **"include default list of common
   package managers"** marcada, e **salvo**. Contorno só pra validar: Network = **Full**, voltando ao Custom.

**Estado do OndeFoi (TRANSP-06):** contrato travado (ADR-0026 + refino); **fatia 1** mergeada (denominador
em código: `app/produtos/onde_foi.py` + 6 testes). Fatias seguintes seguem **grau-demo honesto mesmo sem
o #0**: `v_saude_estado` do IVM (mesmo padrão `*_estado`) → esqueleto de `/v1/onde-foi/{ibge}` → esteira
de despesa por função (dimensão mínima/promovível) → **(b)** tela sobre os primitivos do handoff, com axe no DOM.

## O plano vive no repo
- **`docs/roadmap.md` é a fonte única do plano.** No início da sessão, leia-o e **execute o próximo
  item `[ ]` de cima para baixo**. Marque `[x]` ao mergear.
- **Política de autonomia (pré-autorizada pelo dono — ver `docs/roadmap.md`):** os `🟡` "seguros"
  (#1,#2,#5,#6,#7,#8) estão **pré-autorizados** — siga o *default*, não pare. Só os **🔴 gates
  externos** param (LLM key, OIDC, domínio/TLS, credenciais de fonte restrita, conselho PbD) e, mesmo
  esses, com **adiar-e-seguir**: adia só o item, constrói o resto, e anota na **Lista de desbloqueio**
  do roadmap. **Nunca fique ocioso** num gate.
- **Lente atual (PIVÔ 2026-06-06): puxar PRODUTO até a TELA, por valor (#5).** O backbone já basta
  (financas/educacao/compras/saude no ar pelo `ModuloDominio`). **Não adicionar fonte nova agora** —
  cada fatia vai do dado à **tela**, com dupla-face §17. Marco: **IVM completo → mapa semafórico →
  produtos por valor** (OndeFoi/EDU-01/saúde/PNCP). Fonte nova só quando um produto priorizado exigir.
- **Doutrina dado-vivo (refino 2026-06-06):** todo produto nomeado vai à tela com **dado VIVO**
  (pipeline `run_*` + schedule Dagster), **não seed** — começando pela fonte **gate-free**. Seed é só
  demo/fixture, sempre rotulado. **Realidade de rede do contêiner: github-only** — IBGE/BCB/SICONFI
  respondem 403 ("Host not in allowlist"), então **nenhuma fonte busca dado real aqui**; "vivo" =
  esteira completa (adapter→bronze→prata→ouro) + schedule + fixture fiel + fetcher real, exercida no CI
  por fetcher *fake* (mesmo nível de CAGED/ESTBAN); o dado real flui no ambiente com rede aberta.
  Desbloqueio (🔴 do dono do ambiente): liberar no allowlist `apidatalake.tesouro.gov.br` (SICONFI),
  `servicodados.ibge.gov.br` (IBGE), `www4.bcb.gov.br` (CAGED/ESTBAN) → rodar `python -m app.ingestao.run_<fonte>`.

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
