#!/usr/bin/env bash
# Runbook de backup com SEPARAÇÃO de PII (LGPD Art. 18 / §8.1.5; invariantes 2 e 5).
#
# Produz DOIS artefatos independentes, com retenção própria. Dump é só de DADOS
# (--data-only): o ESQUEMA é reproduzível por `alembic upgrade head` (está no git); o backup
# carrega só o que é insubstituível. Cada classe é dumpada COMO a role de menor privilégio:
#   1) acervo analítico  — SEM PII. `pg_dump --data-only --exclude-schema=app` como role_analitica
#      (que estruturalmente NEM consegue ler `app`: defesa em profundidade). Retenção longa.
#   2) PII (schema `app`) — dump SEPARADO e CIFRADO (gpg AES256) como role_consentimento (única
#      identidade com acesso a `app`; --enable-row-security respeita a RLS). Retenção CURTA.
#
# Segredo nunca no código (invariante 8): tudo vem do ambiente. Uso:
#   DATABASE_URL=... CONSENT_DATABASE_URL=... BACKUP_PASSPHRASE=... scripts/backup.sh
set -Eeuo pipefail

# --- configuração (12-factor) -------------------------------------------------------------
: "${DATABASE_URL:?defina DATABASE_URL (role_analitica) — dump do acervo analítico}"
: "${CONSENT_DATABASE_URL:?defina CONSENT_DATABASE_URL (role_consentimento) — dump do schema app}"
: "${BACKUP_PASSPHRASE:?defina BACKUP_PASSPHRASE — cifragem do dump de PII (>= 16 chars)}"

BACKUP_DIR="${BACKUP_DIR:-./backups}"
ANALYTIC_RETENTION_DAYS="${ANALYTIC_RETENTION_DAYS:-30}"
APP_RETENTION_DAYS="${APP_RETENTION_DAYS:-7}"   # PII: retenção CURTA por minimização (LGPD)

log() { printf '%s  %s\n' "$(date -u +%H:%M:%SZ)" "$*" >&2; }

# DSN do SQLAlchemy (postgresql+asyncpg://) -> libpq (postgresql://). A senha fica na URL (não em argv
# separado) e o script não a ecoa.
para_libpq() { printf '%s' "$1" | sed -E 's#^postgresql\+[a-z0-9]+://#postgresql://#'; }
host_de()    { printf '%s' "$1" | sed -E 's#^postgresql://[^@]*@##; s#[?].*$##'; }  # -> host:porta/db

ts="$(date -u +%Y%m%dT%H%M%SZ)"
analitico_dir="${BACKUP_DIR}/acervo-analitico"
app_dir="${BACKUP_DIR}/app-pii"
mkdir -p "$analitico_dir" "$app_dir"

manifesto() {  # $1=arquivo $2=classe $3=retencao_dias $4=origem
  local sha; sha="$(sha256sum "$1" | cut -d' ' -f1)"
  cat > "$1.manifesto.json" <<JSON
{
  "artefato": "$(basename "$1")",
  "classe": "$2",
  "modo": "data-only",
  "criado_utc": "${ts}",
  "origem": "$4",
  "pg_dump": "$(pg_dump --version | grep -oE '[0-9]+\.[0-9]+' | head -1)",
  "retencao_dias": $3,
  "sha256": "${sha}"
}
JSON
  log "manifesto: $(basename "$1").manifesto.json (sha256 ${sha:0:12}…)"
}

# --- 1) acervo analítico (SEM PII) -------------------------------------------------------
# role_analitica + --exclude-schema=app: PII NÃO pode entrar neste artefato (estrutural + explícito).
analitico_url="$(para_libpq "$DATABASE_URL")"
analitico_file="${analitico_dir}/acervo-analitico_${ts}.dump"
log "dump analítico (role_analitica, exclui schema app) -> $(basename "$analitico_file")"
pg_dump "$analitico_url" \
  --data-only --format=custom --no-owner \
  --exclude-schema=app \
  --exclude-table='public.spatial_ref_sys' \
  --exclude-table='public.alembic_version' \
  --file="$analitico_file"
manifesto "$analitico_file" "acervo-analitico" "$ANALYTIC_RETENTION_DAYS" "$(host_de "$analitico_url")"

# --- 2) PII (schema app) — SEPARADO e CIFRADO --------------------------------------------
# role_consentimento + --enable-row-security (respeita a RLS do app); cifrado antes de tocar o disco.
app_url="$(para_libpq "$CONSENT_DATABASE_URL")"
app_file="${app_dir}/app-pii_${ts}.dump.gpg"
log "dump de PII (role_consentimento, só schema app) cifrado AES256 -> $(basename "$app_file")"
pg_dump "$app_url" --data-only --format=custom --schema=app --enable-row-security \
  | gpg --batch --yes --pinentry-mode loopback --symmetric --cipher-algo AES256 \
        --passphrase-fd 3 -o "$app_file" 3<<<"$BACKUP_PASSPHRASE"
manifesto "$app_file" "app-pii" "$APP_RETENTION_DAYS" "$(host_de "$app_url")"

# --- retenção (poda por classe; PII expira mais rápido) ----------------------------------
podar() {  # $1=dir $2=dias $3=glob
  log "retenção: removendo ${3} com mais de ${2} dias em ${1}"
  find "$1" -maxdepth 1 -type f -name "$3" -mtime "+${2}" -print -delete || true
  find "$1" -maxdepth 1 -type f -name '*.manifesto.json' \
    -exec sh -c 'test -f "${1%.manifesto.json}" || rm -f "$1"' _ {} \; || true
}
podar "$analitico_dir" "$ANALYTIC_RETENTION_DAYS" 'acervo-analitico_*.dump'
podar "$app_dir" "$APP_RETENTION_DAYS" 'app-pii_*.dump.gpg'

log "OK — analítico: ${analitico_file} | pii(cifrado): ${app_file}"
