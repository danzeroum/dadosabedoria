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

## `APP_FIELD_KEY` — a difícil (key-ring)

`app/consentimento/cripto.py` usa **uma** chave para duas coisas **determinísticas**:
- `contato_hash = HMAC-SHA256(APP_FIELD_KEY, contato)` — pseudônimo do cidadão (o e-mail bruto
  **nunca** é gravado; o `sub` do JWT é esse hash);
- cifragem de campo (`condicao_sensivel`) com Fernet, chave derivada da `APP_FIELD_KEY`.

Trocar a chave “na lata” **quebra os dados existentes**: os `contato_hash` antigos ficam órfãos (o
cidadão volta, gera um hash novo e não acha seus alertas) e os textos cifrados ficam ilegíveis.
Como o e-mail bruto **não** foi guardado (privacidade), não dá para apenas re-hashear.

**Procedimento suportado (key-ring + re-chaveamento preguiçoso):**

1. **Pré-requisito de código (sinalizado — ainda não implementado):** adicionar uma coluna
   `chave_versao` nas tabelas de `app` e fazer `cripto.py` operar com um **anel de chaves**:
   - cifragem: `MultiFernet([nova, antiga])` — decifra com qualquer uma, recifra com a nova;
   - pseudônimo: ao logar, compute o hash com **todas** as versões e case com qualquer uma;
     ao casar com uma versão antiga, **regrave** a linha com o hash da chave nova (migração
     preguiçosa, no próximo contato do cidadão).
2. Publique a chave nova como versão corrente; mantenha a antiga no anel.
3. **Re-cifre** `condicao_sensivel` em lote (decifra com a antiga, cifra com a nova) — isso é
   possível porque o texto está no banco.
4. Os **pseudônimos** migram sozinhos conforme os cidadãos acessam (passo 1). Aposente a chave antiga
   só quando a migração estiver completa (ou aceite que pseudônimos nunca mais vistos fiquem na
   versão antiga até expirarem por retenção).

> Até esse código existir, considere a `APP_FIELD_KEY` **não rotacionável sem perda**. Está listado
> como evolução no ADR-0012 e ADR-0013. Em incidente (vazamento da chave), o caminho de menor dano é:
> nova chave + re-cifrar o que dá + invalidar sessões (trocar `JWT_SECRET`) + avisar os titulares.
