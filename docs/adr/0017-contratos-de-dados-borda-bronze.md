# ADR-0017 — Contratos de dados na borda bronze (validação de layout por fonte)

- **Status:** aceito
- **Data:** 2026-06-06

## Contexto
Os adaptadores (CAGED, ESTBAN) selecionam colunas por nome no transform prata. Se a fonte pública
mudar o layout (renomear/remover coluna, arquivo vazio), o erro só aparecia fundo no pipeline, como
exceção críptica do Polars — tarde e pouco diagnóstica. O doc técnico pedia **contratos de dados
formais por fonte** (lacuna "próxima iteração", ADR-0007/0010).

## Decisão
- **`app/ingestao/contratos.py`:** `ContratoFonte` declarativo do bruto tabular —
  `colunas_obrigatorias` (presença), `coluna_contendo` (ao menos uma coluna contém um texto — p/ o
  verbete de crédito **dinâmico** do ESTBAN) e `min_linhas`. `validar(df)` levanta
  `ContratoVioladoError` com mensagem clara (o que faltou, o que veio) — **falha rápido**.
- **Checado na borda bronze:** cada adaptador declara seu `CONTRATO` e o valida no `extrair()`, logo
  após o parse, antes de prata/ouro. Dado fora do contrato não alcança a regra de supressão nem o
  acervo.
  - CAGED: `competênciamov`, `município`, `saldomovimentação`.
  - ESTBAN: `CODMUN` + ao menos uma coluna do verbete `160` (Operações de Crédito).
- **Testável sem rede:** o contrato é puro; testes usam fixture (a amostra real passa; um bruto com
  layout mudado reprova no `extrair`).

## Consequências / a evoluir
- Mudança de layout da origem vira erro **claro e precoce** (qualidade comprovada, §13), com a fonte
  e as colunas no texto — facilita o diagnóstico e protege o acervo.
- **IBGE** (malhas/municípios em JSON) tem forma diferente (não-tabular); seu contrato estrutural do
  JSON fica como próximo passo. Tipos/intervalos por coluna e checagem de defasagem também podem
  entrar no `ContratoFonte` quando houver necessidade.
