# ADR-0039 — Validação ao vivo dos 13 conectores (rede aberta, 2026-07-01)

**Status:** Aceito
**Data:** 2026-07-01
**Contexto:** Sessão nova com egress ABERTO para todos os hosts de coleta. Varredura profunda:
cada conector exercido contra o endpoint REAL, comparando a forma retornada com o que o adaptador
espera (mesmo padrão do #0/ADR-0028).

---

## Contexto

Diferente das sessões anteriores (github-only, 403 nas fontes), esta sessão teve a política de rede
em modo que permite os hosts de coleta — confirmado pela sonda (nenhum `x-deny-reason`). Aproveitou-se
a janela para exercer **os 13 conectores** contra o dado real, uma busca mínima por fonte, e confrontar
a forma real com o contrato de cada adaptador. Um agente de validação por fonte (ou par que compartilha
host), read-only, com evidência de amostra real.

**Limite do ambiente:** o egress passa por um proxy **HTTPS-only (só CONNECT)**. Isso significa que
(a) FTP na porta 21 **não** é tunelado e (b) fetchers em `http://` puro (urllib) também não passam.
Logo, "rede aberta" aqui = HTTPS aos hosts permitidos, **não** FTP.

---

## Placar (13 conectores)

| # | Conector | Host | Veredito | Evidência real |
|---|---|---|---|---|
| 1 | **SICONFI** (DCA) | apidatalake.tesouro.gov.br | ✅ FUNCIONAL | `/tt/entes`+`/tt/dca` 200; Juiz de Fora 2023, conta `RO1.7.0.0.00.0.0`, 3 colunas do ADR-0028 batem |
| 2 | **IBGE** (pop/malhas) | servicodados.ibge.gov.br | ✅ FUNCIONAL | `/localidades`+`/malhas` 200; `id/nome/UF`+`codarea`/geometry batem |
| 3 | **PNCP** (contratos) | pncp.gov.br | ✅ FUNCIONAL | Adelândia-GO; `valorGlobal`+`unidadeOrgao.codigoIbge`+`totalPaginas`; esteira parse→prata→ouro sem perdas |
| 4 | **PAM** (produção agrícola) | servicodados.ibge.gov.br | 🔴→✅ CORRIGIDO | var 762 dava HTTP 500 (não existe); correto = **215** (Boa Vista/RR 2023 = 307383) |
| 5 | **ANEEL** (DEC/FEC) | dadosabertos.aneel.gov.br | 🔴 QUEBRADO | slug errado + dado é formato-longo por conjunto de consumidores, sem `cod_ibge`, `SigIndicador` em vez de colunas `dec/fec` |
| 6 | **ANA** (secas) | monitordesecas.ana.gov.br | 🔴 QUEBRADO | fetcher pega HTML da SPA; API real (`apimsbr.ana.gov.br`) é JSON sem grão município, escala S0–S4 ≠ D0–D4 |
| 7 | **SISVAN** (nutrição) | s3…/ckan.saude.gov.br | 🔴 QUEBRADO | S3 403 AccessDenied; fonte migrou p/ JSON em `apidadosabertos.saude.gov.br` com schema diferente |
| 8 | **ESTBAN** (crédito) | www.bcb.gov.br | 🔴 QUEBRADO | URL de download devolve HTML da SPA, não ZIP; caminho real não descoberto (fixture sintética) |
| 9 | **SNIS** (saneamento) | app4.mdr.gov.br | ⚠️ INDISPONÍVEL | origem retorna **502** (fora do ar); ainda usa `http://` que não passa no proxy CONNECT |
| 10 | **INEP** (censo escolar) | download.inep.gov.br | ⚠️ BLOQUEADO-HOST | falha de TLS no host (`SSL_ERROR_SYSCALL`), não é allowlist |
| 11 | **DATASUS/SIH** | ftp.datasus.gov.br | ⚠️ BLOQUEADO-REDE | FTP:21 não tunelado pelo proxy HTTPS-only |
| 12 | **SINAN** (dengue) | ftp.datasus.gov.br | ⚠️ BLOQUEADO-REDE | idem FTP:21; forma das 3 colunas nunca validada (assunção) |
| 13 | **CAGED** (emprego) | ftp.mtps.gov.br | ⚠️ BLOQUEADO-REDE | idem FTP:21; **forma já validada por fixture/ADR-0036** (pronto-para-vivo) |

**Resumo:** 3 funcionais confirmados ao vivo · 1 bug corrigido (PAM) · 4 quebrados estruturais
(ANEEL/ANA/SISVAN/ESTBAN) · 5 não validáveis neste ambiente por rede/host.

---

## Decisão

### Corrigido nesta sessão (commit "corrige PAM…")
- **PAM**: `FetcherPamHTTP._VAR` `"762"` → `"215"`. A var 762 não existe nos metadados das tabelas
  1612/1613 e retorna HTTP 500; a 215 é "Valor da produção" (Mil Reais), confirmada ao vivo nas duas
  tabelas. Proveniência (invariante 5) atualizada em seed/prato_frio/rotas/orquestração/fixture.
  `codigo_externo` `"PAM_762"` mantido (identificador opaco, sem outras referências). O parser/prata/
  ouro já casavam com a forma real — só o ID da variável no fetcher estava errado.

### Registrado — exige mais que um ajuste pontual (NÃO corrigido nesta sessão)
Cada um destes é uma **fatia de trabalho** (adaptador + fetcher + contrato + fixture fiel), não uma
linha:
- **ANEEL**: adotar CKAN `datastore_search` do pacote `indicadores-coletivos-de-continuidade-dec-e-fec`;
  reescrever parser para formato-longo (`SigIndicador`) e **derivar `cod_ibge`** via ponte
  conjunto-de-unidades→município (fonte externa; o dataset não tem geografia municipal).
- **ANA**: trocar para `apimsbr.ana.gov.br/rpc/v1/dados-tabulares-monitor`; **decisão de produto**: a
  API só serve grão UF/Região/País (sem município, sem `cod_ibge`) e usa severidade S0–S4 — não casa
  com o grão território×período por IBGE sem derivação adicional.
- **SISVAN**: migrar para `apidadosabertos.saude.gov.br/sisvan/estado-nutricional` (JSON); reescrever
  contrato/colunas (`codigo_municipio`, `crianca_imc_x_idade` textual, etc.).
- **ESTBAN**: descobrir o caminho real do ZIP (rodar `scripts/diagnostico_estban.py` no VPS); a URL
  hardcoded caiu com a migração do BCB para SPA. O fetcher já falha limpo (guarda de magic-bytes `PK`).

### Bloqueio de ambiente (não é bug de código)
- **FTP (DATASUS/SINAN/CAGED)**: o proxy só faz CONNECT/HTTPS; FTP:21 dá timeout. Validação real só na
  VPS de rede aberta. CAGED continua **pronto-para-vivo** (forma validada por fixture, ADR-0036).
- **INEP**: TLS reset do host pelo nó de egress; reexaminar quando o handshake completar.
- **SNIS**: origem 502 (indisponibilidade da fonte) **e** fetcher em `http://` incompatível com o
  proxy CONNECT — corrigir o esquema/ajuste de proxy é pré-requisito da validação.

---

## Consequências

- **Confiança calibrada:** dos 13 conectores, apenas **SICONFI, IBGE e PNCP** têm forma confirmada
  contra dado real vivo nesta sessão; PAM passa a ter o fetcher correto (mas a ingestão nacional só na
  VPS). Os demais permanecem **pronto-para-vivo com ressalva** — a esteira roda em CI por fake, mas a
  forma real de ANEEL/ANA/SISVAN/ESTBAN **diverge** e a de INEP/DATASUS/SINAN segue não confirmada.
- **Glossário "vivo" reforçado (CLAUDE.md):** "esteira pronta" ≠ "forma validada". Quatro conectores
  que constavam como esteira pronta têm forma **incompatível** com a fonte real atual — a validação ao
  vivo era o único jeito de descobrir.
- **Próximas fatias sugeridas (roadmap):** priorizar as reescritas por valor de produto; ANEEL/ANA
  dependem de ponte/derivação municipal (decisão de escopo antes de codar).
</content>
</invoke>
