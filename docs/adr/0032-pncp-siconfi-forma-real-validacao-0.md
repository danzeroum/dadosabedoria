# ADR-0032 — PNCP e SICONFI/funções: forma real confirmada no #0 (2026-06-08)

- **Status:** aceito
- **Data:** 2026-06-08
- **Relaciona:** ADR-0023 (PNCP/compras), ADR-0028 (SICONFI I-C), ADR-0029 (OndeFoi/I-E)

## Contexto

Sessão nova de 2026-06-08: sonda do bilhete-ponte confirmou os novos hosts abertos:
- `www.bcb.gov.br` e `dadosabertos.bcb.gov.br` → **200** (BCB/ESTBAN e CAGED via BCB)
- `download.inep.gov.br`, `pncp.gov.br`, `ftp.datasus.gov.br` → **503 sem `x-deny-reason`** (hosts atingíveis,
  porém servidor retorna erro — não é bloqueio de proxy)
- `ftp.mtps.gov.br` → **403 `resolve_no_records`** (FTP puro, DNS sem registro HTTPS)

Hosts abertura confirmada desde a sessão anterior: `apidatalake.tesouro.gov.br` (SICONFI) e
`servicodados.ibge.gov.br` (IBGE). Este ADR fecha o loop no papel para **PNCP** e **SICONFI/funções**
(Anexo I-E), cujos conectores eram "vivo-prontos" e aguardavam a 1ª busca real.

---

## PNCP — forma real confirmada

### Achados da 1ª busca real

Endpoint consultado: `https://pncp.gov.br/api/consulta/v1/contratos?dataInicial=20240101&dataFinal=20240131&pagina=1`

**Envelope de resposta:**
```json
{
  "data": [...],
  "totalRegistros": 35910,
  "totalPaginas": 72,
  "numeroPagina": 1,
  "paginasRestantes": 71,
  "empty": false
}
```

**Item de contrato (campos relevantes):**
- `valorGlobal`: **float** (na maioria; ocasionalmente **str** em dados heterogêneos — ex.: `"5335.13-31"`)
- `unidadeOrgao`: **Struct** com 6 campos:
  `codigoIbge` (str, IBGE 7 dígitos) · `municipioNome` · `ufSigla` · `ufNome` · `codigoUnidade` · `nomeUnidade`
- 41 campos por item no total

**Assunções confirmadas (vs. ADR-0023):**
- ✅ `data` (lista) + envelope de paginação
- ✅ `valorGlobal` presente e numérico
- ✅ `unidadeOrgao.codigoIbge` de 7 dígitos

**Achado novo — `valorGlobal` heterogêneo:** a API retorna `valorGlobal` como float na maioria dos
itens, mas eventualmente como string (ex.: `"5335.13-31"`). O `AdaptadorPncp.parse()` foi corrigido
de `pl.DataFrame(data)` para `pl.from_dicts(data, infer_schema_length=None)`, garantindo que todas as
linhas sejam varridas antes da inferência de tipo; a `transformar_prata()` já usava `cast(strict=False)`
que converte o inválido em null (filtrado em seguida).

**Achado novo — busca anual dá 500:** a URL com intervalo anual completo (`20240101–20241231`) retorna
HTTP 500 no servidor do PNCP. A estratégia correta é **iteração mensal** (12 sub-requests por mês +
paginação interna de cada mês). `FetcherPncpHTTP.baixar()` atualizado.

### Fixture promovida a fiel-à-forma

`tests/fixtures/pncp.py`: `_unidade()` agora retorna os 6 campos reais de `unidadeOrgao`; os itens
incluem campos extras reais (`anoContrato`, `tipoContrato`, `dataAssinatura`, etc.) **e** o item com
`valorGlobal = "5335.13-31"` que prova o tratamento heterogêneo.

---

## SICONFI/Anexo I-E — forma real reconfirmada + bug de ingestão nacional corrigido

### Achado — API exige `id_ente` por município

O ADR-0028 afirmou que "sem `id_ente` a API devolve todos os entes com paginação". **Validação de
2026-06-08 refuta isso:** sem `id_ente`, a API retorna sempre `count: 0 / hasMore: false`, para
qualquer exercício (2021–2025). A ingestão nacional requer loop explícito:

1. Listar municípios via `GET /tt/entes?an_exercicio={ano}&tipo_esfera=M` (paginado, ~5.500 itens)
2. Para cada `cod_ibge`, buscar DCA I-E: `GET /tt/dca?an_exercicio={ano}&no_anexo=DCA-Anexo+I-E&id_ente={cod_ibge}`

`FetcherSiconfiHTTP` (e `FetcherSiconfiFuncoesHTTP`) atualizados com `_listar_municipios()` +
`_baixar_ente()` via `ThreadPoolExecutor(max_workers=20)` — tempo esperado: ~2 min / ~5.500 municípios.

### Forma do Anexo I-E — confirmada (consistente com ADR-0028)

Testado contra SP (3550308), POA (4314902) e BH (3106200), exercício 2023:

```
Colunas: exercicio(int), instituicao(str), cod_ibge(int), uf(str), anexo(str),
         rotulo(str), coluna(str), cod_conta(str), conta(str), valor(float), populacao(int)
```

- `cod_conta` = `"TotalDespesas"` para todas as linhas I-E (constante — confirmado no #0/ADR-0028)
- `conta` = `"NN - Nome"` para função de 1º nível; `"NN.NNN - Nome"` para subfunção (ignorada)
- `coluna` ∈ {`"Despesas Empenhadas"`, `"Despesas Liquidadas"`, `"Despesas Pagas"`, …}
- **24 funções** observadas nas 3 amostras — consistente com ADR-0028

Fixture `AMOSTRA_FUNCOES` em `tests/fixtures/siconfi.py` já era **fiel-à-forma** (ADR-0028); sem mudança.

---

## ESTBAN (BCB) — host aberto, URL migrada ainda pendente

`www.bcb.gov.br` e `dadosabertos.bcb.gov.br` → **200**. O BCB migrou para um portal Angular (SPA):
todos os caminhos estáticos retornam a mesma página HTML. A URL binária do ZIP do ESTBAN precisa ser
descoberta via API backend do BCB — investigação iniciada (tentadas dezenas de variações de
`/api/servico/sitebcb/estban/…`; nenhuma retornou o arquivo binário).

`FetcherEstbanHTTP.BASE` atualizado para `www.bcb.gov.br/estabilidadefinanceira/docs/estban`, com
detecção de HTML + ValueError informativo. A URL real pode seguir o padrão
`/estabilidadefinanceira/cosif/estban/{ano}/ESTBAN_MUNICIPIO_{AAMM}.ZIP` — a confirmar em sessão nova.
Parse/agregação seguem cobertos por fixture.

## INEP / DATASUS / CAGED — 503 / FTP inacessível

- **INEP** (`download.inep.gov.br`): host atingível (sem `x-deny-reason`), mas todas as URLs de
  microdados retornam HTTP 503 — servidor temporariamente indisponível. Vivo-pronto; retentar na
  próxima sessão.
- **DATASUS** (`ftp.datasus.gov.br`): HTTPS 503 e FTP/porta 21 bloqueada pelo proxy. O
  `FetcherDatasusFTP` usa `ftplib` — FTP não é suportado pelo proxy atual. Vivo-pronto; gate de
  protocolo.
- **CAGED** (`ftp.mtps.gov.br`): 403 `resolve_no_records` (FTP puro, sem HTTPS). Mesma situação.

## Consequências

- **ADR-0028 corrigido:** a afirmação de paginação nacional sem `id_ente` era incorreta; o fetcher
  nacional agora usa loop sobre entes (documentado aqui).
- **Fixtures PNCP** promovidas a fiel-à-forma.
- **Conectores SICONFI/funções e PNCP** passam dos testes com forma real travada.
- **Lista de desbloqueio** atualizada: ESTBAN URL, INEP/DATASUS/CAGED status.
