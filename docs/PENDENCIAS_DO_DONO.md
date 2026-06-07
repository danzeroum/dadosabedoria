# Pendências do Dono — fila de análise (checkpoint de 36h)

Tudo que **depende de você** (não do desenvolvedor) para o trabalho avançar de "grau-demo honesto"
para "produto real / lançado". O dev segue sozinho pelo roadmap enquanto você estiver fora; **não
fica parado** em nenhum destes — ele **anota e continua**, acumulando o que for novo na *Lista de
desbloqueio* do repo (ver §3). Quando você voltar, revise **este documento + a Lista de desbloqueio
atualizada no `roadmap.md`** (o dev pode ter acrescentado itens).

Ordenado por **impacto** (o que destrava mais primeiro). Cada item: o que é · o que fazer · o que
destrava · impacto se não fizer · prioridade.

---

## 1. Ações pontuais (gates externos 🔴)

### ✅ #0 — Allowlist do SICONFI *(feito — só confirmar)*
- **Você já fez.** A prova é a sonda do dev na **sessão nova**: `HTTP/` limpo = aberto; se vier
  `x-deny-reason: host_not_allowed`, confira no editor do ambiente (claude.ai/code) que ficou
  **Network access = Custom**, com **"Also include default list of common package managers"**
  marcada, e **salvo**. Fallback temporário só p/ validar: **Full**.
- **Destrava:** a 1ª validação real do OndeFoi (forma real do DCA).

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
