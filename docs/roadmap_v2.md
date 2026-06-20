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

## Bloco 1 — Quick wins de frontend 🟢 (sem dep nova)
- [ ] 1.1 De-hardcodar UFs do mapa IVM (`web/app/ivm/page.tsx`): lista de UFs dinâmica + degradação
  honesta p/ UFs sem malha. (Cobertura nacional plena é 🔴 data-gated na ingestão IBGE.)
- [ ] 1.2 Geolocalização + herói "seu município" na home (`web/app/page.tsx`), com permissão e fallback.
- [ ] 1.3 Tier tablet de responsividade (`globals.css`: breakpoints 768/1024; coropleta+tabelas).
- [ ] 1.4 Badge "mudança significativa" (z-score vs. 12 meses), rotulado e ancorado.

## Bloco 2 — Validação de conectores 🔴 (rede aberta/VPS) → ver pendencia_v2
- [ ] 2.1 Sondar 5 não-validadas (SNIS/ANEEL/ANA/PAM/SISVAN) → forma → fixture fiel + ADR.
- [ ] 2.2 Destravar 5 bloqueadas (CAGED/DATASUS FTP-21; INEP TLS; ESTBAN SPA; SINAN FTP).

## Bloco 3 — Curiosidade/descoberta (maior lacuna de produto)
- [ ] 3.1 🟢 "Dados Relacionados" (domínio+território) — recomendação não-linear.
- [ ] 3.2 🟢 "Você Sabia?" — módulo backend de células contraintuitivas, ancorado/honesto.
- [ ] 3.3 🟢 Narrativa proativa da IA no abrir do município (estende NarradorTemplate).
- [ ] 3.4 🟢 Onboarding 3 passos (município→domínios→panorama), localStorage, anônimo.
- [ ] 3.5 🔴/decisão Visão longa (perfil-curiosidade, trilhas, datasets comunidade, API/SDK).

## Bloco 4 — Saúde de código 🟢
- [ ] 4.1 Gerar tipos do front do OpenAPI (`openapi-typescript`) → mata drift de `types.ts`.
- [ ] 4.2 Quebrar `facade.py` (1992 linhas) em módulos por produto.
- [ ] 4.3 Helper de fetch genérico p/ `api.ts`.

## Novos gaps achados durante a execução
- **CI vermelha em `main` por drift de dependência** (resolvido no Bloco 0.5): `fastapi` sem teto subiu
  p/ 0.138 e quebrou o instrumentator (`_IncludedRouter`); CVEs novas no pip-audit. Lição: as deps de
  runtime precisam de teto/lock — ver D3 (pendencia_v2) p/ modernização do framework.

## Log de PRs
- **PR #158** (branch `claude/wizardly-cray-aj9fpw`): Bloco 0 (docs) + Bloco 0.5 (destrava CI). Em CI.
