# Pendências do Dono — fila de análise (atualizado pós-#0 + MODO DEV)

Tudo que **depende de você** (não do desenvolvedor) para o trabalho avançar de "grau-demo honesto"
para "produto real / lançado". O dev segue sozinho pelo roadmap enquanto você estiver fora; **não
fica parado** em nenhum destes — ele **anota e continua**, acumulando o que for novo na *Lista de
desbloqueio* do repo (ver §3). Quando você voltar, revise **este documento + a Lista de desbloqueio
atualizada no `roadmap.md`** (o dev pode ter acrescentado itens).

> **MODO DEV (2026-06-07 + 2026-06-08):** você ampliou a autonomia — o dev **abre PRs, acompanha a CI
> e mergeia no verde sozinho** (barra inalterada: só verde genuíno). **O que mudou desde o último
> checkpoint (sessão de 2026-06-08):**
> - **PNCP aberto e validado**: `pncp.gov.br` retorna 200 na API (bug de User-Agent corrigido; ADR-0033).
> - **IBGE gzip fix**: `FetcherIbgeHTTP` agora descomprime; 5.571 municípios + 27 UFs carregados (ADR-0033).
> - **SICONFI nacional 2024**: ingestão completa de ~5.570 municípios executada; OndeFoi go-live com
>   dados reais (endpoint lê `execucao_funcao`, não DEMO_MUNICIPIOS). ADR-0033.
> - **INEP TLS cert**: host acessível mas certificado do servidor falha. Gate mudou de "allowlist" para
>   "certificado INEP". Bloqueio técnico do lado do INEP.
> - **ESTBAN URL gate**: `www.bcb.gov.br` / `dadosabertos.bcb.gov.br` respondem 200, mas a URL do ZIP
>   do ESTBAN está embutida no SPA Angular (não encontrada no catálogo CKAN). Gate mudou de "host" para "URL".
> - **DATASUS FTP**: timeout na porta 443; protocolo FTP puro não é acessível via proxy HTTP.
> - **CAGED DNS**: `ftp.mtps.gov.br` não resolve para HTTPS; novo CAGED via `api.bcb.gov.br` (fora do allowlist).

Ordenado por **impacto** (o que destrava mais primeiro). Cada item: o que é · o que fazer · o que
destrava · impacto se não fizer · prioridade.

---

## 1. Ações pontuais (gates externos 🔴)

### ✅ #0 — Allowlist *(sondado 2× — 2026-06-07 ADR-0028 + 2026-06-08 ADR-0033)*

**Validados e ao vivo (dado real na DB):**
- ✅ **SICONFI** `apidatalake.tesouro.gov.br` — forma confirmada (ADR-0028); rate-limit adicionado;
  **ingestão nacional 2024 executada** (~5.570 municípios × ~24 funções → `execucao_funcao`). OndeFoi
  vai ao vivo com dados reais.
- ✅ **IBGE** `servicodados.ibge.gov.br` — gzip fix aplicado; 5.571 municípios + 27 UFs carregados.
- ✅ **PNCP** `pncp.gov.br` — **validado na sessão de 2026-06-08** (ADR-0033): API retorna 200; bug
  de User-Agent corrigido (`FetcherPncpHTTP`); 35.910 contratos jan/2024 confirmados.

**Gates que mudaram de natureza (não são mais "só allowlist"):**
- ⚠️ **INEP** `download.inep.gov.br` — host acessível (503 sem `x-deny-reason`), mas **TLS falha**:
  `CERTIFICATE_VERIFY_FAILED` (issuer não reconhecido). O problema está no **certificado do servidor
  INEP**, não no allowlist. _(O que fazer: verificar se o INEP corrigiu o cert ou se há URL
  alternativa com TLS válido; ou usar `ssl.create_default_context()` com `check_hostname=False`
  apenas em dev — não recomendado em produção.)_
- ⚠️ **ESTBAN/BCB** `www.bcb.gov.br` e `dadosabertos.bcb.gov.br` — **ambos 200** (desbloqueados em
  2026-06-08). Gate mudou: a **URL do ZIP do ESTBAN não foi encontrada** — BCB usa SPA Angular; URLs
  históricas (`/estabilidadefinanceira/cosif/ESTBAN*.zip`) retornam HTML; catálogo CKAN (4.225
  datasets) não tem "estban". _(O que fazer: inspecionar bundle JS do SPA BCB para achar o endpoint
  real, ou contatar BCB/COSIF para obter a URL direta.)_
- ⚠️ **DATASUS** `ftp.datasus.gov.br` — timeout na porta 443 (FTP puro; proxy só suporta HTTP/HTTPS).
  _(Sem caminho HTTP alternativo identificado para o SIH. Gate técnico de protocolo.)_
- ❌ **CAGED** `ftp.mtps.gov.br` — `resolve_no_records` (DNS HTTPS não existe). O **novo CAGED** está
  disponível via `api.bcb.gov.br` (PDET/BCB) — esse host não está no allowlist.
  _(O que fazer: adicionar `api.bcb.gov.br` ao allowlist Custom para acessar novo CAGED via BCB.)_

**Destrava:** com PNCP validado, o próximo produto sobre compras pode usar dado real. SICONFI/IBGE
já estão ao vivo (OndeFoi). INEP/ESTBAN/DATASUS/CAGED têm bloqueios técnicos específicos acima.

### 🔴 OIDC do cidadão — *login real* — **PRIORIDADE ALTA**
- **O que é:** provedor de identidade para o cidadão se autenticar (assinar alerta "Avise-me", área
  logada). Hoje roda em JWT dev até existir isto.
- **O que fazer:** escolher o provedor — **gov.br (Login Único)** para identidade real do cidadão,
  ou **Keycloak** se for auto-hospedado. Registrar/criar um **client OIDC** e obter:
  `issuer URL`, `client_id`, `client_secret`, e definir as **redirect URIs** (apontam para o seu
  domínio de produção — então este item **anda junto com o domínio**, abaixo).
- **Onde entregar ao dev:** como variáveis de ambiente na config do ambiente (claude.ai/code →
  *Environment variables*, formato `.env`). **Para construir/testar**, uma credencial de
  dev/homolog basta; o segredo de **produção** vai no deploy real, não na env da sessão (a env do
  ambiente é visível a quem edita o ambiente).
- **Destrava:** auth do cidadão, alertas ("Avise-me"), toda a camada do cidadão (Onda 2D).
- **Se não fizer:** o produto fica sem login/alerta; o dev constrói a UI e o runtime de
  consentimento "preparados", mas degradados (sem disparo real).

### 🔴 Domínio + TLS de produção — **PRIORIDADE ALTA**
- **O que é:** sair do dev-mode (Traefik sem TLS) para um domínio real com HTTPS.
- **O que fazer:** registrar um **domínio**, apontar o **DNS** para o servidor/VPS, e fornecer
  `ACME_EMAIL` (o Traefik emite o certificado Let's Encrypt automaticamente). Definir as URLs
  públicas (que também são as redirect URIs do OIDC acima).
- **Destrava:** lançar de verdade (produção), e fecha o par com o OIDC.
- **Se não fizer:** tudo continua acessível só em dev-mode; não há "site no ar" público.

### 🔴 Chave de LLM — *IA ancorada real* — **PRIORIDADE MÉDIA**
- **O que é:** a IA (respostas ancoradas com citação) hoje roda em **template** (degradação graciosa).
- **O que fazer:** ou fornecer **`LLM_BASE_URL` / `LLM_MODEL` / `LLM_API_KEY`** (ex.: DeepSeek) +
  orçamento, **ou** subir um **Ollama** local (dispensa chave). Já está tudo plugado por adaptador
  (ADR-0015) — só falta a credencial/instância.
- **Destrava:** a camada de IA com modelo real (vs. template).
- **Se não fizer:** a IA responde em modo template; nada quebra, mas não há geração real.

### 🔴 Credenciais de fontes restritas (ex.: DataJud) — **PRIORIDADE BAIXA**
- **O que é:** algumas fontes exigem chave (ex.: API pública do DataJud/CNJ tem API key).
- **O que fazer:** obter a credencial junto ao órgão e entregá-la como env var quando o produto que
  usa essa fonte entrar na fila.
- **Destrava:** **apenas** os produtos dessas fontes específicas. **As fontes abertas seguem sem isso.**
- **Se não fizer:** só os produtos restritos ficam adiados; o resto avança normalmente.

### 🔴 Conselho PbD (Defensoria/ONGs) — **PRIORIDADE BAIXA (lead longo)**
- **O que é:** um conselho de Privacidade-por-Design a constituir com Defensoria/ONGs.
- **O que fazer:** iniciar a articulação (ação organizacional/jurídica, não técnica).
- **Destrava:** **apenas** dois produtos de acesso restrito — **HAB-04** e **DIR-01**.
- **Se não fizer:** só esses dois ficam adiados; nada mais.

---

## 2. Decisões de produto (🟡) — direção, não execução

O dev está **pré-autorizado** a seguir os *defaults* destes sem te perguntar. Você não precisa
responder agora; se quiser **dar direção**, anote aqui e eu/ele incorporamos. Senão, ele segue o
default.

### ⭐ B. Re-ancoragem do OndeFoi — **a referendar** (novo, importante; ADR-0029)
- **O que tínhamos planejado:** OndeFoi = recebido (transferência) × executado por função.
- **O que o dado real mostrou (#0):** o SICONFI classifica **despesa** por função (Anexo I-E:
  Empenhado→Liquidado→Pago), mas **não** a transferência (recebido). "Recebido por função" **não
  existe na fonte** → o modelo original é **impossível**.
- **Default que o dev está construindo (MODO DEV):** medir **Liquidado ÷ Empenhado por função** — *"do
  que foi comprometido (empenhado) por área, quanto foi de fato executado (liquidado)?"*. A honestidade
  fica intacta (executar ≠ serviço; subexecução **merece a pergunta**, nunca veredito); muda a
  **pergunta-título** do produto. **Reversível** (expand-and-contract) se você redirecionar.
- **Status:** a **esteira de dado** (Anexo I-E → fato `execucao_funcao` → pipeline) está **construída**
  (ADR-0029); a **tela segue grau-demo** até seu aval. **Você decide:** referendar / redirecionar /
  conversar. **Sem ação:** o dev segue no default; nada bloqueia, só não "congela" o enquadramento.

| # | Decisão | Default que o dev seguirá se você não opinar |
|---|---|---|
| #5 | Ordem fina dos produtos | valor de produto **dentro** das fontes já desbloqueadas. _Feito nesta maratona: **TRAB-01 Pulso Produtivo** (endpoint + tela, dado real) e **OndeFoi** (tela grau-demo) — ambos "até a tela", com porta de entrada em `/`. Próximos: mais produtos sobre indicadores já no ar + **tornar vivas** INEP/PNCP/SICONFI/DATASUS quando o #0 abrir._ |
| #6 | Metas de north-star | direcionais; calibrar com dado real (não fixar número agora) |
| #7 | Foco de canal / parcerias B2G | priorizar transparência e saneamento (pull legal) |
| #8 | Alvo de VPS/nuvem | Docker na VPS 4 vCPU/16 GB; migrar só por gatilho numérico (§1.1) |

> Se você **quiser priorizar** produtos específicos do catálogo (dos ~50) para as próximas ondas,
> esta é a única coisa que muda a **ordem** do que o dev constrói. Sem sua opinião, ele segue por
> valor dentro do desbloqueado — o que é seguro.

---

## 3. Como o dev opera enquanto você está fora — e onde olhar ao voltar

**Operação autônoma (24h+):** o dev lê o topo do `CLAUDE.md` (bilhete-ponte), valida o #0 se aberto,
e segue o `roadmap.md` de cima para baixo em **fatias pequenas, CI verde por PR, ADR por decisão**.
Ele **nunca fica ocioso**: ao bater num bloqueio humano, **anota e segue** para o próximo item.

**Onde ele anota (sua fila viva, no repo):** a seção **"Lista de desbloqueio"** do `roadmap.md`. Cada
item novo entra no formato:
```
- [ ] <GATE/DECISÃO>: <o que está bloqueado> · <o que o dono precisa fazer> ·
      <o que fiz no lugar / o que adiei> · <PR/ADR de referência>
```

**Ao voltar, revise (nesta ordem):**
1. **Este documento** (os gates/decisões conhecidos acima).
2. A **"Lista de desbloqueio" do `roadmap.md`** — pode ter itens novos que o dev acumulou.
3. O **roadmap** (itens `[x]` fechados) e os **PRs mergeados** — o que andou.
4. Os **artefatos de screenshot** dos PRs de tela — para certificar a UX pela tela renderizada.

**Garantia de continuidade:** todo o estado durável vive no repo (ADRs, roadmap, código, CLAUDE.md),
então um reset do contêiner no meio da maratona **não perde nada** — a sessão nova se reorienta sozinha.

---

## Resumo de prioridade para o seu checkpoint de 36h

1. **OIDC + Domínio/TLS** (andam juntos) — destravam login e produção. **Faça estes primeiro.**
2. **Chave de LLM** (ou Ollama) — destrava IA real. Médio.
3. **Confirmar o #0** (já feito; só validar pela sonda do dev).
4. **DataJud / PbD** — baixa; só destravam fontes/produtos específicos.
5. **Direção de produtos (🟡)** — opcional; sem ela o dev segue por valor com segurança.
