# Ações Pendentes do Dono

Centraliza tudo que **só o dono pode resolver** para que o produto avance de estado atual
para produção real. O dev continua o roadmap enquanto estas pendências estão abertas —
nunca fica parado esperando.

> Atualizado automaticamente a cada fatia. Para análise detalhada de cada item, ver também
> `docs/PENDENCIAS_DO_DONO.md` e a `Lista de desbloqueio` em `docs/roadmap.md`.

---

## 🔴 Bloqueantes (impedem funcionalidade real)

### 1. FTP do DATASUS — `ftp.datasus.gov.br:21`
- **O que é:** o adaptador DATASUS/SIH baixa arquivos `.dbc` via FTP puro (porta 21). O
  contêiner só suporta HTTP/HTTPS; FTP nativo não está no allowlist.
- **O que fazer:** na **VPS** (não neste contêiner), executar:
  ```bash
  python -m app.ingestao.run_datasus 2026 2   # ou competência disponível
  ```
  Antes, garantir que `ftp.datasus.gov.br` esteja acessível na VPS (porta 21 aberta).
- **Destrava:** Sentinela Respiratória com dado real; subíndice de saúde do IVM; produtos
  SAUDE-02/03/04/05/06/11 quando implementados.

### 2. FTP do CAGED — `ftp.mtps.gov.br:21`
- **O que é:** CAGEDMOV nacional está em FTP puro; DNS HTTPS não resolve neste contêiner.
- **O que fazer:** na VPS, executar:
  ```bash
  python -m app.ingestao.run_caged 2026 4        # ou intervalo histórico
  # Ex. backfill: python -m app.ingestao.run_caged 2025 1 2026 4
  ```
  Ver `docs/RUNBOOK_DEPLOY.md §CAGED go-live` para detalhes.
- **Destrava:** Pulso Produtivo, Salário Radar, Região Emprega, Giro Local, IVM (subíndice
  trabalho) — hoje todos em modo "Demonstração" com seed de 2 municípios.

### 3. OIDC do cidadão — login real
- **O que é:** o login hoje usa JWT dev; falta o provedor de identidade real.
- **O que fazer:** escolher provedor (**gov.br/Login Único** recomendado para identidade
  cívica, ou Keycloak auto-hospedado) → criar client OIDC → fornecer como env vars:
  ```
  OIDC_ISSUER_URL=https://...
  OIDC_CLIENT_ID=...
  OIDC_CLIENT_SECRET=...
  ```
  No editor do ambiente (claude.ai/code → *Environment variables*).
- **Destrava:** auth do cidadão, alertas "Avise-me", toda Onda 2D (cidadão).

### 4. Domínio + TLS de produção
- **O que é:** Traefik em dev-mode (sem HTTPS real); falta domínio + ACME.
- **O que fazer:** registrar domínio → apontar DNS para a VPS → adicionar ao `.env`:
  ```
  PUBLIC_DOMAIN=seudominio.com
  ACME_EMAIL=seuemail@exemplo.com
  ```
  Depois: `docker compose restart proxy` para emitir o certificado Let's Encrypt.
- **Destrava:** produção com HTTPS, URLs públicas, redirect URIs do OIDC.

### 5. Chave de LLM (IA real)
- **O que é:** IA responde em template determinístico; falta credencial do provedor.
- **O que fazer:** fornecer como env vars:
  ```
  LLM_BASE_URL=https://api.deepseek.com/v1   # ou URL do Ollama
  LLM_MODEL=deepseek-chat
  LLM_API_KEY=sk-...
  ```
- **Destrava:** IA com geração real (respostas ancoradas com modelo de linguagem).

---

## ⚠️ Bloqueantes técnicos (não são só allowlist — têm problema próprio)

### 6. INEP — certificado TLS inválido
- **O que é:** `download.inep.gov.br` responde HTTP 503 (acessível), mas o certificado TLS
  do servidor é rejeitado (`CERTIFICATE_VERIFY_FAILED` — issuer não reconhecido).
- **O que fazer:** verificar se o INEP corrigiu o cert (conferir periodicamente) **ou**
  buscar URL alternativa com TLS válido no site do INEP/MEC. **Não desabilitar verificação
  TLS** — isso comprometeria a segurança.
- **Destrava:** ingestão real do Censo Escolar → EDU-01 Bússola e EDU-02 Radar com dado real.

### 7. ESTBAN/BCB — URL do download não encontrada
- **O que é:** `www.bcb.gov.br` e `dadosabertos.bcb.gov.br` estão acessíveis (HTTP 200),
  mas o BCB migrou para SPA Angular — as URLs históricas do ZIP do ESTBAN retornam HTML
  do SPA em vez do arquivo.
- **O que fazer:** inspecionar o bundle JS do SPA do BCB para localizar o endpoint real
  do ESTBAN, **ou** contatar BCB/COSIF diretamente para obter a URL de download.
  Candidato a testar: `https://www4.bcb.gov.br/fis/cosif/estban.asp`.
- **Destrava:** ingestão real do ESTBAN → crédito bancário por município → IVM (subíndice
  finanças) e Giro Local com dado real.

---

## 🟡 Decisões de produto (aguardam referendo)

### 8. OndeFoi — re-ancoragem do número (Liquidado ÷ Empenhado)
- **O que é:** o #0 confirmou que "recebido por função" não existe na fonte SICONFI. A
  ancoragem atual (Liquidado ÷ Empenhado) é honesta e source-grounded, mas altera a
  pergunta-título do produto. Tela permanece em grau-demo até o referendo.
- **O que fazer:** revisar a tela `/onde-foi/{ibge}`, confirmar que a moldura
  "Liquidado ÷ Empenhado = % executado do que foi empenhado" é a pergunta certa, e
  sinalizar ao dev (pode ser por mensagem neste repo ou na sessão do claude.ai/code).
- **Referências:** ADR-0028 §5, ADR-0029.
- **Destrava:** tela OndeFoi sai de grau-demo e passa a mostrar dado real sem o aviso
  "ilustrativo".

### 9. Conselho PbD (Privacy-by-Design)
- **O que é:** constituir conselho com Defensoria/ONGs antes de produtos de acesso
  restrito (HAB-04 Risco Moradia-Clima e DIR-01 via Defensoria).
- **O que fazer:** iniciar contato com Defensoria Pública e ONGs de referência em
  privacidade/direitos digitais para compor o conselho consultivo.
- **Destrava:** HAB-04 e DIR-01 — os demais produtos avançam independentemente.

---

## 📋 Checklist de primeiro deploy na VPS

Execute `scripts/preflight.sh` antes de `docker compose up` para garantir que todos os
segredos foram trocados. Ver `docs/runbooks/deploy.md §0`.

| Item | Status |
|---|---|
| `.env` preenchido (sem `change_me_*`) | ⬜ |
| `scripts/preflight.sh` passou | ⬜ |
| Domínio apontado para a VPS | ⬜ |
| `PUBLIC_DOMAIN` + `ACME_EMAIL` no `.env` | ⬜ |
| `OIDC_*` configurado | ⬜ |
| `LLM_*` configurado (ou Ollama rodando) | ⬜ |
| FTP `ftp.mtps.gov.br:21` acessível na VPS | ⬜ |
| CAGED ingerido (`run_caged`) | ⬜ |
| DATASUS ingerido (`run_datasus`) | ⬜ |
| OndeFoi — referendo da ancoragem | ⬜ |
