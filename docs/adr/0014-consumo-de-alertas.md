# ADR-0014 — Consumo de alertas (IVM → notificação), fechando o ciclo do consentimento

- **Status:** aceito
- **Data:** 2026-06-05

## Contexto
O runtime de consentimento (ADR-0012) deixa o cidadão **assinar** alertas, mas nada os
**consumia**: assinava-se e o IVM mudava sem que ninguém fosse avisado. Faltava casar o evento
analítico (um município entra em **vermelho** no IVM) com os assinantes daquele território e
notificá-los — sem afrouxar o isolamento de PII (invariante 2).

## Problema central — o casamento cruza a fronteira §8.1
O match precisa de DOIS lados que vivem em lados opostos da fronteira:
- o **evento** (IVM por território) está no acervo analítico (público), legível por `role_analitica`;
- os **assinantes** (`contato_hash`) estão no schema `app` (PII), legíveis só por `role_consentimento`.

A direção **crítica** a proteger é "serviços analíticos (api/worker/ai) **nunca** tocam PII". A
direção inversa — o serviço de consentimento, já isolado, ler um agregado **público** — é benigna e
já tem precedente (ele lê `territorio`/`base_legal`).

## Decisão
- **O job roda DENTRO do serviço de consentimento** (`app/consentimento/`, role_consentimento, rede
  isolada) — o único lugar com acesso ao `app`. Ele lê o IVM público e casa com seus assinantes,
  tudo com a própria role. Nenhuma ponte de rede nova; nenhum serviço analítico vê PII.
- **Leitura ESTREITA e explícita** (migração `0013`): `GRANT SELECT ON ivm_municipio TO
  role_consentimento` (dado público, sem PII). A direção crítica (`role_analitica` → `app`) segue
  **REVOKE** e **testada** (a negação agora cobre também `app.notificacao`).
- **Entrega *pull*, não *push*** (minimização — LGPD): como só guardamos o **pseudônimo**
  (`contato_hash`), não há contato bruto para e-mail/SMS. A notificação é gravada em
  `app.notificacao` e o cidadão a **recupera autenticado** (`GET /v1/notificacoes`, JWT cujo `sub` é
  o `contato_hash`). Zero PII nova coletada.
- **`app.notificacao`** (migração `0013`): isolada como as demais (RLS + policy só p/
  role_consentimento). **Idempotente** (`UNIQUE (assinante_id, periodo)` + `ON CONFLICT DO
  NOTHING`): reprocessar não duplica. Carrega **proveniência** (fonte, metodologia do IVM —
  invariante 5) e fica imutável (snapshot do que foi dito).
- **Gatilho:** CLI `python -m app.consentimento.run_alertas [YYYY-MM]`, rodada no contêiner de
  consentimento após cada REFRESH do IVM (período-alvo opcional; padrão = mais recente). Toda
  operação é auditada (`acao='notificar'`).

## Alternativa considerada (e adiada)
**Worker analítico empurra os eventos ao consentimento via gateway** (endpoint interno autenticado):
separação ainda mais forte (o consentimento nunca leria o acervo), mas adiciona rota interna,
token de serviço e um caminho de rede novo atravessando o ingress. Para esta fatia, a leitura
estreita do IVM público é mais simples, testável e mantém intacta a invariante crítica. Fica como
evolução se quisermos separação total.

## Consequências / a evoluir
- O ciclo do consentimento fecha: assinar → (IVM muda) → **ser notificado** → recuperar → revogar →
  eliminar (cascade apaga as notificações).
- **Agendamento** automático após o REFRESH do IVM: hoje é uma CLI manual (o `orchestrator` é
  analítico/`net_core` e não pode rodar o job de consentimento). Um scheduler no lado de
  consentimento é o próximo passo — sinalizado.
- Marcar-como-lida (`lida_em` já existe no schema), canais de entrega adicionais (se algum dia se
  decidir coletar contato cifrado, com base legal própria) e alertas por **condição sensível** ficam
  como evolução.
