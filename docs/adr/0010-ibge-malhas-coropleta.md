# ADR-0010 — Malhas do IBGE e coropleta geográfica do IVM

- **Status:** aceito
- **Data:** 2026-06-05

## Contexto
O mapa do IVM era um painel de cartões (ADR-0009) por falta de geometrias. Para a **coropleta
geográfica** faltavam as **malhas do IBGE** em `territorio.geom` e um endpoint GeoJSON. IBGE é a
terceira fonte da Onda 1 (aberta, sem auth).

## Decisão
- **`AdaptadorIbge`** (fetcher injetável; testado com fixture): parse de **Localidades**
  (registro de municípios: código/nome/UF/hierarquia) e de **Malhas** (GeoJSON → `{código:
  geometria}`). Fetcher real HTTP (`servicodados.ibge.gov.br`); URLs a confirmar (próxima iteração).
- **Carga estrutural** (`app/ingestao/territorios.py`, fora do caminho ouro — é dimensão, não fato):
  `carregar_municipios` (upsert `territorio`, resolvendo `pai_id` pela UF) e `carregar_geometrias`
  (`UPDATE ... ST_Multi(ST_SetSRID(ST_GeomFromGeoJSON(...), 4674))`). Idempotente. CLI
  `python -m app.ingestao.run_ibge <UF>`.
- **Endpoint GeoJSON** `GET /v1/mapa/ivm?uf=&periodo=`: FeatureCollection com a geometria
  (`ST_AsGeoJSON` + `ST_SimplifyPreserveTopology` para payload menor) **left-join** com o IVM do
  período — município sem dado vem com `ivm: null`. Prefixo `/v1/mapa/...` para não colidir com
  `/v1/ivm/{codigo}`. Cacheado/invalidado junto do IVM.
- **Frontend `Coropleta`** (SVG): projeção equirretangular pura (`lib/geo.ts`, testada), área
  clicável (→ drill-down) onde há IVM, **cinza** onde não há. Seletor de UF no `/ivm` (SSR via query
  param); o painel de cartões permanece como visão tabular.

## Consequências / a evoluir
- O mapa é geográfico de verdade quando se roda `run_ibge <UF>`; sem isso, cai no painel de cartões.
- Próximos: carga nacional (todas as UFs) + cache de malha mais agressivo; projeção apropriada
  (ex.: cônica) e simplificação por nível de zoom; níveis acima de município (UF/região).
