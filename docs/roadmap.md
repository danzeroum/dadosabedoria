# DadoSabedoria — Roadmap / Plano de execução

> **Fonte única do plano.** Vive no repo (sobrevive a resets do contêiner). Três camadas, marcadas
> com honestidade: **[B] definido no briefing**, **[A] já implícito nos ADRs** (executável sem
> perguntar), **🟡 proposta minha / decisão de produto** (pode parar e perguntar; tem default).

## Como usar (Claude e humanos)

- **Claude, no início de cada sessão:** leia este arquivo e o `CLAUDE.md`. Execute o **próximo item
  `[ ]` de cima para baixo**. Fluxo: branch nova ← `origin/main` → implementar (com teste) →
  push → PR → **CI verde** → merge → marcar `[x]` aqui (no mesmo PR ou no próximo) → seguir.
- **Não re-perguntar** itens `[B]`/`[A]`. Em itens **🟡**, use o *default proposto*; só pare para
  perguntar se a decisão for irreversível/cara e não houver default seguro.
- **Invariantes inegociáveis** (nunca afrouxar — README §Invariantes; ADR-0002): privacidade
  estrutural; isolamento de PII (analítico nunca lê `app`, testado); IA ancorada; API aditiva;
  proveniência sempre; economia de recurso; quality gate verde p/ merge; segredo só em env.
- **Para redirecionar:** edite este arquivo (reordene, adicione, mude 🟡). O Claude segue a ordem daqui.

---

## ✅ Concluído

- **Fundação executável** — esquema canônico, supressão única (k-anon) no único ponto de escrita,
  isolamento de PII (2 roles + RLS + rede), API de leitura com proveniência, observabilidade,
  quality gate. ADR-0001–0005. _(PR #1)_
- **Onda 1** [B] — backbone: ingestão **CAGED** + **BCB/ESTBAN** + **IBGE** (medallion) → **IVM**
  (view materializada, semáforo) → **frontend** Next.js (coropleta + drill-down). ADR-0006–0010.
  _(PRs #2–#6)_
- **Reforços da espinha** (dirigidos fatia a fatia) — **IA ancorada** (0011), **runtime de
  consentimento** + ciclo LGPD (0012), **runbooks** backup/rotação/DAGSTER_HOME (0013), **consumo
  de alertas** (0014), **provedor de LLM** DeepSeek/Ollama (0015). _(PRs #7–#11)_

Estamos **no fim da Onda 1**. Abaixo: fechar/endurecer a Onda 1, depois abrir a Onda 2.

---

## 🔜 Backlog imediato — fechar/endurecer a Onda 1

_Ordem de execução. Itens [A] saem dos "a evoluir" já escritos nos ADRs._

1. [ ] **[A] Anel de chaves p/ `APP_FIELD_KEY`** (segurança) — coluna `chave_versao` + `MultiFernet`
   p/ a cifragem + verificador HMAC multi-versão p/ o pseudônimo + re-chave preguiçoso no login.
   Hoje a chave é *não-rotacionável sem perda* (ADR-0012 §a-evoluir, ADR-0013 §APP_FIELD_KEY).
2. [ ] **[A] Agendar o consumo de alertas** após o REFRESH do IVM — scheduler no lado de
   consentimento (o `orchestrator` é analítico e não pode rodar o job). ADR-0014 §a-evoluir.
3. [ ] **[A] Rotação graciosa do `JWT_SECRET`** — aceitar lista de segredos (novo+antigo por uma
   janela), assinar só com o novo. ADR-0012/0013.
4. [ ] **[A] Marcar-como-lida** nas notificações (`lida_em` já existe) + filtro `?nao_lidas`. ADR-0014.
5. [ ] **[A] Dagster Degrau 2** — storage do Dagster em Postgres (run/event/schedule) ao escalar;
   validação de competência da ingestão. ADR-0006/0013, runbook dagster-home.
6. [ ] **[A] Carga nacional IBGE** (todas as UFs) + cache de malha mais agressivo + projeção
   apropriada. ADR-0010 §próximos.
7. [ ] **[A] Confirmar contratos reais** de CAGED/ESTBAN/IBGE contra arquivos reais (hoje há
   ASSUNÇÕES a confirmar — layout do FTP/zip, URLs do IBGE). ADR-0007/0010 §lacunas.
8. [ ] 🟡 **OIDC real do cidadão** — substitui o login v1 (JWT simples). **Decisão:** qual provedor
   de identidade (gov.br? Auth0? Keycloak self-hosted?). _Default proposto:_ **gov.br OIDC** (cidadão
   brasileiro) com Keycloak self-hosted como fallback de dev. ADR-0012.
9. [ ] 🟡 **TLS/ACME no Traefik** — habilitar HTTPS. **Decisão:** domínio público + `ACME_EMAIL`
   (já há placeholders no `.env.example` e bloco ACME templado). Sem domínio, fica em dev-mode.

---

## 🌊 Onda 2 — largura + profundidade + produto  🟡 _precisa da sua priorização_

> O briefing definiu a Onda 1 com precisão e deixou as ondas seguintes mais abertas (decisão de
> produto, §10). O que segue é **proposta**; edite a ordem/escopo.

### 2.A Largura — novos domínios no IVM
Cada domínio = novo `AdaptadorFonte` (medallion) + subíndice + peso no IVM (metodologia versionada).
- [ ] 🟡 **Saúde** — já há `saude.resp.internacoes_j` no seed (origem **sensível** → exige cuidado de
  supressão/revisão; bom primeiro candidato porque já modela o caso sensível). _Default: começar por
  aqui._ Fonte candidata: DATASUS/SIH.
- [ ] 🟡 **Educação** — ex.: INEP/Censo Escolar, IDEB (município/ano).
- [ ] 🟡 **Segurança** — ex.: SINESP / dados estaduais (heterogêneos).
- [ ] 🟡 **Fiscal/Transparência** — ex.: SICONFI (finanças municipais), execução orçamentária.

### 2.B Profundidade
- [ ] 🟡 Cobertura **nacional** (todos os municípios), múltiplos períodos, *backfill* histórico.
- [ ] 🟡 Qualidade: validação de competência, detecção de revisão de série, frescor vs lag (métrica
  `dadosabedoria_frescor_dias` já existe como stub).

### 2.C Produto (Open-Core Cívico — corte aberto × pago)
- [ ] 🟡 **Consultas em lote** (`/v1/consultas-lote`) — tier mais fundo (briefing). Auth + cota.
- [ ] 🟡 **API pública com chave** + planos/limites; documentação do contrato.
- [ ] 🟡 Definir o corte **core aberto × recurso pago** (o "Open-Core" do nome).

---

## 🔭 Onda 3+ — visão (hardening de produção & escala)

- [ ] WAF (OWASP CRS) como toggle de produção (ADR-0005/§gap).
- [ ] Deploy canário + auto-rollback (gatilho p95>300ms já honesto com o tuning de 16 GB).
- [ ] Observabilidade off-box (Grafana Alloy / retenção curta) — não co-residir 5 serviços pesados
  com api+ingestão na VPS de 16 GB (ADR-0005).
- [ ] Cifragem de backup por destinatário (chave pública) + game-day de restauração (ADR-0013).
- [ ] IA: streaming de tokens, cache por pergunta (§6), few-shot por domínio (ADR-0015).

---

## Decisões de produto pendentes (briefing §10)

| Decisão | Status | Default proposto (se você não redirecionar) |
|---|---|---|
| Provedor de LLM | ✅ **resolvido** | DeepSeek **ou** Ollama (config) — feito (ADR-0015) |
| Stack de frontend | ✅ **resolvido** | Next.js (ADR-0009) |
| Ordem de domínios (Onda 2) | 🟡 pendente | **Saúde primeiro** (já modela o caso sensível) |
| VPS / domínio / TLS | 🟡 pendente | dev-mode até existir domínio + `ACME_EMAIL` |
| OIDC do cidadão | 🟡 pendente | gov.br OIDC (fallback Keycloak self-hosted) |
| Credenciais existentes (DataJud etc.) | 🟡 pendente | usar só fontes abertas até você fornecer |
