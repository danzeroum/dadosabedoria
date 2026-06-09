# ADR-0034 — OndeFoi: investigação de escala e testes de regressão

**Data:** 2026-06-09  
**Status:** Aceito  
**Contexto:** PASSO 1 da sessão 2026-06-09 — investigar "SP/Saúde/2024 ≈ R$ 1,5 bi" vs. real ~R$ 17–18 bi

---

## Contexto

O prod (dadosabedoria.buildtovalue.cloud) serve OndeFoi em grau-demo (rotulado "demonstração"). Em
sessões anteriores foram observados valores de escala errada: SP/Saúde/2024 ≈ R$ 1,5 bi, mas o
Fundo Municipal de Saúde público (2024) é da ordem de R$ 17–22 bi. A suspeita era: (a) erro de
unidade/escala na ingestão, (b) divisão acidental, ou (c) mesma coluna lida duas vezes
(empenhado == liquidado exatamente).

---

## Investigação (2026-06-09)

### Três pontos de comparação

| Ponto | SP / Saúde / 2024 (função 10) |
|-------|-------------------------------|
| (a) API cru SICONFI | Empenhado = R$ 22.752.837.820,49 · Liquidado = R$ 21.927.842.055,50 |
| (b) `execucao_funcao` (DB) | empenhado = 22752837820.49 · liquidado = 21927842055.5 ✓ idêntico à fonte |
| (c) `/v1/onde-foi/3550308` | emp = 22.752.837.820 · liq = 21.927.842.056 · pct = 96% · banda = alta ✓ |

Os três pontos são **coerentes** — nenhum fator de escala está se perdendo.

### Causa raiz do valor errado anterior (R$ 1,5 bi)

O valor R$ 1,5 bi vem da **seed** do indicador `financas.transferencias.correntes`
(`app/seed/__init__.py`, `Decimal("1.50e9")`), que é o DCA **Anexo I-C** (receitas), não o Anexo
I-E (despesas por função). O OndeFoi lê o **Anexo I-E** via `execucao_funcao`; os dois indicadores
não se sobrepõem.

O motivo pelo qual o endpoint retornava dados errados anteriormente:
1. As **duas primeiras execuções** de `run_siconfi_funcoes` em 2026-06-08 gravaram **0 linhas** por
   causa de um bug do asyncpg (limite de 32.767 parâmetros por query; INSERT com ~133.000 linhas ×
   8 colunas ≈ 1 M parâmetros — `InterfaceError`).
2. Com `execucao_funcao` vazia, o endpoint retornava 404 (não havia fallback com dados errados).
3. O bug foi corrigido em PR #87 (batch INSERT de 3.000 linhas); a terceira execução gravou
   83.444 linhas corretamente.

### Suspeita "empenhado == liquidado"

Não confirmada com os dados reais. No DB: empenhado ≠ liquidado (22,75 bi ≠ 21,93 bi). A suspeita
era de que `agregar_funcoes` lesse a mesma coluna duas vezes:
```python
pl.col("valor").filter(pl.col("coluna") == COLUNA_EMPENHADO).sum()  # "Despesas Empenhadas"
pl.col("valor").filter(pl.col("coluna") == COLUNA_LIQUIDADO).sum()   # "Despesas Liquidadas"
```
As duas constantes são **distintas** e os filtros corretos. O SICONFI Anexo I-E retorna 5 colunas
(`Despesas Empenhadas`, `Despesas Liquidadas`, `Despesas Pagas`, `Inscrição RAP Não Processados`,
`Inscrição RAP Processados`); o pipeline filtra apenas as duas primeiras.

---

## Falha descoberta: isolamento dos testes de pipeline

Ao re-executar os testes após a ingestão nacional (83.444 linhas reais em `execucao_funcao`), dois
testes falharam:

- `test_pipeline_grava_execucao_por_funcao` — esperava 4 linhas para SP/2024, obteve 24 (as 24
  funções reais da ingestão nacional).
- `test_pipeline_funcoes_idempotente` — `assert n == 4` obteve 24.

**Causa:** os testes de pipeline (`test_siconfi_funcoes_pipeline.py`) **não limpavam** a tabela
`execucao_funcao` antes de rodar, ao contrário dos testes de API (`test_onde_foi_api.py`, que já
tinham `_limpar()`).

**Correção:** adicionada função `_limpar()` (via `ADMIN_DATABASE_URL`, igual à de `test_onde_foi_api`)
e chamada no início de cada teste de pipeline que depende de estado limpo.

---

## Decisão

1. **Testes de pipeline isolados**: `test_siconfi_funcoes_pipeline.py` agora chama `_limpar()` antes
   de cada teste de pipeline, garantindo estado determinístico independente de ingestões reais.

2. **Guardas de ordem de grandeza**: adicionadas asserções explícitas ao teste de pipeline:
   - `float(saude["liquidado"]) > 10e9` — trava escala: deve ser dezenas de bilhões, não milhões.
   - `float(saude["empenhado"]) > 10e9` — idem.
   - `saude["empenhado"] != saude["liquidado"]` — trava leitura dupla de coluna.

3. **Fixture fiel-à-forma mantida**: a fixture `AMOSTRA_FUNCOES` usa os valores reais de SP/2024
   (empenhado=22.752.837.820,49, liquidado=21.927.842.055,50), garantindo que os testes detectem
   qualquer regressão de escala.

4. **Ingestão nacional re-executada** (2026-06-09): após os testes limparem a tabela, a ingestão
   nacional 2024 foi re-executada via `run_siconfi_funcoes 2024`.

---

## Consequências

- CI agora é **resistente a estado residual**: os testes passam tanto num DB limpo quanto num DB que
  já tenha dados reais da ingestão.
- A guarda `> 10e9` detecta se uma futura alteração introduzir erro de escala (divisão por 1000,
  conversão errada de unidade, etc.).
- O OndeFoi em grau-demo permanece correto — o rotulo "demonstração" reflete que a tela ainda aguarda
  o referendo do dono (🟡 ADR-0029); os dados subjacentes são reais e corretos.
