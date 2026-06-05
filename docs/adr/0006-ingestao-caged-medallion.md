# ADR-0006 — Ingestão CAGED (adaptador + medallion) e orquestração Degrau 1

- **Status:** aceito
- **Data:** 2026-06-05

## Contexto
Primeira fonte real da Onda 1: Novo CAGED (MTE/PDET) — menor atrito (aberto, sem auth), sinal
precoce de emprego. Precisa virar o indicador `trabalho.emprego.saldo_caged` **sem** abrir exceção
aos invariantes nem ao caminho de escrita da fundação.

## Decisão
- **Contrato `AdaptadorFonte`** (§6): `extrair(janela) -> DataFrame` (Polars) para a bronze. O
  `AdaptadorCaged` isola o formato CAGEDMOV; o **fetcher é injetável** (`FetcherFonte`) → o
  parse/transformação são testados com fixture, **sem rede**. O fetcher real (`FetcherCagedFTP`)
  baixa o `.7z` do FTP do PDET (canal oficial público; FTP suprimido no SAST com justificativa).
- **Medallion:** bronze (bruto + sha256 em object storage S3/MinIO; em memória nos testes) →
  prata (normaliza/filtra, Polars) → ouro (soma `saldomovimentação` por município).
- **Carga pela MESMA regra única:** o `pipeline.executar_caged` chama `escrever_ouro` (supressão +
  `linhagem` com URL de origem e hash do bruto). Idempotente (upsert). Nada de caminho paralelo.
- **Crosswalk** município: CAGED usa IBGE de 6 dígitos (o de 7 sem o verificador) → casamos por
  `codigo_ibge[:6]`. Município fora do cadastro é ignorado (contado no log).
- **Plugin `trabalho`:** primeiro `ModuloDominio` concreto — registra o adaptador e o catálogo do
  indicador, provando o encaixe (§6) sem alterar o núcleo.
- **Dagster Degrau 1:** `app/orquestracao/definitions.py` — job + `schedule` mensal (cron) que
  dispara a esteira com retry e logs. Dagster é **dependência opcional** (extra `orquestracao`); só
  o contêiner `orchestrator` o instala (build arg `INSTALL_EXTRAS`), mantendo api/worker enxutos.

## Consequências
- O endpoint de leitura passa a servir dados reais de CAGED pela API existente (sem rota nova).
- Cobertura: parse/prata/agregação, crosswalk e pipeline testados (fixture + Postgres real);
  Dagster validado em job de CI dedicado. Supressão/ouro seguem em 100%.
- Pendências conhecidas: persistência do `DAGSTER_HOME` (Degrau 2); validação de competência do
  arquivo vs. janela; backfill em lote; contrato de dados formal por fonte.
