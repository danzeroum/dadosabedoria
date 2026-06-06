# ADR-0022 — Domínio `educacao` via INEP/Censo Escolar (2ª fonte da Onda 2A)

- **Status:** aceito
- **Data:** 2026-06-06

## Contexto
Seguindo a sequência da Onda 2A por prontidão de fonte (**SICONFI → INEP → PNCP → DATASUS**,
ADR-0021), o **INEP/Censo Escolar** é a 2ª fonte: dado aberto, **sem credencial** (microdados anuais
em CSV). Abre o domínio **`educacao`** e a base para os produtos **EDU-01 Bússola Educação-Trabalho**
(INEP+CAGED+IBGE) e **EDU-02 Radar de Evasão**.

## Decisão
- **`AdaptadorInep`** (medallion bronze→prata→ouro): parse do CSV ``;``-delimitado dos microdados
  (nível escola) → Polars (tudo texto; `utf8-lossy` tolera o latin-1 da fonte, como CAGED/ESTBAN);
  prata normaliza `CO_MUNICIPIO` e `QT_MAT_FUND`; ouro soma as matrículas do fundamental por
  município. **Contrato na borda bronze** (`ContratoFonte`, ADR-0017): exige `CO_MUNICIPIO` e
  `QT_MAT_FUND` — falha claro se o layout mudar. Fetcher real HTTP/ZIP (aberto, `pragma: no cover`);
  parse/transform cobertos por fixture.
- **Indicador** `educacao.matriculas.fundamental` (Censo Escolar, **anual**, contagem, polaridade
  neutra) + **fonte** `inep` — semeados pelo **mesmo caminho ouro** (`escrever_ouro`: supressão +
  linhagem), nada de INSERT cru. A **API genérica** já serve (`/v1/indicadores?dominio=educacao`,
  `/v1/valores?indicador=educacao.matriculas.fundamental`) — zero rota nova (Open/Closed).
- **`domains/educacao`** (`ModuloEducacao`): registra o adaptador + o catálogo do indicador.

## ASSUNÇÕES a confirmar (lacuna sinalizada)
A URL/nome do ZIP dos microdados (`download.inep.gov.br/.../microdados_censo_escolar_<ano>.zip`), o
nome do CSV de escolas dentro do pacote e o nome exato da coluna de matrículas (`QT_MAT_FUND`) são
**assunções** — a confirmar contra o pacote real do INEP, como em ADR-0007/0010/0021. O contrato de
dados falha claro se divergir.

## Consequências / a evoluir
- 2º domínio novo no ar (fatia vertical via seed→API), 2ª fonte externa pelo `ModuloDominio` — agora
  com **2 formatos** provados (JSON no SICONFI, CSV/latin-1 aqui), reforçando a abstração da medalhão.
  **Próximos:** wiring do pipeline **live** (`run_inep` + Dagster); produtos **EDU-01/EDU-02** (telas
  e cruzamentos com CAGED/IBGE); **subíndice de educação no IVM completo** (z-score v2, ADR-0018).
- Sequência seguinte da Onda 2A (por prontidão): **PNCP → DATASUS …**.
