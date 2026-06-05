# ADR-0002 — Isolamento de PII por duas roles + RLS + rede + teste de negação

- **Status:** aceito
- **Data:** 2026-06-05

## Contexto
Dado pessoal (assinatura de alerta, condição de saúde) só pode existir no schema `app`, isolado por
rede e credencial (invariante 2, doc técnico §8.1). A API analítica e a IA **não** podem acessá-lo.
A garantia tem de ser **verificável a cada commit**, não uma promessa.

## Decisão
Defesa em profundidade, implementada na migração `0009` e no compose:

1. **Roles distintas:** `role_analitica` (api/worker/ai) recebe USAGE + SELECT/INSERT/UPDATE em
   `public`; **REVOKE ALL** em `app` (sem nem USAGE → não resolve `app.*`). `role_consentimento` é
   a única com acesso a `app`; só leitura nas dimensões que referencia; sem escrita no acervo.
   Os nomes/senhas vêm das DSNs (fonte única).
   - *Nota:* `role_analitica` recebe **UPDATE** (além de SELECT/INSERT) porque o caminho ouro usa
     upsert idempotente (`ON CONFLICT DO UPDATE`) e o padrão expand-and-contract precisa de
     backfill. Isso não enfraquece o isolamento (que é sobre o schema `app`, não sobre escrever no
     acervo analítico).
2. **RLS** (`ENABLE` + `FORCE ROW LEVEL SECURITY`) nas tabelas de `app`, política só para
   `role_consentimento` (segunda camada; USAGE é a tranca primária).
3. **Rede:** `net_core` (api/worker/ai) e `net_consentimento` (db + consentimento). A `ai` **não**
   compartilha rede com o consentimento. `pg_hba` restringe a origem de cada role por subnet
   (best-effort em dev; em prod, somar política de rede real).
4. **Credenciais:** api/worker/ai **não** recebem `CONSENT_DATABASE_URL`/`APP_FIELD_KEY` — checado
   por teste estático do compose no CI.
5. **Teste de negação (quality gate):** `role_analitica` lendo `app.*` deve falhar com permissão
   negada (SQLSTATE 42501); um **controle positivo** (`role_consentimento` consegue ler) garante
   que a negação não passa por motivo trivial. Build reprova se o acesso for possível.

## Consequências
- Isolamento de PII é uma garantia testada, não documental.
- Paridade dev/prod parcial no `pg_hba` (subnets fixas no compose); a camada de rede real de
  produção é um item de hardening conhecido.
