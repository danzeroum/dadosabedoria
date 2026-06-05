# ADR-0007 — Ingestão BCB/ESTBAN (crédito por município)

- **Status:** aceito
- **Data:** 2026-06-05

## Contexto
Segunda fonte da Onda 1: ESTBAN (Estatística Bancária por Município, BCB) → indicador
`credito.operacoes.saldo_total`, insumo do **subíndice de finanças do IVM**. Reusa o padrão do
CAGED (ADR-0006), sem abrir exceção aos invariantes nem ao caminho de escrita.

## Decisão
- **`AdaptadorEstban`** conforme `AdaptadorFonte` (fetcher injetável; parse CSV em Polars; prata;
  ouro). O *tail* de carga (`_gravar_celulas`) e o mapa de territórios são **compartilhados** com o
  CAGED em `pipeline.py`; só extração/transformação mudam por fonte.
- **Plugin `credito`** (segundo `ModuloDominio`) — registra o adaptador e o indicador.
- **Dagster:** segundo job + schedule mensal (`job_estban`/`schedule_estban_mensal`), defasagem 3
  meses (lag ESTBAN ~60d).
- **CLI:** `python -m app.ingestao.run_estban <ano> <mes>`.

## Contrato de dados (ASSUNÇÕES a confirmar contra arquivo real — lacuna conhecida §“próxima
iteração”)
- **CODMUN** é o código IBGE de **7 dígitos** (casamento direto com `territorio.codigo_ibge`).
- A coluna de crédito é o **verbete 160** ("Operações de Crédito") — detectada por conter `"160"`
  no nome.
- O valor está em **R$ mil** → convertido para **reais** (×1000). Formato numérico brasileiro
  (separador de milhar `.`, decimal `,`) normalizado na prata.
- O arquivo real tem **preâmbulo** → `skip_rows=2` no fetcher real (a fixture de teste não tem).

Estas assunções estão isoladas em constantes/parâmetros do adaptador e cobertas por teste com
fixture; ajustá-las ao layout real do BCB é trivial e não toca o restante da esteira.

## Consequências
- `credito.operacoes.saldo_total` passa a ser alimentado por dados reais pela mesma API.
- Próxima fatia (IVM) já tem as duas pernas (emprego + finanças) para compor o índice.
