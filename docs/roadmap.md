# DadoSabedoria — Roadmap de Ondas de Desenvolvimento

Plano completo das ondas de desenvolvimento, do estado atual até a escala multiproduto. **Fonte
única do plano** (vive no repo, sobrevive a resets do contêiner). Serve para o desenvolvimento
**autônomo**: leia de cima para baixo, execute o próximo item aberto `[ ]`, e **pare apenas nas
decisões marcadas 🟡** (decisões de produto do dono). Fluxo de cada fatia: branch ← `origin/main` →
implementar com teste → push → PR → **CI verde** → merge → marcar `[x]` aqui → próximo item.

## Como usar (legenda)

- `[ ]` item executável; `[x]` concluído.
- **Camadas de autoridade** (honestidade sobre a origem de cada item):
  - **🟢 Definido** — vem do briefing / documento técnico / esquema. Executar sem perguntar.
  - **🔵 Backlog implícito** — decorre dos invariantes e ADRs; executável sem perguntar.
  - **🟡 Decisão de produto** — escolha do dono (§10 do briefing). **Pare** (ou siga o default se o
    dono autorizou "siga sem perguntar").
- Cada onda termina num **critério de saída** com a mesma régua de qualidade.

## Estado atual (reconciliação — 2026-06-06)

16 PRs mergeados; ADRs 0001–0018. **Adiantado** em capacidades transversais em relação à sequência
do briefing: o consentimento (runtime + ciclo LGPD + **anel de chaves**), a **IA ancorada** (RAG +
guardrails + **provedor de LLM** DeepSeek/Ollama) e os **runbooks** (backup/restore com PII separada,
rotação) já estão entregues — eles aparecem na Onda 2D/Onda 0 e estão marcados `[x]` abaixo. **Falta
largura**: mais domínios/produtos (Ondas 2–3) e as fontes de ETL médio/pesado.

- **Onda 0 (Fundação): COMPLETA** ✅ — ADRs 0001–0005, 0013, 0016.
- **Onda 1 (Backbone + IVM básico): essencialmente completa** — ADRs 0006–0010, 0017, 0018;
  contratos de dados + frescor + calibrações 🟡 (IVM, design tokens) resolvidos; só faltam os
  **produtos TRAB extra** (precisam de definição de produto/fonte).
- **Onda 2D (cidadão + IA + open-core): parcial** — consentimento/IA/LLM `[x]` (ADRs 0011, 0012,
  0014, 0015, 0016); faltam OIDC real e a camada profunda paga.

## Princípios que valem em TODAS as ondas

1. **Invariantes inegociáveis** (doc técnico §0): privacidade estrutural (supressão antes de gravar),
   isolamento de PII (schema `app`, duas roles, teste que reprova o build), IA ancorada com citação,
   não quebrar o passado (expand-and-contract), proveniência sempre, economia de recurso, quality
   gate verde, segredo nunca no código.
2. **Duas lentes reconciliadas.** A *ordem de construção* segue **prontidão de dado** (fontes de
   menor atrito primeiro, montando o backbone). A *escolha de produtos no alcance* segue **valor de
   produto**. Quando colidem, a construção manda.
3. **Fatias verticais.** Todo incremento atravessa do dado à API/tela, testado e observável.
4. **Plugar, não reescrever.** Cada domínio entra pelo contrato `ModuloDominio` (§6), zero mudança no
   núcleo. Extrair serviço só ao bater o gatilho objetivo (§1.1).
5. **Dupla face por produto.** Antes de publicar um produto, aplique a mitigação do registro de risco
   (doc técnico §17). Risco alto = mitigação no design, nunca retrofit.
6. **Economia medida.** Pré-computar → cachear → incremental, antes de escalar hardware. Alvo: VPS
   4 vCPU / 16 GB. Subir recurso/serviço só quando o gatilho numérico disparar.

---

## ONDA 0 — Fundação executável  ✅ COMPLETA

**Objetivo:** a base permanente — fatia vertical do banco à API de leitura, contratos presos desde o
1º commit, sem ingestão externa.

- [x] 🟢 Scaffold do monorepo, `docker-compose` mínimo (proxy/api/db/redis/migrator).
- [x] 🟢 Migrações Alembic (autogenerate-off, expand-and-contract) do esquema canônico §3.
- [x] 🟢 Schema `app` isolado: duas roles, GRANT/REVOKE, RLS `FORCE`, redes separadas, segredos
  segregados; **teste de negação de PII** (controle ±) que reprova o build; **compose-static check**.
- [x] 🟢 Regra única de supressão (k-anon, Strategy) + caminho único de gravação ouro
  (`escrever_ouro`); seeds passam por esse caminho.
- [x] 🟢 API de leitura `/v1/indicadores|valores|territorios` com `meta` de proveniência via
  `valor_publico`; envelope de erro; OpenAPI com diff-gate.
- [x] 🟢 Observabilidade (structlog JSON + scrubber de PII, OTel, `/metrics`, `/health`), CI quality
  gate, ADRs 0001–0004, README.
- [x] 🔵 **Anel de chaves para `APP_FIELD_KEY`** (MultiFernet + re-chave preguiçoso no login + CLI de
  re-cifragem) — ADR-0016.
- [x] 🔵 Tuning do Postgres em `infra/postgres/` (shared_buffers/effective_cache_size/work_mem) — ADR-0005.
- [x] 🔵 **MinIO** no profile de ingestão (stack padrão = proxy/api/db/redis/migrator) — ADR-0005.
- [x] 🔵 `/metrics` interno (nunca roteado pelo entrypoint público do Traefik).
- [x] 🔵 Guard de ENUM via bloco `DO $$ … pg_type … $$` (re-run idempotente) — migração 0001.
- [x] 🔵 Runbook de **backup/restore** com o backup do `app` **separado** do acervo (§8.1.5) — ADR-0013.

**Critério de saída:** ✅ CI verde; invariantes por teste; contratos congelados; stack mínima saudável.

---

## ONDA 1 — Backbone de dado + IVM básico  (núcleo completo)

**Objetivo:** ligar a ingestão real pelas fontes de menor atrito e entregar o produto-âncora visível.
Convergência: **TRAB-01 (Pulso Produtivo) + TRANSP-01 (IVM básico)**.

**Capacidades / infra:**
- [x] 🟢 Contrato `AdaptadorFonte` + medallion **bronze→prata→ouro**; MinIO bronze (profile ingestão) — ADR-0006.
- [x] 🟢 Primeiro plugin de domínio `domains/trabalho/` pelo contrato `ModuloDominio` (Open/Closed).
- [x] 🟢 Orquestração **Dagster Degrau 1** (schedules mensais) por fonte — ADR-0006.
- [x] 🟢 Métrica `supressao_total{indicador}`.
- [x] 🔵 `frescor_dias{fonte}` populado pela ingestão (dias desde o período mais recente) — `pipeline.py`.
- [x] 🔵 **Contratos de dados formais** por fonte (CAGED/ESTBAN): colunas obrigatórias validadas na
  **borda bronze** (`extrair`), falha clara se o layout mudar — ADR-0017. *(IBGE/JSON: próximo passo.)*
- [x] 🟡 **Metodologia e pesos do IVM** — **decidido (ADR-0018):** manter **v1** (min-max + 50/50,
  robusto com poucos municípios; o IVM é MV recomputada, não há série a preservar). O **z-score é a
  v2**, adiada até cobertura nacional (com guarda de `stddev=0`, reescala 0–100, gatilho na Onda 2).

**Produtos entregues** (sobre CAGED/IBGE/BCB):
- [x] 🟢 **TRANSP-01 IVM básico** (view materializada O(1)) — ADR-0008; `/v1/ivm`.
- [ ] 🔵 **TRAB-01 Pulso Produtivo** — empacotar o produto/endpoint nomeado (dado já no ar via `/v1/valores`).
- [ ] 🔵 TRAB-03 Giro Local (CAGED+IBGE+ESTBAN); TRAB-02 Salário Radar; TRAB-04 Região Emprega.

**Frontend (design system):**
- [x] 🟢 App `web/` Next.js: **mapa semafórico do IVM** + drill-down — ADR-0009/0010.
- [x] 🟡 **Tokens/componentes do design system** (WCAG) — tokens centralizados (`lib/semaforo.ts`:
  `ESTADOS`, `CORES`, `COR_SEM_DADO`; CSS vars em `globals.css`), componente `Legenda` reutilizável,
  semáforo acessível (cor redundante com texto + `sr-only` + `:focus-visible`; coropleta com
  `role=img`/`<title>`). Default aplicado: DS mínimo neutro, não comunica só por cor.

**Critério de saída:** ingestão reexecutável/idempotente; IVM no ar com proveniência; mapa navegável;
cobertura mantida (100% supressão/IVM). **Núcleo ✅; resta produtos TRAB e contratos formais.**

---

## ONDA 2 — Camada cívica de alto valor + open-core profundo  (Tração)

**Objetivo:** abrir os produtos de maior impacto, ligar as fontes de ETL médio/pesado, e ativar a
monetização (camada profunda) e a camada de cidadão. **Sequenciar por desbloqueio de fonte.**

### 2A. Fontes de ETL médio + transparência
**Fontes:** DataJud, INEP (anual), Portal da Transparência, SICONFI/STN, PNCP/COMPRASNET, OSM, INMET/INPE/OpenAQ.
- [ ] 🔵 Adaptadores + contratos dessas fontes; **Dagster Degrau 2** (assets c/ linhagem) e **Degrau 3**
  (sensors por chegada de arquivo, partições por período/domínio).
- [ ] 🔵 EDU-01 Bússola Educação-Trabalho (INEP+CAGED+IBGE); EDU-02 Radar de Evasão.
- [ ] 🔵 TRANSP-06 OndeFoi (SICONFI); TRANSP-03 Fornecedor Transparente (PNCP+Receita+DataJud);
  TRANSP-05 ObraViva (PNCP/SIOP/SIAFI+CAGED+OSM).
- [ ] 🟢 IVM **completo** (incorpora saúde/educação/transparência; nova `versao_metodologia`, série
  antiga preservada).

### 2B. Fontes de saúde (ETL pesado — DATASUS)
**Fontes:** DATASUS SIA/SIH/CNES/SINAN/SINASC/SIM (PySUS/FTP DBC), INSS, BPS; clima (INMET/INPE).
- [ ] 🔵 Adaptador DATASUS robusto (DBC→Parquet, incremental, idempotente) — o de maior atrito.
- [ ] 🔵 SAUDE-04 Fila Visível; SAUDE-06 Receita Cidadã; SAUDE-05 Navegador de Acesso.
- [ ] 🔵 SAUDE-01 Sentinela Respiratória; SAUDE-02 Caçador de Arboviroses; SAUDE-03 Materno-Infantil;
  SAUDE-11 Burnout. *(`saude.resp.internacoes_j` já está no seed como exemplo de origem sensível.)*

### 2C. Saneamento, água, energia, alimentação
**Fontes:** ANA/HidroWeb, SNIS, ANEEL (DEC/FEC), IBGE PAM, CEPEA/CONAB, SICAR/MapBiomas.
- [ ] 🔵 SANE-01 AguaViva; SANE-02 Rio em Risco; SANE-03 Esgoto Invisível; SANE-04 Luz no Mapa.
- [ ] 🔵 ALIM-01 Prato no Frio; ALIM-02 Fome Oculta; ALIM-05 Semeando Transparência.

### 2D. Open-core profundo + cidadão + IA (capacidades transversais)
- [ ] 🟢 **Camada profunda paga:** `/v1/consultas-lote` e endpoints premium autenticados; roteamento
  de tier no gateway (público grátis rate-limited × profundo autenticado/cobrado).
- [ ] 🟢 **Autenticação do cidadão (OIDC):** OIDC → JWT curto → cookie HttpOnly/Secure/SameSite →
  refresh. Hoje há **login v1** (JWT em cookie HttpOnly, ADR-0012); falta o OIDC real. 🟡 provedor.
- [x] 🟢 **Serviço de consentimento (runtime):** escrita em `app`, cifragem de campo (+ **anel de
  chaves**), trilha de auditoria, `/v1/alertas` (assinar/listar/revogar) + `/v1/eu` + consumo de
  alertas (`/v1/notificacoes`) — ADRs 0012, 0014, 0016.
- [x] 🟢 **IA ancorada (RAG):** recuperação sobre o repositório canônico, citação por afirmação,
  guardrails (sanitização, abstenção, **ancoragem numérica**), sem credencial do `app` — ADR-0011/0015.
- [x] 🟡 **Provedor de LLM** — **resolvido:** DeepSeek **ou** Ollama via API OpenAI-compatível (config) — ADR-0015.

**Dupla face (obrigatória):** ao construir produtos de risco alto/médio, implemente a mitigação do
§17 como requisito — SAUDE-01 (veda seguradora), SAUDE-02 (geo ~500 m), TRANSP-02/05 (revisão humana),
EDU-02 (agregado por município).
- [ ] 🟡 **Conselho de Privacy-by-Design** (Defensoria/ONGs) p/ produtos de acesso restrito (HAB-04, DIR-01).

**Infra / gatilhos (provavelmente disparam aqui):**
- [ ] 🔵 Avaliar gatilhos §1.1: Postgres→gerenciado (>60 GB ou p95>300 ms), MinIO→S3 (>200 GB),
  observabilidade externalizada (agente leve, retenção curta).
- [ ] 🔵 Deploy **canário + rollback automático**; WAF (OWASP CRS) e ACME/TLS (domínio real). 🟡 domínio.

**Critério de saída:** ≥1 produto cívico de cada bloco no ar com sua mitigação; camada profunda
monetizável; cidadão assina alerta com consentimento isolado e auditado; IA só com citação.

---

## ONDA 3 — Escala multiproduto + extração de serviços  (Escala)

**Objetivo:** completar o catálogo, extrair serviços por dor, capacidades analíticas avançadas,
operação multi-cliente B2G.

- [ ] 🔵 Habitação: HAB-01 Alerta de Despejo, HAB-02, HAB-03 Escudo Antigentrificação, HAB-04 Risco
  Moradia-Clima, HAB-05 (com mitigação de dupla face onde marcada).
- [ ] 🔵 Justiça/Direitos/Crédito: JUST-01, DIR-01 (via Defensoria, zero PII), CRED-01 (só índice agregado).
- [ ] 🔵 Mobilidade (MOB-01), Meio Ambiente (AMB-01/02), Alimentação (ALIM-03/04), Transparência
  (TRANSP-04/07), e os produtos score-4 de Saúde/Educação/Saneamento.
- [ ] 🔵 **TRANSP-02 Farol de Conluio** — requer **capacidade de grafo** (sócios cruzados via Receita/CNPJ).
- [ ] 🔵 Analytics inferencial (correção de comparações múltiplas/FDR, regressão com diagnósticos) e
  produtos preditivos ("o conhecimento mora no lag").
- [ ] 🔵 **Extração de serviços** ao bater o gatilho §1.1: candidatos = alertas, API profunda, IA,
  grafo. Sempre pela fronteira do plugin.
- [ ] 🔵 Migração de compute gerenciado→K8s só se >3 réplicas; broker durável (Kafka) se >5.000
  eventos/min; OLAP dedicado (ClickHouse) se consulta recorrente >5 s.
- [ ] 🔵 Runbooks completos (incidentes, depreciação, multi-serviço); SLAs/alertas de frescor por
  ativo (Dagster Degrau 4, backfills gerenciados).
- [ ] 🟡 Ordem fina dos produtos (comitê trimestral) · metas de north star · foco de canal/parcerias B2G.

**Critério de saída:** catálogo coberto nos domínios priorizados; serviços extraídos com seus próprios
pipelines de qualidade; plataforma multi-cliente madura; custo sob controle pelos gatilhos.

---

## Trilhas transversais (contínuas, todas as ondas)

- **Qualidade & evolução:** quality gate sempre verde; expand-and-contract; testes de contrato/regressão;
  cobertura ponderada por risco; código morto deletado; dívida como issue.
- **Segurança & LGPD:** defesa em profundidade (gateway + recheck no serviço); base legal por DMN;
  minimização; direitos do titular (revogação/eliminação no `app`); auditoria de acesso ao `app`.
- **Observabilidade:** logs/métricas/traces correlacionados por `trace_id`, sem PII; métricas de domínio.
- **Docs-as-code:** OpenAPI gerado; ADR por decisão; este roadmap atualizado a cada item fechado.
- **Dupla face:** registro §17 honrado produto a produto; produto novo não listado = risco médio até revisão.
- **Economia de recurso:** caminhos quentes pré-computados/cacheados; ingestão incremental; medir antes de otimizar.

---

## Registro consolidado de decisões 🟡 (para o dono)

| # | Decisão | Onde entra | Status / default proposto |
|---|---|---|---|
| 1 | Metodologia/pesos do IVM | Onda 1 | v1 (min-max 50/50) entregue; calibrar p/ z-score quando houver dado |
| 2 | Tokens/componentes do design system | Onda 1 | componentes prontos; tokenizar + WCAG (DS mínimo neutro, semáforo acessível) |
| 3 | Provedor de LLM, chave, orçamento | Onda 2D | **resolvido:** DeepSeek/Ollama (config) — ADR-0015 |
| 4 | Conselho PbD com Defensoria/ONGs | Onda 2D | criar antes dos produtos de acesso restrito (HAB-04, DIR-01) |
| 5 | Ordem fina de produtos por onda | Ondas 2–3 | seguir valor de produto dentro do que a fonte já desbloqueou |
| 6 | Metas de north star | Onda 3 | direcionais; calibrar com dado real |
| 7 | Foco de canal/parcerias B2G | Onda 3 | priorizar transparência/saneamento (pull legal) |
| 8 | Alvo de VPS/nuvem, domínio, TLS | Onda 2 (gatilho) | Traefik dev até existir domínio; migrar por gatilho §1.1 |
| 9 | Stack de frontend | Onda 1 | **resolvido:** Next.js — ADR-0009 |

---

## Mapa de dependências (visão macro)

```mermaid
flowchart TB
  O0[Onda 0: Fundacao + API leitura - COMPLETA] --> O1[Onda 1: Backbone IBGE/CAGED/BCB + IVM basico]
  O1 --> O2A[2A: ETL medio + transparencia]
  O1 --> O2B[2B: DATASUS / saude]
  O1 --> O2C[2C: saneamento/energia/alimentacao]
  O2A --> O2D[2D: open-core profundo + cidadao + IA - parcial]
  O2B --> O2D
  O2C --> O2D
  O2D --> O3[Onda 3: escala multiproduto + extracao de servicos]
  O0 -. anel de chaves OK .-> O2D
```

## Definition of Done por onda (resumo)

Toda onda só fecha com: testes verdes (supressão/cálculo a 100%), SAST/estática limpos, sem mudança
destrutiva, isolamento de PII verificado, proveniência em tudo, IA (se tocada) só com citação e sem
acesso ao `app`, observabilidade da nova rota, OpenAPI/ADR atualizados, caminhos quentes
cacheados/pré-computados, e — para cada produto — a mitigação de dupla face do §17 implementada.
