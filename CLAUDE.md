# CLAUDE.md — guia da sessão

**DadoSabedoria**: plataforma de inteligência de dados públicos brasileiros (Valor Triplo /
Open-Core Cívico). O ativo é a **confiança** — privacidade, proveniência e qualidade comprovada a
cada commit.

## ⚠️ SESSÃO NOVA — PRIMEIRA tarefa: re-sondar o #0 e validar os conectores ABERTOS
**SICONFI #0 = VALIDADO** (2026-06-07, sessão nova → **ADR-0028**): a DCA real foi exercida, as 3
incógnitas de forma confirmadas (campos reais; vocabulário de função = Portaria 42 da fonte;
`exe_estado` válido = `{valor, sem_cobertura}`) e a fixture promovida a **fiel-à-forma**. O egress
(modo **Custom**) **só vale em sessão NOVA** (resume herda a política antiga e dá falso negativo) — por
isso o #0 vive aqui. Última sonda (**2026-07-04**): **nenhum host devolve `x-deny-reason`** —
SICONFI/IBGE/BCB/PNCP ✅ abertos (SICONFI respondeu dado real ao vivo); INEP ⚠️ allowlist ok mas
**TLS reset no servidor do INEP**; DATASUS/CAGED ⚠️ allowlist HTTPS ok mas **porta 21 (FTP) segue
bloqueada** — caminho é a VPS (detalhe: `docs/analise-pareto-2026-07.md` §1). Antes da próxima fatia,
**fure a fila** pelo #0 que ainda rende:
1. **Sonda** (só confiável em sessão nova) — SICONFI + os ainda-bloqueados:
   ```bash
   for h in apidatalake.tesouro.gov.br download.inep.gov.br pncp.gov.br ftp.datasus.gov.br; do
     echo "== $h =="; curl -sS -D - -o /dev/null --max-time 15 "https://$h/" | grep -iE "^HTTP/|x-deny-reason"
   done
   ```
   `HTTP/...` **sem** `x-deny-reason` → aberto; `x-deny-reason: host_not_allowed` → bloqueado.
2. **Conectores abertos ainda NÃO exercidos (IBGE/CAGED/ESTBAN):** rode o fetcher real UMA vez,
   confirme a forma (campos/colunas) vs. a fixture, **feche o loop no papel** (ADR) e promova a fixture
   a fiel-à-forma — mesmo padrão do SICONFI/ADR-0028. **Não refazer SICONFI** (já validado).
3. **Quando INEP/PNCP/DATASUS abrirem:** idem — 1ª busca real, confirme a forma (a marca "confirmar na
   1ª busca real" de cada), grave no ADR, promova a fixture. _Senão a validação vira evento perdido no
   próximo reset._
4. **Se ainda 403 em sessão nova:** a config não pegou — peça ao dono no editor do ambiente
   (claude.ai/code): Network = **Custom** (não só "Trusted"), **"include default list of common package
   managers"** marcada, e **salvo**. Contorno só pra validar: Network = **Full**, voltando ao Custom.

**Estado dos produtos à TELA (maratona 2026-06-07):** o backbone foi puxado até a tela por valor —
**Pulso Produtivo (TRAB-01)**: `/v1/pulso-produtivo/{ibge}` + tela `/pulso/{ibge}` sobre o saldo CAGED
real (ADR-0027); **OndeFoi (TRANSP-06)**: contrato (ADR-0026) + `/v1/onde-foi/{ibge}` + tela
`/onde-foi/{ibge}` **referendado** (ADR-0029; selo "demonstração" removido no PR-94 — render local
em `demo=true` enquanto o seed < 50 mun; DS atual); **Panorama do município**: `/v1/territorios/{ibge}/panorama` + tela `/municipio/{ibge}`
(todos os indicadores, supressão honesta); **porta de entrada** em `/`. **OndeFoi pós-#0:** a forma está
presa (ADR-0028) e a **re-ancoragem foi referendada** — Liquidado÷Empenhado por função (ADR-0029),
escala corrigida (ADR-0034), banda calibrada com ~5.541 municípios (ADR-0035), selo removido (PR-94);
a esteira viva (Anexo I-E → função como dimensão → `run_siconfi_funcoes`/Dagster) está
**pronta-para-vivo**. Como todo produto, o render local/CI segue `demo=true` até a ingestão nacional do
SICONFI no ambiente de rede aberta (VPS). Os demais produtos seguem por valor (roadmap), telas na **DS atual** (ADR-0009,
acessível) até o handoff voltar.

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
  - **Glossário "vivo" vs. "ao vivo" (evita super-conclusão):** quando o repo/ADR diz que um conector
    está **"vivo"/"ao vivo"/"validado"**, isso significa **esteira pronta-para-vivo** (adapter→ouro +
    schedule + fixture fiel + fetcher real, exercida em CI por fake) e/ou uma **busca real única em VPS
    de rede aberta** registrada em ADR. **Não** significa dado nacional servindo aqui: neste
    contêiner/CI **tudo é `demo=true` rotulado** (seed < 50 mun; `GET /v1/cobertura/<fonte>`). O dado
    real só flui no ambiente de rede aberta e **não é reproduzível a partir deste checkout**.

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
