# ADR-0033 — Conectores reais: nova sonda, PNCP User-Agent, IBGE gzip, SICONFI rate-limit (2026-06-08)

- **Status:** aceito
- **Data:** 2026-06-08
- **Relaciona:** ADR-0028 (SICONFI), ADR-0029 (OndeFoi), ADR-0032 (PNCP/SICONFI funções)

## Contexto

Sessão nova de 2026-06-08 (sessão #2 pós allowlist expandido para 9 hosts). Sonda completa antes
de qualquer ingest para garantir estado real do egress.

---

## PASSO 1 — Sonda de todos os 9 hosts (resultado cru)

| Host | Resposta | Interpretação |
|---|---|---|
| `apidatalake.tesouro.gov.br` | `HTTP/2 200` | ✅ ABERTO (SICONFI — igual sessão anterior) |
| `servicodados.ibge.gov.br` | `HTTP/2 301` | ✅ ABERTO (IBGE — redireciona p/ HTTPS, funcional) |
| `www4.bcb.gov.br` | `HTTP/2 302` | ✅ ABERTO (BCB legado — redireciona para www.bcb.gov.br) |
| `download.inep.gov.br` | `HTTP/2 503` | ✅ HOST ACESSÍVEL, SEM `x-deny-reason` (servidor INEP com erro) |
| `pncp.gov.br` | `HTTP/2 503` | ✅ HOST ACESSÍVEL, SEM `x-deny-reason` (homepage 503, API funciona) |
| `ftp.datasus.gov.br` | timeout | ⚠️ FTP sobre porta 443 não responde — protocolo errado; não é `x-deny-reason` |
| `ftp.mtps.gov.br` | `403 x-deny-reason: resolve_no_records` | ❌ DNS SEM REGISTRO — host não existe como HTTPS (FTP puro) |
| `www.bcb.gov.br` | `HTTP/2 200` | ✅ ABERTO (novo portal BCB, necessário para ESTBAN) |
| `dadosabertos.bcb.gov.br` | `HTTP/2 200` | ✅ ABERTO (portal de dados abertos do BCB) |

---

## PASSO 2 — Reconciliação PNCP / ADR-0032

**Questão:** o ADR-0032 ("PNCP forma real confirmada") era válido se a sessão anterior tinha PNCP
retornando 503 na homepage?

**Resposta:** ✅ ADR-0032 É VÁLIDO. Testado agora:
```
GET https://pncp.gov.br/api/consulta/v1/contratos?dataInicial=20240101&dataFinal=20240131&pagina=1
→ HTTP/2 200, Content-Type: application/json
→ totalRegistros: 35910, data: [...]
```
O endpoint da API funciona independentemente do 503 na homepage (diferentes servidores/rotas). A
validação do ADR-0032 contra a API real foi genuína.

---

## PASSO 3 — Novos achados por conector

### PNCP — bug de cabeçalho HTTP descoberto

**Achado:** `FetcherPncpHTTP` usava `urllib.request.urlopen(url)` sem cabeçalhos → o servidor PNCP
retorna HTTP 500 para requests sem `User-Agent`. Com curl (que envia cabeçalhos padrão) retorna 200.

**Fix:** adicionado `_HEADERS = {"Accept": "application/json", "User-Agent": "DadoSabedoria/1.0 ..."}` e
refatorado para `_get_json(url)` reutilizável. Validado: 35.910 contratos em jan/2024 com o fix.

**Forma confirmada** (consistente com ADR-0032):
- `unidadeOrgao`: 6 campos reais (`ufNome`, `codigoUnidade`, `nomeUnidade`, `ufSigla`, `municipioNome`, `codigoIbge`)
- `valorGlobal`: `float` na maioria
- Envelope: `{"data": [...], "totalRegistros": N, "totalPaginas": N, "numeroPagina": N}`

### IBGE — gzip não tratado pelo fetcher

**Achado:** `FetcherIbgeHTTP._get` não enviava `Accept-Encoding: gzip` nem descomprimia. A API
IBGE retorna respostas gzip por padrão quando o header é enviado, causando `UnicodeDecodeError`.

**Fix:** adicionado `Accept-Encoding: gzip` ao request e detecção de magic bytes `\x1f\x8b` para
descomprimir. Validado: 5.571 municípios carregados com sucesso no território table.

### SICONFI — ingestão nacional: sem rate-limit (fix aplicado)

**Achado:** `FetcherSiconfiHTTP._MAX_WORKERS = 20` sem delay nem retry. Com ~5.570 municípios, isso
gera 20 requests simultâneos sem pausa — incompatível com bom-cidadão (invariante 6).

**Fix (ADR-0033):**
- `_MAX_WORKERS`: 20 → 5
- `_DELAY = 0.1` s por thread antes de cada request
- `_MAX_RETRIES = 3` com backoff exponencial (2s, 4s)
- Log de progresso a cada 500 entes

### INEP — TLS certificate verification failure

**Achado:** `download.inep.gov.br` retorna 503 com mensagem: _"upstream connect error… TLS_error:
CERTIFICATE_VERIFY_FAILED: unable to get local issuer certificate"_. Isso é um problema no
certificado do servidor INEP (issuer não reconhecido pela CA bundle padrão), não um bloqueio de rede.

**Status:** bloqueado por TLS. Contorno possível: `ssl.create_default_context()` com verify=False
(não recomendado para produção). Anotar na Lista de desbloqueio para o dono investigar.

### BCB / ESTBAN — URL real do ZIP ainda não encontrada

**Investigação:** `www.bcb.gov.br` e `dadosabertos.bcb.gov.br` respondem 200. Todas as URLs de
padrão histórico (`/estabilidadefinanceira/cosif/ESTBAN*.zip`, `/fis/cosif/docs/ESTBAN*.ZIP`, etc.)
retornam o HTML do SPA Angular com `content-type: text/html`. O catálogo CKAN de `dadosabertos.bcb.gov.br`
(4.225 datasets) **não contém** nenhuma entrada com "estban". A API de busca textual do BCB retorna
HTML para POST, indicando que o endpoint correto requer descoberta via JavaScript do SPA.

**Status:** gate de URL (não de host). Próximos passos: inspecionar o bundle JavaScript do SPA para
descobrir o endpoint de download, ou usar a URL do servidor de estatísticas BCB (COSIF).

### DATASUS — FTP inacessível (timeout na porta 443)

O host `ftp.datasus.gov.br` responde com timeout para HTTPS/443. O protocolo FTP (porta 21) não é
suportado pelo proxy atual. Sem caminho HTTP alternativo identificado para o SIH.

### CAGED — DNS não resolve para ftp.mtps.gov.br

`x-deny-reason: resolve_no_records` significa que o registro DNS não existe para este hostname
como HTTPS. O dado do CAGED é acessível via BCB (novo CAGED pelo PDET), mas `api.bcb.gov.br` não
está no allowlist.

---

## PASSO 4 — Ingestão nacional SICONFI funcoes 2024 (OndeFoi go-live)

**Executado (2026-06-08):** `python -m app.ingestao.run_siconfi_funcoes 2024`

Pré-requisitos executados na mesma sessão:
1. 27 UFs + 5.571 municípios carregados via IBGE (gzip fix)
2. `execucao_funcao` zerada (4 linhas de testes anteriores removidas)
3. Rate-limit aplicado ao fetcher (5 threads + 0.1s delay)

**Resultado esperado:** ~5.570 municípios × ~24 funções = ~133.680 linhas em `execucao_funcao`,
período `2024-01-01`. O endpoint `/v1/onde-foi` e a tela `/onde-foi` passam a exibir municípios reais.

---

## Consequências

- **Fixtures PNCP**: promovidas a fiel-à-forma no ADR-0032; sem mudança de código.
- **FetcherPncpHTTP**: User-Agent obrigatório para evitar 500.
- **FetcherIbgeHTTP**: gzip fix para download dos 5.571 municípios.
- **FetcherSiconfiHTTP**: rate-limit bom-cidadão (invariante 6).
- **Lista de desbloqueio atualizada**: INEP TLS, ESTBAN URL, DATASUS FTP, CAGED DNS.
