# ADR-0013 — Runbooks operacionais: backup/restauração com separação de PII, rotação e `DAGSTER_HOME`

- **Status:** aceito
- **Data:** 2026-06-05

## Contexto
O plano marcava, como **primeiro runbook operacional “quando o dado real chega”**, o backup/restauração
com o backup do `app` (PII) **separado** do analítico, cada um com retenção própria (§8.1.5 / LGPD
Art. 18). Com a ingestão (CAGED/ESTBAN/IBGE) e o runtime de consentimento já no lugar, o banco passa
a ter dado real — então este é o momento. Faltavam também procedimentos de **rotação de segredos** e
a **persistência do histórico do Dagster**.

## Decisão

### Backup/restauração (`scripts/backup.sh`, `scripts/restore.sh`)
- **Dois artefatos, separados por classe**, espelhando o isolamento §8.1 na camada de backup:
  - `acervo-analitico` — `pg_dump --exclude-schema=app` rodando como **`role_analitica`**, que
    estruturalmente **não lê `app`** (defesa em profundidade sobre o flag). Sem PII por construção.
  - `app-pii` — `pg_dump --schema=app --enable-row-security` como **`role_consentimento`**,
    canalizado direto para **`gpg --symmetric` (AES256)** — a PII **nunca toca o disco em claro**.
- **Dump só de dados** (`--data-only`): o esquema (roles, RLS, `app`) é reproduzível por
  `alembic upgrade head`; o backup carrega só o insubstituível. `spatial_ref_sys`/`alembic_version`
  são excluídos (vêm do PostGIS/migrações).
- **Retenção por classe**, PII mais curta (padrão 7d vs 30d) — minimização: a eliminação (Art. 18)
  se propaga quando os artefatos de PII antigos são podados.
- **Proveniência** (invariante 5): cada artefato tem manifesto (`sha256`, origem, versão, retenção);
  o restore confere o `sha256` antes de aplicar.
- **Restauração privilegiada:** roda como admin/superusuário (necessário para `setval` e para
  inserir no `app` sob `FORCE ROW LEVEL SECURITY`); `--disable-triggers` resolve as FKs circulares de
  `territorio`. O IVM (view materializada) é recomputado, não restaurado.
- **Migração `0012`** (aditiva): concede a cada role **SELECT nas sequences do seu schema**
  (existentes/futuras), para o `pg_dump` ler o estado das colunas IDENTITY rodando como a role de
  menor privilégio. Nada cruza a fronteira §8.1 — `role_analitica` segue sem acesso a `app`.
- **Verificação no CI:** um teste **estático** (a separação é mecânica) e um **vivo** (insere
  marcador de PII, faz o backup, prova que ele não vaza no analítico e está no de PII cifrado).

### Rotação de segredos (`docs/runbooks/rotacao-de-segredos.md`)
- Senhas de role e `JWT_SECRET`: procedimento direto (a migração `0009` **não** rotaciona senha de
  role existente — é manual via `ALTER ROLE`). `BACKUP_PASSPHRASE`: manter a antiga durante a
  retenção dos artefatos.
- **`APP_FIELD_KEY` é a difícil:** pseudônimo (HMAC) e cifragem (Fernet) são determinísticos na
  chave e o e-mail bruto não é guardado → trocar “na lata” quebra os dados. O caminho suportado é um
  **anel de chaves** (`MultiFernet` + verificador HMAC multi-versão) com **coluna `chave_versao`** e
  re-chaveamento preguiçoso no próximo login — **mudança de código sinalizada** (ainda não feita).

### `DAGSTER_HOME` (`docs/runbooks/dagster-home.md`)
- Volume nomeado `dagster_home` montado no `orchestrator` + `DAGSTER_HOME=/dagster_home` → histórico
  de runs/agendamentos sobrevive a reinício. SQLite padrão basta no Degrau 1; Postgres ao escalar.

## Consequências / a evoluir
- O isolamento de PII deixa de valer só em runtime: vale também **em repouso/backup** (testado).
- A `APP_FIELD_KEY` é, **hoje, não rotacionável sem perda** — o anel de chaves é o próximo passo de
  hardening (também citado no ADR-0012), assim como a rotação graciosa do `JWT_SECRET` (lista de
  segredos aceitos) e o storage do Dagster em Postgres.
- Backups off-box, cifragem por destinatário (chave pública em vez de passphrase simétrica) e teste
  periódico de restauração (game-day) ficam como evolução de operação.
