# ADR-0024 — Domínio `saude` via DATASUS/SIH (1ª fonte de origem sensível; Onda 2B)

- **Status:** aceito — forma real confirmada
- **Data:** 2026-06-06
- **Atualização:** 2026-06-11 — forma real validada contra RDRO2604 (Rondônia, 2026-04)
- **Atualização:** 2026-06-12 — política de UF ausente (550) revisada; ver §grain-v2

## Contexto
Concluída a sequência de fontes abertas de menor atrito da Onda 2A (SICONFI/INEP/PNCP), a Onda 2B
abre a saúde pelo **DATASUS/SIH** (Sistema de Informações Hospitalares). É a 1ª fonte de **origem
sensível** do acervo e o adaptador de **maior atrito** (FTP + arquivos DBC). O indicador
`saude.resp.internacoes_j` já existia no seed como exemplo sensível (com célula sub-limiar suprimida);
agora ganha seu adaptador e módulo de domínio.

## Decisão
- **`AdaptadorDatasus`** (medallion bronze→prata→ouro): parse do tabular do SIH-RD (uma linha por
  AIH) → Polars; prata filtra o diagnóstico principal do **grupo J** (CID-10 respiratório) e
  normaliza `MUNIC_RES`; ouro **conta** as AIH por município — a contagem é também o `n_amostra` que
  alimenta a supressão. **Contrato na borda bronze** (`ContratoFonte`, ADR-0017): exige `MUNIC_RES` e
  `DIAG_PRINC`. Fetcher real FTP+DBC (`pragma: no cover`, decodificação via PySUS), espelhando o
  padrão do CAGED (download/descompressão fora do teste; parse coberto por fixture).
- **Origem sensível:** nada de tratamento especial no adaptador — a contagem entra pelo **mesmo
  caminho ouro** (`escrever_ouro`), onde o k-anonimato com **piso sensível** suprime células abaixo
  do limiar (invariante 1). O indicador é `menor_melhor`, `n_minimo=5`, `origem_sensivel=true`.
- **`domains/saude`** (`ModuloSaude`): registra o adaptador + o catálogo do indicador existente.
  A API genérica já serve (`/v1/indicadores?dominio=saude`) — zero rota nova (Open/Closed).

## Forma real confirmada (2026-06-11, RDRO2604 — Rondônia 2026-04)

Diagnóstico executado na VPS com `scripts/diagnostico_datasus.py`: 9670 linhas × 114 colunas.
Decoder: `datasus_dbc.decompress` (Rust wheel, substitui `expand_dbc_to_dbf`) + dbfread + polars.

**Confirmados:**
- Caminho FTP: `/dissemin/publicos/SIHSUS/200801_/Dados/RD<UF><AAMM>.dbc` ✅
- `MUNIC_RES` presente (município de residência, 6 dígitos) ✅
- `DIAG_PRINC` presente (CID-10; grupo J confirmado na distribuição) ✅
- `DT_INTER` presente (data de internação, YYYY-MM-DD após decode) ✅
- IBGE do SIH tem 6 dígitos → mapa 6→7 no pipeline ✅

**Decisões decorrentes da forma real:**
- **Mês = DT_INTER (1.º dia do mês), NÃO `ANO_CMPT`/`MES_CMPT`** (competência de faturamento mistura meses). Ajustado no adaptador (`transformar_prata`) e no pipeline (`executar_datasus`).
- **Município = `MUNIC_RES`** (residência). `MUNIC_MOV` (local de internação) zeraria municípios sem hospital. Confirmado na nota honesta do produto.
- **Meses recentes incompletos**: AIH recentes ainda em faturamento → os últimos 1–2 meses do SIH são parciais. Caveat obrigatório no `NOTA_HONESTA` e na tela.
- **Fixture mínima** (`tests/fixtures/datasus.py`): `MUNIC_RES`, `MUNIC_MOV`, `DIAG_PRINC`, `DT_INTER`, `ANO_CMPT`, `MES_CMPT` — sem quasi-identificadores. Amostra bruta não comitada no repo.

## Grão: mensal (decisão 2026-06-11)

Avaliado se um fallback trimestral ou anual reduziria a supressão excessiva em municípios pequenos.
Ground-truth RO 2026-04: 90/137 células suprimidas a k=5 — taxa de ~65 %.

**Decisão: manter grão mensal como autoritativo.**

Justificativa:
- A supressão alta em municípios pequenos é **comportamento correto de privacidade** (ADR-0004), não
  um defeito do produto. Municípios com < 5 internações respiratórias/mês são, por definição, de baixo
  volume — revelá-los como número seria arriscar reidentificação.
- O grão mensal preserva o sinal de **sazonalidade** (pico inverno × verão), que é o principal valor
  da série respiratória. Um trimestre conflatiria julho (pico) com maio e junho.
- Alternativa trimestral seria um indicador separado (ex. `saude.resp.internacoes_j.trimestral`), não
  uma substituição — a adicionar quando um produto analítico exigir.

**Meses recentes parciais:** os últimos 1–3 meses do SIH têm AIH ainda em faturamento; a série
estabiliza após ~3–6 meses da competência. A tela marca esses meses com `*parcial`; a `NOTA_HONESTA`
e o `lag_tipico_dias=90` já comunicam o atraso estrutural.

## Política de UF ausente: 550 vs. erro transitório (§grain-v2, 2026-06-12)

Observado em produção (comp 2604): AC e RR retornaram 550 file-not-found — estados pequenos que
atrasam a publicação da competência. Retry é inútil: 550 é permanente até a UF publicar.

**Decisão: distinguir 550 de erro transitório e tratar de forma diferente.**

| Tipo de falha | Comportamento |
|---|---|
| Erro transitório (conexão, timeout, 4xx) | Abortar tudo — sem subcontagem (política original) |
| 550 file-not-found (`UFNaoPublicadaError`) | Ingere as UFs disponíveis; registra ausentes na proveniência |
| Nenhuma UF disponível (todas 550) | Abortar com mensagem clara |

**Justificativa para não abortar em 550:**
Via `MUNIC_RES`, a única subcontagem seria residentes da UF ausente que se internaram nela mesma.
Para AC (894 k hab, ~0,4 % da pop.) e RR (652 k hab, ~0,3 %) esse impacto é desprezível no
indicador nacional. Bloquear os outros 25 estados por duas UFs minúsculas prejudicaria a cobertura
sem benefício real de privacidade ou precisão.

**Proveniência honesta:** a string de URL retornada pelo fetcher passa a incluir
`UFs ainda não publicadas: AC, RR` — gravada nos metadados de cada carga e visível na API.
A mensagem de log orienta: *"use a competência anterior ou aguarde a publicação"* (não "tente novamente").

## Consequências / a evoluir
- 1ª fonte sensível com adaptador no ar; a supressão passa a ser exercida sobre uma fonte externa
  (não só no seed). **Próximos:** pipeline **live** (`run_datasus` + Dagster, incremental por
  competência, mapa 6→7); produtos SAÚDE com a **dupla face** do §17 (SAUDE-01 veda seguradora,
  SAUDE-02 geo ~500 m); demais sistemas DATASUS (SIA/CNES/SINAN/SINASC/SIM) e subíndice de saúde no
  IVM completo.
