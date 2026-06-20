# Roadmap v2 — execução do plano de auditoria unificada (minha análise × Auditor B)

> Tracker vivo da execução autônoma aprovada pelo dono (2026-06-20). Atualizado a cada fatia.
> Fonte do plano: auditoria cruzada (ver também `docs/pendencia_v2.md` para gates do dono).
> Legenda: `[x]` feito · `[~]` em andamento · `[ ]` pendente · 🟢 construível aqui · 🔴 travado (VPS/dono).

## Bloco 0 — Integridade de documentação 🟢
- [x] 0.1 Reconciliar deriva `CLAUDE.md`×roadmap sobre OndeFoi (referendado ADR-0029/0034/0035, selo
  removido PR-94; mantém `demo=true` local explícito).
- [x] 0.2 Glossário "vivo vs. ao vivo" na §Doutrina dado-vivo do `CLAUDE.md`.
- [x] 0.3 Nota VPS-≠-repo em `PENDENCIAS_DO_DONO.md`.
- [x] 0.4 Criar trackers `docs/roadmap_v2.md` + `docs/pendencia_v2.md`.

## Bloco 0.5 — Destravar a CI (gap novo achado na execução) 🟢
> A CI de `main` estava **vermelha** (pré-existente): deps sem teto driftaram. `fastapi 0.138` introduziu
> `_IncludedRouter` em `app.routes` → `prometheus-fastapi-instrumentator` (`_get_route_name` faz
> `route.path`) quebra **toda requisição** → 133 testes de integração falhando; e `build_scan`/pip-audit
> falhando por CVEs novas. Sem isto, nada merge. Reproduzido e corrigido localmente (venv py3.12 + PG).
- [x] 0.5.1 Pin `fastapi>=0.115,<0.137` (último sem `_IncludedRouter`; bug ainda em instrumentator 8.0.0).
- [x] 0.5.2 Bump `cryptography>=48.0.1` (GHSA-537c-gmf6-5ccf) e `py7zr>=1.1.3` (CVE-2026-23879/55206/55195).
- [x] 0.5.3 pip-audit do CI ignora as CVEs de starlette inalcançáveis sob `fastapi<0.137` (doc + D3 na
  pendencia_v2). Verificado local: 811 testes ✓, cobertura 89%/100%, OpenAPI sem diff, ruff/mypy/bandit ✓.
- [x] 0.5.4 gitleaks: pina a imagem oficial `ghcr.io/gitleaks/gitleaks:v8.21.2` (a `zricethezav:latest`
  era tag flutuante da org descontinuada, com falsos-positivos) + allowlist do trailer claude.ai/code.
  Verificado local (8.21.2): árvore inteira e commits sem leaks.

## Bloco 1 — Quick wins de frontend 🟢 (sem dep nova) — PR #159
- [x] 1.1 De-hardcodar UFs do mapa IVM (`ivm/page.tsx`): 27 UFs + `.ufs` com `flex-wrap`; degradação
  honesta "Sem mapa para {uf}" onde falta malha (cobertura nacional plena segue 🔴 data-gated no IBGE).
- [~] 1.2 Geolocalização: a versão precisa (lat/lon→município) precisa de endpoint backend
  `/v1/territorios/proximo` (PostGIS) e geometria nacional (data-gated) → **adiada p/ a fatia de backend**
  (Bloco 3.2/3.3). O onboarding (3.4) já cobre a entrada por busca de município.
- [x] 1.3 Tier tablet de responsividade (`globals.css`: `@media ≤1024px` empilha `.enquadra`/coropleta;
  `≤680px` ajusta os novos blocos).
- [ ] 1.4 Badge "mudança significativa" (z-score) — **revisar necessidade**: o Pulso já mostra
  `tendencia` (melhorando/estável/piorando, ADR-0027) e a série inteira; um z-score sobre saldo (volátil
  por natureza) arriscaria **alarme falso** (contra a honestidade). Só vale como sinal **transversal**
  em indicadores estáveis (per-capita) — desenho cuidadoso, não trivial. _Adiado com ressalva._

## Bloco 2 — Validação de conectores 🔴 (rede aberta/VPS) → ver pendencia_v2
- [ ] 2.1 Sondar 5 não-validadas (SNIS/ANEEL/ANA/PAM/SISVAN) → forma → fixture fiel + ADR.
- [ ] 2.2 Destravar 5 bloqueadas (CAGED/DATASUS FTP-21; INEP TLS; ESTBAN SPA; SINAN FTP).

## Bloco 3 — Curiosidade/descoberta (maior lacuna de produto)
- [x] 3.1 🟢 "Dados Relacionados" (domínio+território) — recomendação não-linear (PR #159): helper
  `lib/relacionados.ts` (reusa o catálogo) + `<ProdutosRelacionados>` + teste; troca os links fixos de
  pulso/onde-foi pelo componente catálogo-driven. _Rollout completo (26 páginas de produto
  municipal, total 28): PR #163 — pulado em indicador/ivm/municipio/perfil-orcamentario (não-municipais)._
- [x] 3.2 🟢 "Você Sabia?" — módulo backend ancorado/honesto (PR #160): `curiosidades.py` (regras puras,
  Invariante 3 — só valor recuperado, cita fonte, zero causalidade; sem dado → vazio) + endpoint
  `GET /v1/territorios/{ibge}/curiosidades` + `<VoceSabia>` no panorama. Regra-âncora: gap água–esgoto
  (mesma fonte SNIS). Seed: Campinas água 88%/esgoto 35% → o demo mostra o card. 9 testes; OpenAPI +78.
- [~] 3.3 Narrativa proativa da IA no município — **largamente coberto** por 3.2 (`<VoceSabia>`,
  fatos ancorados) + o panorama (todos os indicadores com fonte). Uma narrativa em prosa proativa
  agregaria pouco sobre isso e, feita à mão, é delicada (Invariante 3); com LLM real vira síntese
  natural (🔴 chave do dono, ver pendencia_v2 G3). _Adiado: marginal sem LLM._
- [x] 3.4 🟢 Onboarding do 1º acesso (PR #159): `<Onboarding>` na home — busca de município
  (código IBGE→panorama; nome→busca IVM), `localStorage` anônimo, dispensável. (Reduzi de "3 passos"
  para 1 passo focado — sem persistência de preferências entre páginas, evita overreach.)
- [ ] 3.5 🔴/decisão Visão longa (perfil-curiosidade, trilhas, datasets comunidade, API/SDK).

## Bloco 4 — Saúde de código 🟢
> Dívida real (Auditor B MEDIO-02), **não delicada** mas de refactor amplo — cada item merece a
> própria fatia cuidadosa (não um big-bang no fim de uma maratona).
- [ ] 4.1 Gerar tipos do front do OpenAPI (`openapi-typescript`) → mata o drift de `types.ts` (890
  linhas manuais). _Cuidado: gerar + adotar incrementalmente (gerar sem usar = peso morto). Ainda aberto:
  o valor está na ADOÇÃO (arriscada), não no scaffolding — merece fatia dedicada._
- [ ] 4.2 Quebrar `facade.py` (1992 linhas) em módulos por produto. _Refactor amplo; um produto por vez.
  Ainda aberto: 28 classes independentes e bem seccionadas (split mecânico mas ~2000 linhas movidas +
  refiação de imports em `rotas.py`) — fatia dedicada, não fim-de-maratona._
- [x] 4.3 Helper de fetch genérico p/ `api.ts` (PR #162): 3 helpers (`pedir`/`pedirOuNull`/
  `pedirSilencioso`), as 49 funções viram 1-linhas; **modo de cache (no-store×revalidate) e modo de erro
  preservados, verificado por diff path→modo** (zero flips). _De quebra, corrige um homoglyph cirílico._

## Novos gaps achados durante a execução
- **CI vermelha em `main` por drift de dependência** (resolvido no Bloco 0.5): `fastapi` sem teto subiu
  p/ 0.138 e quebrou o instrumentator (`_IncludedRouter`); CVEs novas no pip-audit. Lição: as deps de
  runtime precisam de teto/lock — ver D3 (pendencia_v2) p/ modernização do framework.
- **Homoglyph cirílico `SentinelaMatern[а]`** (resolvido no PR #162): o identificador da camada API/web
  usava `а` cirílico (U+0430), enquanto a classe de domínio `SentinelaMaterna` é latina — dois nomes
  visualmente idênticos, porém distintos (footgun; alguém digitando o latino teria `undefined`). Corrigido
  em 6 arquivos (Python+TS) com alvo preciso `perl \x{0430}`; o contrato OpenAPI regenerado de quebra
  limpou um nome de schema mangled (`SentinelaMatern_Out` → `SentinelaMaternaOut`).

## Log de PRs
- **PR #158** (`claude/wizardly-cray-aj9fpw`): Bloco 0 (docs) + Bloco 0.5 (destrava CI). **MERGEADO** ✓.
- **PR #159** (`claude/auditoria-v2-frontend`): Bloco 1.1+1.3 + 3.1 + 3.4 (mapa nacional, tier tablet,
  Dados Relacionados, onboarding). **MERGEADO** ✓.
- **PR #160** (`claude/auditoria-v2-curiosidades`): Bloco 3.2 "Você Sabia?" (backend ancorado + endpoint
  + card + seed demo). **MERGEADO** ✓.
- **PR #161** (`claude/auditoria-v2-trackers`): disposição final dos itens restantes (1.4/3.3 adiados com
  ressalva; 4.x recomendado como próxima frente; gates anotados). **MERGEADO** ✓.
- **PR #162** (`claude/auditoria-v2-saude-codigo`): Bloco 4.3 (helper de fetch no `api.ts`) + correção do
  homoglyph cirílico (Python+TS) + regen do contrato OpenAPI. **MERGEADO** ✓.
- **PR #163** (`claude/auditoria-v2-descoberta-rollout`): rollout do `<ProdutosRelacionados>` a 26 páginas
  de produto municipal (completa o follow-up do 3.1). **MERGEADO** ✓.
- **PR #165** (`claude/auditoria-v2-hardening`): hardening pós-revisão — helper `_liquidado_ou_zero`
  (SICONFI) + teste de regressão, `api.test.ts` (helpers de fetch), comentário do `pedirSilencioso`.
- **PR (docs)** (`claude/auditoria-v2-revisao-final`): roadmap reflete #162/#163/#165 + veredito da revisão
  final independente.

## Resumo da execução (2026-06-20)
**Mergeado, CI verde (6 PRs, #158–#163):** Bloco 0 (docs), **0.5 (resgate da CI vermelha — gap
pré-existente)**, 1.1, 1.3, 3.1 **+ rollout completo (28 telas)**, 3.2, 3.4, **4.3 (helper de fetch) +
homoglyph cirílico**. **Adiado com ressalva (redundante/delicado):** 1.4, 3.3. **Gated (dono/VPS, em
`pendencia_v2`):** 1.2, 2.1, 2.2, 3.5, D1, D2, D3, G3. **Recomendado próxima frente (fatia dedicada):**
4.1 (tipos do OpenAPI — adoção) e 4.2 (split do `facade.py`) — refactors amplos que **não** devem ser
big-bang de fim-de-maratona. A camada de **descoberta** (a maior lacuna do Auditor B) está completa: mapa
nacional, Dados Relacionados (em todas as 28 telas de produto), onboarding e "Você Sabia?" — honesty-first
e CI-verde.

### Revisão final (2026-06-20)
- **`api.ts` (PR #162) verificado por construção:** diff `path→modo` confirma **zero flips** de cache
  (no-store×revalidate) e de modo de erro (404→null × silencioso × lança) nas 49 funções.
- **`main` verde** após os merges #162/#163 (CI por merge-ref).
- **Revisão independente (subagente, leitura-única): SEM bloqueio.** Veredito: a auditoria pode ser
  chamada de **concluída** — nenhum item CRIT/HIGH. Confirmados sãos: **Inv. 1** (supressão/k-anon antes
  de gravar, fail-closed; `test_supressao.py` + BDD), **Inv. 2** (isolamento de PII com **teste que
  reprova o build**, `tests/integration/test_pii_isolation.py`: a role analítica leva
  `InsufficientPrivilegeError` ao tocar `app.*`), **Inv. 3** (curiosidades só justapõem valor recuperado,
  citam `fonte_nome`, filtram suprimidos, `[]` sem fato), **doutrina de honestidade** (`demo` rotulado +
  proveniência nas 28 telas; mapa IVM degrada "Sem mapa para {uf}" sem falsa cobertura nacional),
  contrato OpenAPI e a refatoração do `api.ts`. Trackers conferem com a realidade.
- **3 follow-ups não-bloqueantes → endereçados no PR #165 (hardening):** [MED] proteger o `NULL SUM()→0.0`
  do SICONFI (helper `_liquidado_ou_zero` documentado + teste de regressão nos 11 produtos); [LOW] helpers
  de `api.ts` sem teste unitário (`api.test.ts` novo, 6 testes — modos de erro e de cache); [LOW] comentar
  que `pedirSilencioso` não recebe `rotulo` (2ª posição é o `ModoCache`).
