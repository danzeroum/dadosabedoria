# web — frontend (Next.js)

Mapa semafórico do **IVM** + drill-down de município, consumindo a API pública `/v1/ivm`
(SSR, sem CORS). Stack: Next.js 14 (App Router) + React + TypeScript. Design system v1 e limitações
em **ADR-0009**.

## Telas
- `/ivm` — painel semafórico (cartões por município, do mais ao menos vulnerável; padrão = período
  mais recente).
- `/ivm/[codigo]` — drill-down: subíndices (emprego/finanças) + série temporal do IVM.

## Rodar
```bash
npm install
API_URL=http://localhost:8000 npm run dev      # aponta para a API local
# ou na stack: docker compose --profile app up  # web roteado pelo Traefik
```

## Qualidade (mesmo do CI, job `web`)
```bash
npm run lint && npm run typecheck && npm run test && npm run build
```

## Componentes (design system v1)
`Semaforo`, `MapaSemaforico`, `Comparador`, `SerieTemporal`. A regra do semáforo espelha o backend
(ADR-0008) em `lib/semaforo.ts` (testada). Acessibilidade: estado nunca só por cor, foco visível,
HTML semântico.

> A coropleta geográfica chega com as malhas do IBGE (próxima fatia). O "mapa" v1 é um painel de
> cartões.
