# ADR-0012 — Runtime de consentimento (PII isolada) e auth do cidadão v1

- **Status:** aceito (auth do cidadão **v1** — especificação proposta para a lacuna do briefing;
  sinalizada)
- **Data:** 2026-06-05

## Contexto
A fundação criou o schema `app` isolado (roles, RLS, rede) e o teste de negação. Faltava o
**runtime** que o usa: o cidadão consente em alertas, informa condição sensível, acessa, revoga e
elimina seus dados (LGPD) — tudo isolado do acervo analítico (invariante 2).

## Decisão
- **Serviço ISOLADO** (`app/consentimento/`, compose `consent`): conecta como `role_consentimento`
  via `CONSENT_DATABASE_URL` (engine separada), na rede `net_consentimento`. **Único** com
  `APP_FIELD_KEY`. api/worker/ai **não** acessam `app` (checagem estática do compose no CI).
- **Pseudonimização + cifragem de campo** (`cripto.py`): contato por HMAC-SHA256 determinístico
  (pepper = `APP_FIELD_KEY`) → `contato_hash` (o e-mail bruto nunca é gravado); condição sensível
  cifrada com **Fernet** (chave derivada do `APP_FIELD_KEY`) antes de gravar.
- **Trilha de auditoria** (`app.auditoria_acesso`, migração 0011, também sob RLS): toda operação
  (assinar/listar/revogar/eliminar) é registrada.
- **Ciclo LGPD** (`rotas.py`): `POST /v1/alertas` (consentir) · `GET /v1/alertas` (acessar) ·
  `DELETE /v1/alertas/{id}` (revogar, Art. 8 §5) · `DELETE /v1/eu` (eliminar, Art. 18).
- **Auth do cidadão v1 (proposta):** login simples emite **JWT curto** (HS256) em **cookie
  HttpOnly + SameSite=Strict** (token nunca em localStorage, §8); o `sub` é o `contato_hash`. OIDC
  real é plugue futuro. CSRF: SameSite (token anti-CSRF é hardening futuro).
- **Gateway:** o Traefik (ingress controlado) ganha a rede `net_consentimento` só para **rotear**
  `/v1/alertas|/v1/auth|/v1/eu` ao serviço de consentimento, com prioridade > api.

## Consequências / a evoluir
- O isolamento §8.1 deixa de ser só estrutura: é **exercido** e testado (PII cifrada, contato
  pseudonimizado, role analítica negada em `app.*` incl. a auditoria, ciclo LGPD completo).
- Próximo: **OIDC real** (provedor de identidade — decisão do responsável), token anti-CSRF, rotação
  de chave de campo, e o consumo dos alertas (worker que casa indicador×território e notifica).
