# ADR-0009 — Frontend do IVM (Next.js) e proposta de design system v1

- **Status:** aceito (design system **v1** — especificação proposta para uma lacuna conhecida do
  briefing; sinalizada ao responsável)
- **Data:** 2026-06-05

## Contexto
Fecha a Onda 1 na tela: o **mapa semafórico do IVM** + **drill-down** de município (briefing §15.5),
consumindo `/v1/ivm`. O briefing lista o **design system** (tokens, componentes, acessibilidade) e o
**fluxo de autenticação do cidadão** como lacunas — proponho uma especificação concreta e sinalizo.

## Decisão
- **Stack:** Next.js 14 (App Router) + React 18 + TypeScript estrito; **SSR** (server components
  buscam a API pela rede interna → sem CORS, sem segredo no cliente). Build `standalone` (imagem
  enxuta). Sem biblioteca de gráficos: **SVG inline** (menos dependência/superfície).
- **Design system v1 (proposta):** tokens em `app/globals.css` (cores, raio, sombra, tipografia de
  sistema); componentes `Semaforo`, `MapaSemaforico`, `Comparador`, `SerieTemporal`. **Acessibilidade:**
  o estado nunca é comunicado **só por cor** (texto + `aria-label`/`title`), foco visível, HTML
  semântico, `lang="pt-BR"`. A regra do semáforo espelha o backend (ADR-0008), num único lugar
  (`lib/semaforo.ts`), testada (vitest).
- **Telas:** `/ivm` (painel semafórico, padrão = período mais recente) e `/ivm/[codigo]`
  (drill-down: subíndices + série). Páginas `dynamic` (não pré-renderizam no build → sem dependência
  da API em build-time).
- **CI:** job `web` (lint + typecheck + vitest + build). Compose: serviço `web` no profile `app`,
  roteado pelo Traefik (api tem prioridade nas rotas `/v1` e `/health`).

## Limitações conhecidas / próximos passos (sinalizados)
- **Coropleta geográfica:** o "mapa" v1 é um **painel de cartões por município** (não polígonos).
  A coropleta exige as **malhas do IBGE** (geometrias em `territorio.geom`, hoje vazias) e um
  endpoint GeoJSON — é a próxima fatia natural (fonte IBGE da Onda 1).
- **Autenticação do cidadão** (OIDC → JWT em cookie HttpOnly) e **interatividade client-side**
  (filtros, busca) ficam para a próxima iteração; v1 é leitura pública/SSR.
- **`npm audit`:** dev-tooling (esbuild/glob/postcss via vitest) e um *advisory* do `next` com faixa
  ampla sem versão estável fora dela (triado, como o caso da starlette no backend). Mantemos o
  **último patch estável 14.2.x**; `npm audit` é revisão manual periódica, **não** gate de CI (que
  é lint + typecheck + teste + build).
