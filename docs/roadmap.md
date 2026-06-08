# DadoSabedoria — Roadmap de Ondas de Desenvolvimento

Plano completo das ondas de desenvolvimento, do estado atual até a escala multiproduto. **Fonte
única do plano** (vive no repo, sobrevive a resets do contêiner). Serve para o desenvolvimento
**autônomo**: leia de cima para baixo, execute o próximo item aberto `[ ]`, e **pare apenas nas
decisões marcadas 🟡** (decisões de produto do dono). Fluxo de cada fatia: branch ← `origin/main` →
implementar com teste → push → PR → **CI verde** → merge → marcar `[x]` aqui → próximo item.

> **FIM DE SESSÃO — MODO DEV (2026-06-07/08): estado = VERDE.** Autonomia ampliada exercida: **24 PRs
> abertos, CI verde e mergeados sozinho** (#55–#77; +#78 **"Fontes & confiança"**). **#5 exercido
> ("priorizar um produto" + "siga"):** `/comparar` (ADR-0030, dois municípios lado a lado, sem novo
> contrato, descritivo, supressão honesta) **e** `/fontes` + `GET /v1/fontes` (ADR-0031) — a
> **proveniência consolidada** (órgão/licença/cadência/lag/base legal LGPD + cobertura por domínio,
> lida do acervo) com o modelo de privacidade ao lado: a confiança como **fato verificável**, aditivo
> ao contrato, sem JS, na porta de entrada. Ambos escalam sozinhos com mais dado.
> O selo de confiança vive também nas listas `/ivm` e `/onde-foi`. **Handoff de design reconciliado por completo** — a
> **superfície de agir** cobre **OndeFoi (#68) e IVM (#70)** (primitivo `lib/agir.ts` + estilos
> `.acoes`); a **lista/índice `/onde-foi`** (#72) fechou a navegação com mitigação de dupla-face
> (ordenada por nome, aviso "ilustrativo"); e o drill-down do IVM ganhou **leitura humana** (#73:
> significado do semáforo + tendência da série). Os âncora têm o **funil completo**
> (entender→comparar→agir→confiar). **Backlog ungated de PRODUTO esgotado:** o que resta é **TUDO gate
> do dono** (hosts 403, referendo do OndeFoi, OIDC/domínio/LLM/DataJud/PbD). Entregue:
> 1. **#0 das fontes abertas validado** (ADR-0028): SICONFI ✅ + IBGE ✅ contra dado real; forma-verdade
>    gravada, fixtures fiéis-à-forma, bugs de forma do `financas` corrigidos.
> 2. **OndeFoi re-ancorado em Liquidado÷Empenhado** (ADR-0029 — default MODO DEV, pois "recebido por
>    função" não existe na fonte): **esteira viva COMPLETA** (Anexo I-E → fato `execucao_funcao`/mig.
>    0017 → `executar_siconfi_funcoes` → `run_siconfi_funcoes` + **Dagster**) **+ produto re-ancorado
>    ponta-a-ponta** (contrato/API `empenhado*`/`liquidado`, tela e copy) — ainda **grau-demo**.
> 3. **Gate axe/WCAG consertado** (era **falso-verde** — nunca rodava): agora roda, achou e **corrigi** a
>    única violação (contraste de `.tendencia`) e o gate **BLOQUEIA** serious/critical + "axe não rodou".
> 4. **Telas do IVM reconciliadas — 4/4** (primitivos compartilhados, sem forkar): `SeloConfianca`
>    reutilizado (`MetaIVM` com fontes+frescor), **busca** server-side, **"o que é IVM"** (explicador) e
>    **comparar cidade parecida** (`/v1/ivm/{ibge}/similares`).
> 5. **Superfície de agir (OndeFoi #68 + IVM)** — `AcoesOndeFoi`/`AcoesIVM`, `<details>` sem JS, sobre
>    o primitivo compartilhado `lib/agir.ts` (+ estilos `.acoes` neutros, renomeados de `of-` sem
>    forkar): compartilhar, exportar com citação **ABNT** (proveniência embutida), avise-me
>    (LGPD-por-desenho, prepara o lugar p/ a auth do cidadão) e a-quem-cobrar/levar (Fala.BR/CGU real).
>    Copy honesta por produto (execução≠serviço; IVM comparativo≠veredito); gates degradando.
>
> **O que resta é TUDO gate do dono:** **(a)** OndeFoi **go-live** — endpoint
> lendo a fato `execucao_funcao` (🟡 referenda a ancoragem Liquidado/Empenhado; PENDENCIAS §B); **(b)**
> **allowlist** dos hosts ainda 403 (INEP/PNCP/DATASUS/CAGED + ESTBAN) p/ tornar vivos os conectores;
> **(c)** OIDC/domínio/LLM/DataJud/PbD (PENDENCIAS §C). _Sem flake real: o `integration`/`screenshot`
> às vezes falha por timeout do Docker Hub — mesmo SHA passa no run paralelo; mergeado só no verde._
> **Bloqueios humanos** (Lista de desbloqueio): allowlist INEP/PNCP/DATASUS/CAGED(`ftp.mtps.gov.br`) +
> ESTBAN(`www.bcb.gov.br`/`dadosabertos.bcb.gov.br`).
> _Pausa, não bloqueio — tudo verde._

## Como usar (legenda)

- `[ ]` item executável; `[x]` concluído.
- **Camadas de autoridade** (honestidade sobre a origem de cada item):
  - **🟢 Definido** — vem do briefing / documento técnico / esquema. Executar sem perguntar.
  - **🔵 Backlog implícito** — decorre dos invariantes e ADRs; executável sem perguntar.
  - **🟡 Decisão de produto** — escolha do dono (§10 do briefing). Ver **Política de autonomia**.
- Cada onda termina num **critério de saída** com a mesma régua de qualidade.

## Política de autonomia (pré-autorização do dono — 2026-06-06)

O dono **pré-autorizou** os 🟡 "seguros" (reversíveis/direcionais): o agente segue o *default* sem
parar. Só os **🔴 gates externos** (dependem de conta/chave/domínio/pessoa de fora) param — e mesmo
esses seguem a regra **adiar-e-seguir**: adia SÓ aquele item, constrói tudo ao redor, e acumula o
pendente na **Lista de desbloqueio** abaixo. O agente **nunca fica ocioso** esperando um gate.

**PIVÔ (2026-06-06) — da "prontidão de fonte" para "valor de produto até a TELA".** O backbone já
basta (financas/educacao/compras/saude no ar pelo `ModuloDominio`; 5+ domínios). **Pare de adicionar
fonte nova**; feche o ciclo ponta-a-ponta: **(1) IVM completo → (2) mapa semafórico (1ª tela) →
(3) puxar produtos por valor (#5)**, cada um como fatia vertical **até a tela**, com a dupla-face do
§17. Fonte nova só quando um produto priorizado exigir. Os únicos pontos que param seguem os 5 🔴.

**🟢 Pré-autorizados (seguir o default, não perguntar):**
- **#1 Metodologia do IVM** — min-max v1 agora; **z-score = v2** no *IVM completo* (multidomínio +
  cobertura nacional), versionado (ADR-0018). _(decidido)_
- **#2 Design system** — DS mínimo acessível (WCAG); feito (#16). _(decidido)_
- **#5 Ordem de produtos** — valor de produto **dentro** do que a fonte já desbloqueou.
- **#6 Metas north-star** — direcionais; não enshrine; calibrar com dado real.
- **#7 Canal/parcerias** — priorizar transparência/saneamento (pull legal B2G).
- **#8 TLS/gateway** — Traefik em **dev-mode** até existir domínio (vira 🔴 só em produção).

**🔴 Gates externos (HARD STOP do item — adiar-e-seguir + Lista de desbloqueio):**
1. **Provedor/chave de LLM** (DeepSeek key + orçamento; Ollama local dispensa) — gate da IA real.
2. **IdP/OIDC do cidadão** (provedor + client credentials) — gate da auth real do cidadão.
3. **Domínio + TLS/ACME de produção** — gate ao sair do dev-mode.
4. **Credenciais de fontes restritas** (ex.: DataJud) — gate só dessas fontes; as abertas seguem.
5. **Conselho PbD (Defensoria/ONGs)** — **não** é gate de código: bloqueia só **HAB-04 e DIR-01**;
   o resto é construído e esses dois ficam adiados/sinalizados.

## Lista de desbloqueio (gates externos pendentes — para o dono resolver em bloco)

_O agente acrescenta aqui ao bater num 🔴 e segue construindo o resto. Análise detalhada (o que é · o
que fazer · o que destrava · impacto · prioridade) dos gates conhecidos: **`docs/PENDENCIAS_DO_DONO.md`**
— a fila de análise do dono no checkpoint de 36h (revisar junto com esta lista)._
- [ ] **LLM real:** `LLM_BASE_URL`/`LLM_MODEL`/`LLM_API_KEY` (DeepSeek) ou subir Ollama. _(IA roda em
  template até lá — degradação graciosa, ADR-0015.)_
- [ ] **OIDC:** provedor (gov.br/Keycloak) + client id/secret. _(login v1 por JWT segue até lá.)_
- [ ] **Domínio + `ACME_EMAIL`:** para TLS de produção no Traefik. _(dev-mode até lá.)_
- [ ] **DataJud (e outras fontes com auth):** credencial/chave. _(fontes abertas seguem sem isso.)_
- [~] **Allowlist dos conectores vivos (lote, a adicionar em bloco no #0):** os conectores foram
  construídos "vivo-pronto" (esteira + schedule + fixture), mas a 1ª busca real só roda com o host
  liberado. **#0 parcialmente aberto (sondado 2026-06-07, sessão nova):**
  - ✅ **SICONFI** `apidatalake.tesouro.gov.br` (200) — **VALIDADO** (forma real gravada, ADR-0028;
    fixture promovida a **fiel-à-forma**).
  - ✅ **IBGE** `servicodados.ibge.gov.br` (aberto) — **VALIDADO** no #0: `localidades/municipios`
    (5571) + `v3/malhas` casam o `AdaptadorIbge`; fixture já fiel-à-forma, **sem mudança de código**.
  - ⚠️ **ESTBAN/BCB** — `www4.bcb.gov.br` aberto mas a URL antiga dá **404**: o BCB migrou o portal
    para `www.bcb.gov.br` / `dadosabertos.bcb.gov.br`, **ambos 403** no ambiente. _(Dono: liberar um
    desses hosts no allowlist — virou **gate de host**, não "achar a URL". Sondei o portal, 2026-06-07.)_
  - ❌ **CAGED** `ftp.mtps.gov.br` (FTP do MTPS) — **403**: host **fora** do allowlist (que tem BCB,
    não MTPS). _(Dono: adicionar `ftp.mtps.gov.br`.)_
  - ❌ ainda **bloqueados** (403 `host_not_allowed`): **INEP** `download.inep.gov.br` · **PNCP**
    `pncp.gov.br` · **DATASUS** `ftp.datasus.gov.br`. _(Dono: adicionar ao allowlist Custom; cada um
    traz a marca "confirmar na 1ª busca real" — a forma vem da fonte, não do mock.)_
- [~] **🟡 OndeFoi — re-ancoragem do número (a referendar; ADR-0028 §5 + ADR-0029):** o #0 mostrou que
  **"recebido por função" NÃO existe na fonte** (transferências [I-C] não são classificadas por
  função; só as despesas [I-E] têm função, nas colunas Empenhado→Liquidado→Pago). **Em MODO DEV o dev
  segue no default** (source-grounded): **Liquidado÷Empenhado por função** ("empenhar≠liquidar"). A
  camada pura (`onde_foi.calcular`) e a honestidade ficam; muda o significado das colunas e a
  pergunta-título. **Fiz:** forma/vocabulário presos (#0/ADR-0028) **+ esteira VIVA completa**
  (ADR-0029: fato `execucao_funcao`/migração 0017, `executar_siconfi_funcoes`, `run_siconfi_funcoes`,
  Dagster `job_siconfi_funcoes`+`schedule_siconfi_funcoes_anual`). **Tela segue grau-demo** até o dono
  referendar. _(Falta dono: referendar a moldura → então endpoint/tela demo→vivo.)_
- [x] **🟡 OndeFoi — lista/índice `/onde-foi` (handoff `OFLista`): FEITO com mitigação de dupla-face.**
  Pré-autorização dos 🟡 seguros → segui o default **com a mitigação no design** (§17, nunca retrofit),
  em vez de adiar: endpoint `GET /v1/onde-foi` + tela `/onde-foi` (busca server-side, sem JS). A
  dupla-face de rankear **grau-demo** mora no design: **ordenado por NOME (não por %)** — sem
  leaderboard de número provisório — **+ aviso forte "ilustrativo, não reflete gestão real"**; a
  ExecPill já enquadra "merece a pergunta, não veredito". Home re-ancorada (copy Liquidado÷Empenhado,
  link à lista). **Reversível:** quando o dado for real (host SICONFI), a lista pode ordenar por % e
  o aviso cai — _🟡 do dono só se quiser ordenar por execução já no grau-demo (default meu = por nome)._
- [ ] **Conselho PbD:** constituir com Defensoria/ONGs antes de **HAB-04** e **DIR-01**.
- [x] **Handoff de design (arquivos): RESOLVIDO** — o dono commitou o protótipo no repo
  (`docs/design/`, durável, sobrevive a reset). **Reconciliação em curso** (telas ↔ handoff, nos
  primitivos compartilhados, sem forkar): OndeFoi **enquadramento honesto** (donut + enquadra +
  callout + trilha + "o que é execução") **e o selo de confiança** (`SeloConfianca` compartilhado,
  `<details>` acessível; meta enriquecida com fonte rica + licença) — feitos. OndeFoi
  **superfície de agir COMPLETA** ✅ (`AcoesOndeFoi`, `<details>` nativos sem JS no cliente):
  **compartilhar** (texto cívico honesto + WhatsApp/e-mail + link canônico), **exportar com citação
  ABNT** (proveniência embutida + ponteiro à API `/v1`), **avise-me** (prepara o lugar + nota
  LGPD-por-desenho — a auth do cidadão é gate do dono) e **a quem cobrar** (Fala.BR/CGU real + busca
  da ouvidoria local, foco no território, nunca em pessoas) — `lib/agir.ts` com testes; gates
  degradando honestamente. IVM — **reconciliação COMPLETA**: ✅ `SeloConfianca` reutilizado no drill-down (`MetaIVM` com
  `fontes` [CAGED/ESTBAN/SIH] + frescor + licença, sem forkar); ✅ **busca** de município (server-side
  `?q=`, sem JS); ✅ **"o que é IVM"** (explicador `<details>`); ✅ **comparar cidade parecida
  LADO A LADO** (endpoint `/v1/ivm/{ibge}/similares` = mesma UF, IVM mais próximo; subíndices
  side-by-side com picker `?compara=` sem JS — revela ONDE duas cidades parecidas diferem); ✅
  **superfície de agir** (`AcoesIVM` reusa `lib/agir.ts` + estilos `.acoes` neutros — primitivo
  compartilhado com o OndeFoi, sem forkar: compartilhar/exportar-ABNT/avise-me/a-quem-levar, copy
  honesta "comparativo, não veredito", gates degradando); ✅ **leitura humana** do drill-down
  (`lib/ivm-leitura.ts`, pura/testada): **significado do semáforo** ("entre as mais vulneráveis — há
  razão para cobrar prioridade, não sentença") + **tendência da série** (subir = piora) — o "so what"
  do handoff `TelaDrill`, sem JS. _Default
  "parecida" = mesma UF + IVM mais próximo, no exercício; reversível se o dono preferir outro._ **axe/WCAG no DOM vivo** do screenshot: ✅ **RESOLVIDO
  (2026-06-07)** — (1) o axe **nunca rodava** (falso-verde): `captura.mjs` usava `browser.newPage()`,
  rejeitado pelo `@axe-core/playwright` → auditoria pulada em silêncio; corrigido com
  `browser.newContext()`. (2) A 1ª rodada real acusou **1 violação** (`color-contrast` em `.tendencia`
  do Pulso: verde #16a34a=3.15:1, vermelho #dc2626=4.62:1); corrigida (#15803d=4.79:1, #b91c1c=6.18:1;
  a seta+rótulo já garantem que não é só cor). (3) Gate **apertado para BLOQUEAR** serious/critical
  **e** "axe não rodou" (anti-falso-verde). As outras 6 telas já passavam limpas.

## Estado atual (reconciliação — 2026-06-06)

24 PRs mergeados; ADRs 0001–0025. **Adiantado** em capacidades transversais em relação à sequência
do briefing: o consentimento (runtime + ciclo LGPD + **anel de chaves**), a **IA ancorada** (RAG +
guardrails + **provedor de LLM** DeepSeek/Ollama) e os **runbooks** (backup/restore com PII separada,
rotação) já estão entregues — eles aparecem na Onda 2D/Onda 0 e estão marcados `[x]` abaixo. **Falta
largura**: mais domínios/produtos (Ondas 2–3) e as fontes de ETL médio/pesado.

- **Onda 0 (Fundação): COMPLETA** ✅ — ADRs 0001–0005, 0013, 0016.
- **Onda 1 (Backbone + IVM básico): essencialmente completa** — ADRs 0006–0010, 0017, 0018;
  contratos de dados + frescor + calibrações 🟡 (IVM, design tokens) resolvidos; só faltam os
  **produtos TRAB extra** (precisam de definição de produto/fonte).
- **Onda 2D (cidadão + IA + open-core): parcial** — consentimento/IA/LLM + **camada profunda paga
  com chaves por cliente** `[x]` (ADRs 0011–0020); falta **OIDC real** (🔴 gate) e cotas/billing.
- **Onda 2A/2B (novos domínios): em andamento** — `financas` (SICONFI), `educacao` (INEP), `compras`
  (PNCP) e `saude` (DATASUS/SIH — 1ª fonte sensível) no ar pelo `ModuloDominio`; 2C a abrir.
  Sequência por prontidão de fonte: **SICONFI → INEP → PNCP → DATASUS …** (decisão do dono).

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
- [x] 🟢 **TRANSP-01 IVM completo (multidomínio)** — soma o subíndice de **saúde** (SIH) a
  emprego+finanças, peso dinâmico (saúde opcional, respeita supressão), `versao_metodologia=v1.1`;
  min-max mantido (z-score = v2 ao atingir cobertura nacional) — ADR-0025; migração 0015.
- [x] 🔵 **TRAB-01 Pulso Produtivo** — endpoint `/v1/pulso-produtivo/{ibge}` sobre o saldo CAGED
  **real** (mesmo Repository de `/v1/valores`): nível = a batida do mês, momento = mês vs anterior,
  janela como contexto explícito. Honesto: emprego **formal**, fluxo volátil que "merece a pergunta",
  **sem cadeado** (n_minimo=0). **Tela** `/pulso/{ibge}` (pivô "até a tela"): selo de nível +
  tendência + série mês-a-mês a partir do **zero** (sinal explícito) + a nota honesta; acessível
  (cor nunca sozinha, ADR-0009) e **certificada no screenshot de CI**; cross-link do drill-down do IVM.
- [ ] 🔵 TRAB-03 Giro Local (CAGED+IBGE+ESTBAN); TRAB-02 Salário Radar; TRAB-04 Região Emprega.

**Frontend (design system):**
- [x] 🟢 App `web/` Next.js: **mapa semafórico do IVM** + drill-down — ADR-0009/0010.
- [x] 🔵 **Porta de entrada dos produtos** (`/`): cada produto como uma PERGUNTA com sua tela —
  IVM, Pulso Produtivo (TRAB-01) e OndeFoi (TRANSP-06, grau-demo); navegação no topo; o pitch de
  confiança (privacidade/proveniência/qualidade). Acessível, DS atual (ADR-0009).
- [x] 🔵 **Panorama do município** (`/municipio/{ibge}` ← `GET /v1/territorios/{ibge}/panorama`):
  o último valor de **cada** indicador público do acervo (todos os domínios, não só os do IVM), com
  proveniência por fonte; a célula suprimida vira **protegido** (reusa `EstadoSupressao`). Uma
  consulta sem N+1 (DISTINCT ON). Cross-link do drill-down do IVM e da porta de entrada.
- [x] 🔵 **IA ancorada à tela** (`/perguntar` ← `POST /v1/ia/perguntar`): dá rosto ao diferencial
  (ADR-0011/0015) — exemplos navegáveis (server-side, sem JS no cliente) mostram a resposta **com
  citação** + ressalvas, o selo do **narrador** (template sem chave de LLM — degradação graciosa,
  honesta) e a **abstenção** quando a pergunta sai do acervo (não inventa). Certificada no screenshot.
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
- [x] 🔵 **SICONFI/STN — domínio `financas`** (1ª fonte 2A, ADR-0021): `AdaptadorSiconfi` + contrato
  na borda bronze + `ModuloFinancas` (plugin) + indicador `financas.transferencias.correntes`
  semeado pelo caminho ouro e **servido pela API genérica**. **OndeFoi (TRANSP-06)** entregue
  ponta-a-ponta em **grau-demo**: contrato (ADR-0026) → endpoint `/v1/onde-foi/{ibge}` → **tela**
  `/onde-foi/{ibge}` (recebido×executado por função, banda de atenção, `EstadoSupressao` reusado p/
  "sem cobertura", honestidade "executar≠entregar"; screenshot de CI). **#0 VALIDADO (2026-06-07,
  ADR-0028):** forma real do DCA confirmada (campos `cod_ibge` int/`valor` num/dimensão `coluna`),
  **vocabulário de função promovido da fonte** (Portaria 42, Anexo I-E), `exe_estado` válido =
  `{valor, sem_cobertura}` (sem `suprimido`); fixture **fiel-à-forma**; bugs de forma do indicador
  `financas` corrigidos (filtro por `cod_conta`+`coluna`). _Falta: esteira viva de **despesa por
  função** (Anexo I-E → função como dimensão → `run_siconfi`/Dagster, paginação nacional) e o **🟡
  do dono** (re-ancoragem recebido→empenhado, ADR-0028 §5) p/ migrar a tela demo→vivo; subíndice IVM._
- [x] 🔵 **INEP/Censo Escolar — domínio `educacao`** (2ª fonte 2A, ADR-0022): `AdaptadorInep` (CSV
  latin-1 via `utf8-lossy`) + contrato na borda bronze + `ModuloEducacao` (plugin) + indicador
  `educacao.matriculas.fundamental` semeado pelo caminho ouro e **servido pela API genérica**.
  **Pipeline VIVO-PRONTO:** `executar_inep` (bronze→prata→ouro + linhagem) + `run_inep` (CLI) +
  **Dagster** (`job_inep` + `schedule_inep_anual`); fetcher real exercitado no CI por fake (fixture
  fiel-ao-contrato) — **forma a confirmar na 1ª busca real** (#0, host `download.inep.gov.br`).
  _Falta: dado real (#0), produtos EDU-01/EDU-02 (telas)._
- [x] 🔵 **PNCP/Contratações — domínio `compras`** (3ª fonte 2A, ADR-0023): `AdaptadorPncp` (JSON
  aninhado/Struct: `unidadeOrgao.codigoIbge`) + contrato na borda bronze + `ModuloCompras` (plugin) +
  indicador `compras.contratos.valor_total` semeado pelo caminho ouro e **servido pela API genérica**.
  **Pipeline VIVO-PRONTO:** `executar_pncp` + `run_pncp` + **Dagster** (`job_pncp` + `schedule_pncp_anual`);
  fetcher real exercitado no CI por fake — **forma a confirmar na 1ª busca real** (#0, host `pncp.gov.br`).
  _Falta: dado real (#0), produtos TRANSP-03/05 (telas, dupla face §17)._
- [ ] 🔵 Demais adaptadores 2A (DATASUS → …) + contratos; **Dagster Degrau 2** (assets c/ linhagem)
  e **Degrau 3** (sensors por chegada de arquivo, partições por período/domínio).
- [ ] 🔵 EDU-01 Bússola Educação-Trabalho (INEP+CAGED+IBGE); EDU-02 Radar de Evasão.
- [ ] 🔵 TRANSP-06 OndeFoi (SICONFI) — **tela no ar em grau-demo** (ver 2A acima); falta só o dado
  vivo (#0) para fechar. TRANSP-03 Fornecedor Transparente (PNCP+Receita+DataJud); TRANSP-05
  ObraViva (PNCP/SIOP/SIAFI+CAGED+OSM).
- [x] 🟢 IVM **completo** (multidomínio) — incorpora o subíndice de **saúde** (SIH) a emprego+finanças
  (`versao_metodologia=v1.1`, min-max; z-score=v2 ao atingir cobertura nacional) — ADR-0025. Os
  indicadores **neutros** (matrículas, transferências, contratos) seguem descritivos (fora do índice
  de vulnerabilidade) até existir recorte direcional/per capita.

### 2B. Fontes de saúde (ETL pesado — DATASUS)
**Fontes:** DATASUS SIA/SIH/CNES/SINAN/SINASC/SIM (PySUS/FTP DBC), INSS, BPS; clima (INMET/INPE).
- [x] 🔵 **DATASUS/SIH — domínio `saude`** (1ª fonte sensível, ADR-0024): `AdaptadorDatasus` (conta
  AIH do grupo J por município = `n_amostra`) + contrato na borda bronze + `ModuloSaude` alimentando
  `saude.resp.internacoes_j` pelo caminho ouro (k-anon). **Pipeline VIVO-PRONTO:** `executar_datasus`
  (a contagem É o `n_amostra` → **k-anon suprime ANTES de gravar** contagens <5; teste prova SP=3 e
  Campinas=2 protegidas) + `run_datasus` + **Dagster** (`job_datasus` + `schedule_datasus_mensal`,
  com `refrescar_ivm` — saúde é subíndice do IVM). _Falta: dado real (#0, `ftp.datasus.gov.br`),
  DBC→Parquet robusto, produtos SAUDE com dupla face §17._
- [ ] 🔵 Adaptador DATASUS **robusto** (DBC→Parquet, incremental/idempotente, mapa IBGE 6→7) +
  Dagster; demais sistemas (SIA/CNES/SINAN/SINASC/SIM) — o de maior atrito.
- [ ] 🔵 SAUDE-04 Fila Visível; SAUDE-06 Receita Cidadã; SAUDE-05 Navegador de Acesso.
- [ ] 🔵 SAUDE-01 Sentinela Respiratória; SAUDE-02 Caçador de Arboviroses; SAUDE-03 Materno-Infantil;
  SAUDE-11 Burnout. *(`saude.resp.internacoes_j` já está no seed como exemplo de origem sensível.)*

### 2C. Saneamento, água, energia, alimentação
**Fontes:** ANA/HidroWeb, SNIS, ANEEL (DEC/FEC), IBGE PAM, CEPEA/CONAB, SICAR/MapBiomas.
- [ ] 🔵 SANE-01 AguaViva; SANE-02 Rio em Risco; SANE-03 Esgoto Invisível; SANE-04 Luz no Mapa.
- [ ] 🔵 ALIM-01 Prato no Frio; ALIM-02 Fome Oculta; ALIM-05 Semeando Transparência.

### 2D. Open-core profundo + cidadão + IA (capacidades transversais)
- [x] 🟢 **Camada profunda paga:** `POST /v1/consultas-lote` (lote sobre o acervo público — paga-se
  escala, não acesso), **auth por chave de API** (Bearer/X-API-Key) com **emissão/revogação por
  cliente no banco** (`chave_api`, só hash; api só lê, admin emite — least-privilege; CLI
  `run_chaves`) + break-glass por `DEEP_API_KEYS` — ADR-0019/0020. *(Cotas/billing + rate-limit
  autenticado no gateway + consulta-lote otimizada: próximos.)*
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
