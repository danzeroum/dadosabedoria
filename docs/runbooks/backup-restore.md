# Runbook — Backup & Restauração (com separação de PII)

> Primeiro runbook operacional “quando o dado real chega” (§8.1.5 / LGPD Art. 18). Implementa a
> **separação de PII** dos invariantes 1–2 também na camada de backup: o acervo analítico e o
> schema `app` (PII) são salvos em **artefatos distintos**, com **retenção própria**, e o de PII é
> **cifrado**. Scripts: `scripts/backup.sh` e `scripts/restore.sh`.

## Princípio

| Classe            | Conteúdo                          | Role do dump        | Cifrado? | Retenção (padrão) |
|-------------------|-----------------------------------|---------------------|----------|-------------------|
| `acervo-analitico`| `public.*` (sem PII)              | `role_analitica`    | não      | 30 dias           |
| `app-pii`         | `app.*` (PII, já cifrada no banco)| `role_consentimento`| **sim** (gpg AES256) | **7 dias** |

Por que assim:
- **Sem PII no backup analítico, por construção.** A PII vive só no schema `app`. O dump analítico
  roda como `role_analitica` — que **estruturalmente não consegue ler `app`** (invariante 2,
  testado) — e ainda passa `--exclude-schema=app` (defesa em profundidade). Logo o artefato
  analítico **não pode** conter PII.
- **PII isolada e cifrada.** O dump de `app` roda como `role_consentimento` (única identidade com
  acesso ao `app`) e é canalizado direto para `gpg --symmetric` (**nunca toca o disco em claro**).
- **Minimização (LGPD).** A PII tem retenção **mais curta**: um backup de PII expira rápido, então
  uma eliminação (Art. 18) “se propaga” naturalmente quando os artefatos antigos são podados.
- **Dump só de dados.** O **esquema** (roles, RLS, `app`) é reproduzível por `alembic upgrade head`
  (está no git). O backup carrega só o que é insubstituível — os dados.

## Fazer backup

```bash
export DATABASE_URL=postgresql+asyncpg://role_analitica:...@HOST:5432/dadosabedoria
export CONSENT_DATABASE_URL=postgresql+asyncpg://role_consentimento:...@HOST:5432/dadosabedoria
export BACKUP_PASSPHRASE='...'              # passphrase LONGA do gestor de segredos (cifra a PII)
export BACKUP_DIR=/var/backups/dadosabedoria # opcional (padrão ./backups)
scripts/backup.sh
```

Gera, com manifesto de proveniência (`*.manifesto.json`: sha256, origem, versão do pg_dump,
retenção):

```
$BACKUP_DIR/acervo-analitico/acervo-analitico_<ts>.dump        (+ .manifesto.json)
$BACKUP_DIR/app-pii/app-pii_<ts>.dump.gpg                      (+ .manifesto.json)
```

A retenção é aplicada ao final (poda por classe). Agende **dois** cronogramas distintos se quiser
políticas independentes (ex.: analítico diário, PII de hora em hora com expurgo rápido). Envie os
artefatos para **armazenamento off-box** (a PII com controle de acesso mais estrito).

> O `app-pii_*.dump.gpg` é inútil sem a `BACKUP_PASSPHRASE`. Perdê-la = perder o backup de PII.
> Guarde-a separada dos artefatos.

## Restaurar (DR)

Restauração é uma operação **privilegiada**: roda como **admin/superusuário** (`ADMIN_DATABASE_URL`)
— necessário para `setval` das sequences e para inserir no `app` sob `FORCE ROW LEVEL SECURITY`.
O esquema vem das migrações; o backup só recarrega dados.

```bash
# 1) banco vazio + esquema (reproduz roles, schema app, RLS a partir do git)
createdb dadosabedoria && alembic upgrade head     # (ou o migrator do compose)

# 2) restaurar cada classe (arquivos/comandos distintos: a separação é mantida)
export ADMIN_DATABASE_URL=postgresql+asyncpg://postgres:...@HOST:5432/dadosabedoria
scripts/restore.sh analitico  acervo-analitico/acervo-analitico_<ts>.dump

export BACKUP_PASSPHRASE='...'                      # só para o app-pii (decifrar)
scripts/restore.sh app-pii    app-pii/app-pii_<ts>.dump.gpg

# 3) recomputar a vista de topo (não é dumpada; é derivada)
psql "$ADMIN…" -c "REFRESH MATERIALIZED VIEW CONCURRENTLY ivm_municipio;"
```

`restore.sh` confere o `sha256` do manifesto (integridade) antes de aplicar e usa
`pg_restore --data-only --disable-triggers` (carrega na ordem certa apesar das FKs circulares de
`territorio`).

### Restaurar SÓ o acervo analítico (sem tocar PII)

É o caso comum (corrupção do acervo, rollback de ingestão): rode apenas o passo `analitico`. O
schema `app` nem é aberto — a PII não entra no fluxo.

## Verificação (rodada no CI)

- `tests/unit/test_backup_separa_pii.py` — checagem **estática** do script: dump analítico exclui
  `app`; dump de PII usa só `app` e é cifrado; retenção de PII < retenção do acervo.
- `tests/integration/test_backup_restore.py` — **prova viva** contra Postgres real: insere um
  marcador de PII, roda o backup e confirma que o marcador **não** aparece no dump analítico e
  **aparece** (após decifrar) no de PII.

## Pontos de atenção

- A `BACKUP_PASSPHRASE` é distinta da `APP_FIELD_KEY` (que cifra os campos **dentro** do banco). Uma
  protege o artefato em repouso; a outra, o dado na linha. Rotacione-as por procedimentos separados
  (ver `rotacao-de-segredos.md`).
- O IVM (`ivm_municipio`) é uma **view materializada** derivada — não é dumpada; recompute no fim.
- `spatial_ref_sys` e `alembic_version` são excluídos do dump (vêm do PostGIS e das migrações).
