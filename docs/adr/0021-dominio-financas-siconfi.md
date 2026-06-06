# ADR-0021 — Domínio `financas` via SICONFI/STN (1ª fonte da Onda 2A)

- **Status:** aceito
- **Data:** 2026-06-06

## Contexto
Onda 2A abre os domínios novos **por prontidão de fonte**. O **SICONFI/STN** é o de menor atrito
(API REST/JSON aberta, **sem credencial**) — escolhido (decisão do dono, 2026-06-06) para abrir o
**1º domínio novo** e **provar o contrato `ModuloDominio` com dado externo real** (`domains/financas`
plugando sem tocar o núcleo; a Onda 1 só provou o plugin com `trabalho`).

## Decisão
- **`AdaptadorSiconfi`** (medallion bronze→prata→ouro): parse do JSON da DCA → Polars; prata filtra a
  conta **Transferências Correntes** e normaliza `cod_ibge`/valor; ouro soma por município. **Contrato
  na borda bronze** (`ContratoFonte`, ADR-0017): exige `cod_ibge`, `valor`, `conta` — falha claro se o
  layout mudar. Fetcher real HTTP (aberto, `pragma: no cover`); parse/transform cobertos por fixture.
- **Indicador** `financas.transferencias.correntes` (DCA, **anual**, R$, polaridade neutra) + **fonte**
  `siconfi` — semeados; os fatos passam pelo **mesmo caminho ouro** (`escrever_ouro`: supressão +
  linhagem), nada de INSERT cru. A **API genérica** já serve (`/v1/indicadores?dominio=financas`,
  `/v1/valores?indicador=financas.transferencias.correntes`) — zero rota nova (Open/Closed).
- **`domains/financas`** (`ModuloFinancas`): registra o adaptador + o catálogo do indicador.

## ASSUNÇÕES a confirmar (lacuna sinalizada)
A URL/params/shape da DCA do SICONFI (`apidatalake.tesouro.gov.br/ords/siconfi/tt/dca`, nome do anexo,
nome exato da conta) são **assunções** — a confirmar contra a API real, como em ADR-0007/0010. O
contrato de dados falha claro se divergir.

## Consequências / a evoluir
- 1º domínio novo no ar (fatia vertical via seed→API), contrato `ModuloDominio` provado com fonte
  externa. **Próximos:** wiring do pipeline **live** (`run_siconfi` + Dagster); produto **TRANSP-06
  OndeFoi** (tela); **subíndice fiscal no IVM** (entra com o *IVM completo* → z-score v2, ADR-0018).
- Sequência seguinte da Onda 2A (por prontidão): **INEP → PNCP → DATASUS …**.
