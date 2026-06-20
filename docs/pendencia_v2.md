# Pendências do dono — v2 (gates e decisões da execução da auditoria unificada)

> O dev (autônomo) **não para** nestes: anota aqui e segue para a próxima tarefa. Revise quando puder.
> Complementa `docs/PENDENCIAS_DO_DONO.md` (gates históricos) e `docs/roadmap_v2.md` (execução).

## Decisões de produto (🟡 — direção, não execução)
- [ ] **D1 — Escopo internacional?** O Auditor B penalizou ausência de dados internacionais (World
  Bank/OWID) e i18n (ALTO-04/VIS-03). **Mas isso não aparece na proposta do repo** (missão = "dados
  públicos **brasileiros**"; o termo só existe em 2 mockups HTML offline em `docs/design/`).
  _Default do dev:_ tratar como **fora de escopo** — não implementar i18n nem fontes internacionais até
  o dono confirmar que entram no escopo. Se entrarem, viram Bloco novo no roadmap_v2.
- [ ] **D2 — Quebrar a doutrina zero-dep de UI?** Auditor B sugeriu Recharts/Tailwind (MEDIO-01/
  BAIXO-01). Conflita com a Invariante 6 (economia) e a escolha deliberada de zero-dep de UI.
  _Default do dev:_ **manter zero-dep**; enriquecer SVG/CSS nativos. Só adoto lib se o dono pedir.

## Decisões técnicas (🟡)
- [ ] **D3 — Modernizar o framework p/ zerar os ignores de CVE de starlette.** Hoje o teto
  `fastapi<0.137` (necessário: a 0.137 introduziu `_IncludedRouter`, que o
  `prometheus-fastapi-instrumentator` ≤8.0.0 não trata e quebra toda requisição) prende `starlette` em
  0.46.x, cujas CVEs (CVE-2025-54121, CVE-2025-62727, CVE-2026-48818/48817/54283/54282) só têm fix em
  0.47+/1.x. Estão **ignoradas no pip-audit** (risco baixo: API só-leitura atrás de rate-limit), mas o
  certo é **modernizar**: subir FastAPI/Starlette e (a) trocar/atualizar o instrumentator por um que
  trate `_IncludedRouter`, ou (b) prover um instrumentador de métricas próprio. _Default do dev:_ manter
  o pin + ignores documentados até alguém priorizar a modernização (não bloqueia a entrega de valor).

## Gates externos (🔴 — só o dono/infra destrava)
- [ ] **G1 — Sondagem de conectores (Bloco 2.1):** SNIS/ANEEL/ANA/PAM/SISVAN têm URL/colunas marcadas
  "a confirmar na 1ª busca real". Precisam de **rede aberta** (VPS/allowlist) para a 1ª busca real →
  promover fixture a fiel-à-forma + ADR (padrão #0). Aqui (github-only) é impossível. _Adiado._
- [ ] **G2 — Conectores bloqueados (Bloco 2.2):** CAGED/DATASUS (FTP porta 21), INEP (cert TLS do
  servidor), ESTBAN (BCB virou SPA — URL do ZIP sumiu), SINAN (FTP). Ações de infra/dono já listadas
  em `PENDENCIAS_DO_DONO.md §1`. ESTBAN: investigar `dadosabertos.bcb.gov.br` como alternativa.
- [ ] **G3 — IA com LLM real (Bloco 3.3 enriquecido):** narrativa proativa funciona em modo template;
  com `LLM_BASE_URL`/`LLM_MODEL`/`LLM_API_KEY` (ou Ollama) fica mais rica. Gate já em
  `PENDENCIAS_DO_DONO.md §1`.
- [ ] **G4 — Visão longa (Bloco 3.5):** datasets da comunidade, API pública/SDK, perfil de curiosidade
  persistido entre dispositivos (depende do OIDC do cidadão, já gate em PENDENCIAS §1).
- [ ] **G5 — Geolocalização precisa (Bloco 1.2):** mostrar "seu município" pela posição do navegador
  precisa de (a) um endpoint backend `/v1/territorios/proximo?lat&lon` (PostGIS, vizinho mais próximo)
  e (b) **geometria nacional do IBGE ingerida** (no contêiner só há SP/RJ semeados) → **data-gated**.
  O onboarding (3.4) já cobre a entrada por **busca** de município, que funciona sem isso. _Adiado p/
  quando a malha IBGE nacional estiver no ambiente de rede aberta (mesmo gate do mapa nacional)._
