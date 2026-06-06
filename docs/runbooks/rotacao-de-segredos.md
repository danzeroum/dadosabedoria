# Runbook — Rotação de segredos

> Invariante 8 (segredo nunca no código): todo segredo vem do ambiente / gestor de segredos, então
> rotacionar é trocar o valor lá e reiniciar quem o lê. Alguns têm sutilezas (abaixo). Faça um
> backup (`backup-restore.md`) **antes** de qualquer rotação de chave de cifragem.

## Resumo

| Segredo               | Dificuldade | Efeito colateral                                   |
|-----------------------|-------------|----------------------------------------------------|
| Senhas das roles (DB) | fácil       | reinício rolante dos serviços                      |
| `JWT_SECRET`          | fácil       | sessões de cidadão caem (re-login)                 |
| `BACKUP_PASSPHRASE`   | fácil       | guarde a antiga enquanto houver artefato no prazo  |
| `APP_FIELD_KEY`       | **difícil** | quebra hashes/cifragem existentes — exige key-ring |

## Senhas das roles do banco (`role_analitica`, `role_consentimento`, `postgres`)

A migração `0009` cria as roles com `IF NOT EXISTS` — ou seja, **re-rodar a migração NÃO troca a
senha** de uma role existente (de propósito). Rotação é manual:

```sql
-- como superusuário, no banco:
ALTER ROLE role_analitica     WITH PASSWORD 'novo_segredo';
ALTER ROLE role_consentimento WITH PASSWORD 'novo_segredo';
```

1. `ALTER ROLE … PASSWORD` no banco.
2. Atualize a senha **na DSN** correspondente no gestor de segredos (`DATABASE_URL` /
   `CONSENT_DATABASE_URL` / `ADMIN_DATABASE_URL`). A DSN é a **fonte única** do nome/senha da role.
3. Reinício rolante dos serviços que usam aquela DSN (api/worker/ai para a analítica; o serviço de
   consentimento para a de consentimento). Conexões antigas seguem até o pool reciclar.

> Como a DSN guarda a senha, mantê-las em sincronia (passo 1 ↔ 2) é o ponto crítico. Rotacione uma
> role por vez para limitar o risco.

## `JWT_SECRET` (auth do cidadão)

Assina o cookie de sessão (HS256). Trocar invalida todas as sessões: os cidadãos refazem login
(impacto pequeno — sessão curta de 30 min). Procedimento: troque `JWT_SECRET`, reinicie o serviço de
consentimento.

- **Rotação graciosa (hardening futuro, sinalizado):** aceitar uma *lista* de segredos na
  verificação (novo + antigo por uma janela) e assinar só com o novo. Exige uma pequena mudança em
  `app/consentimento/auth.py` (hoje há um único `JWT_SECRET`).

## `BACKUP_PASSPHRASE`

Cifra o dump de PII em repouso. Trocar afeta só os **novos** backups. Mantenha a passphrase antiga
no gestor de segredos enquanto existirem artefatos `app-pii_*.dump.gpg` dentro da retenção
(`APP_RETENTION_DAYS`, padrão 7 dias) — sem ela, não dá para restaurá-los. Passada a retenção,
descarte a antiga.

## `APP_FIELD_KEY` — anel de chaves (implementado, ADR-0016)

`app/consentimento/cripto.py` usa a chave **primária** (`APP_FIELD_KEY`) para duas coisas
**determinísticas**: o pseudônimo `contato_hash = HMAC-SHA256(chave, contato)` (o e-mail bruto
**nunca** é gravado; o `sub` do JWT é esse hash) e a cifragem de campo (`condicao_sensivel`, Fernet).
Trocar a chave “na lata” quebraria tudo (hashes órfãos, textos ilegíveis) — por isso há um **anel**:
`APP_FIELD_KEYS_ANTIGAS` (CSV) lista chaves aposentadas, aceitas só para **decifrar/verificar**.

- **Cifragem:** `MultiFernet` cifra com a primária e decifra com qualquer chave do anel.
- **Pseudônimo:** `hashes_contato` calcula o hash com cada chave; no **login**, `migrar_pseudonimo`
  casa qualquer versão e **regrava** a linha com o hash da primária (re-chave preguiçoso).

**Procedimento de rotação (sem perda):**

1. Gere a chave nova. No gestor de segredos: mova a atual para `APP_FIELD_KEYS_ANTIGAS` e ponha a
   **nova** em `APP_FIELD_KEY`. Reinicie o serviço de consentimento (lê o anel no boot).
2. **Re-cifre** as condições sensíveis para a primária (no contêiner de consentimento):
   ```bash
   python -m app.consentimento.run_rechave
   ```
3. Os **pseudônimos** migram sozinhos conforme os cidadãos fazem login (re-chave preguiçoso).
4. Quando a migração estiver completa (ou após a janela de retenção dos alertas), **remova** a chave
   antiga de `APP_FIELD_KEYS_ANTIGAS` e reinicie. Pronto — a antiga não decifra mais nada.

> Com o anel vazio, o comportamento é o de chave única (compatível-para-trás). Em incidente
> (vazamento), rotacione já + `run_rechave` + invalide sessões (trocar `JWT_SECRET`) + avise os
> titulares. Verificado por teste (unidade + integração de rotação contra Postgres real).
