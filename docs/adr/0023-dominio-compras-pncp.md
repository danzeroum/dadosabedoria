# ADR-0023 — Domínio `compras` via PNCP/Contratações Públicas (3ª fonte da Onda 2A)

- **Status:** aceito
- **Data:** 2026-06-06

## Contexto
Seguindo a sequência da Onda 2A por prontidão de fonte (**SICONFI → INEP → PNCP → DATASUS**,
ADR-0021/0022), o **PNCP** (Portal Nacional de Contratações Públicas, Lei 14.133/2021) é a 3ª fonte:
API de consulta aberta REST/JSON, **sem credencial**. Abre o domínio **`compras`** e a base para os
produtos **TRANSP-03 Fornecedor Transparente** (PNCP+Receita+DataJud) e **TRANSP-05 ObraViva**
(PNCP/SIOP/SIAFI+CAGED+OSM).

## Decisão
- **`AdaptadorPncp`** (medallion bronze→prata→ouro): parse do JSON de contratos (lista `data`) →
  Polars, com o município **aninhado** em `unidadeOrgao.codigoIbge` (**Struct** — 3º formato provado,
  após o JSON plano do SICONFI e o CSV do INEP); prata extrai o IBGE aninhado e normaliza
  `valorGlobal`; ouro soma o valor dos contratos por município. **Contrato na borda bronze**
  (`ContratoFonte`, ADR-0017): exige `valorGlobal` e `unidadeOrgao` — falha claro se o layout mudar.
  Fetcher real HTTP (aberto, `pragma: no cover`); parse/transform cobertos por fixture.
- **Indicador** `compras.contratos.valor_total` (contratos, **anual**, R$, polaridade neutra) +
  **fonte** `pncp` (atualização **diária** — PNCP é quase em tempo real) — semeados pelo **mesmo
  caminho ouro** (`escrever_ouro`: supressão + linhagem), nada de INSERT cru. A **API genérica** já
  serve (`/v1/indicadores?dominio=compras`, `/v1/valores?indicador=compras.contratos.valor_total`) —
  zero rota nova (Open/Closed).
- **`domains/compras`** (`ModuloCompras`): registra o adaptador + o catálogo do indicador.

## ASSUNÇÕES a confirmar (lacuna sinalizada)
A URL/params da consulta de contratos (`pncp.gov.br/api/consulta/v1/contratos`, paginação por
`dataInicial`/`dataFinal`/`pagina`) e a forma exata do item (`valorGlobal`, `unidadeOrgao.codigoIbge`)
são **assunções** — a confirmar contra a API real, como em ADR-0021/0022. O contrato de dados falha
claro se divergir.

## Consequências / a evoluir
- 3º domínio novo no ar (fatia vertical via seed→API), 3ª fonte externa pelo `ModuloDominio` — agora
  com **3 formatos** provados (JSON plano, CSV/latin-1, JSON aninhado/Struct), o que valida a
  abstração da medalhão para layouts heterogêneos. **Próximos:** pipeline **live** (`run_pncp` +
  Dagster); produtos **TRANSP-03/05** (telas e cruzamentos), com a **dupla face** do §17 (revisão
  humana antes de imputar conluio/irregularidade a fornecedor); paginação completa no fetcher.
- Sequência seguinte da Onda 2A (por prontidão): **DATASUS** (2B, ETL pesado) …
