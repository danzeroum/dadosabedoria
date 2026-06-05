#!/usr/bin/env bash
# Runbook de restauração — contraparte de backup.sh (dumps SÓ de dados).
#
# Pré-condição: o banco-alvo já tem o ESQUEMA (roles, schema app, RLS) aplicado:
#     createdb dadosabedoria && alembic upgrade head     # reproduz tudo a partir do git
# A restauração é uma operação de DR PRIVILEGIADA: roda como ADMIN_DATABASE_URL (superusuário) —
# necessário para `setval` das sequences e para inserir no `app` sob FORCE ROW LEVEL SECURITY.
# A SEPARAÇÃO de PII é preservada: analítico e app são restaurados por comandos/arquivos distintos.
#
# Uso:
#   scripts/restore.sh analitico <acervo-analitico_*.dump>
#   scripts/restore.sh app-pii   <app-pii_*.dump.gpg>          (pede BACKUP_PASSPHRASE)
set -Eeuo pipefail

classe="${1:?uso: restore.sh <analitico|app-pii> <arquivo>}"
arquivo="${2:?caminho do artefato de backup}"
: "${ADMIN_DATABASE_URL:?defina ADMIN_DATABASE_URL (superusuário) — alvo da restauração}"
[ -f "$arquivo" ] || { echo "arquivo não encontrado: $arquivo" >&2; exit 1; }

log() { printf '%s  %s\n' "$(date -u +%H:%M:%SZ)" "$*" >&2; }
para_libpq() { printf '%s' "$1" | sed -E 's#^postgresql\+[a-z0-9]+://#postgresql://#'; }

verificar_sha() {  # confere o manifesto, se presente (integridade/proveniência)
  local f="$1" man="$1.manifesto.json"
  [ -f "$man" ] || { log "sem manifesto p/ $(basename "$f") (pulando verificação de sha256)"; return 0; }
  local esperado real
  esperado="$(grep -oE '[0-9a-f]{64}' "$man" | head -1)"
  real="$(sha256sum "$f" | cut -d' ' -f1)"
  [ "$esperado" = "$real" ] || { echo "sha256 DIVERGE do manifesto: corrupção/violação" >&2; exit 1; }
  log "integridade OK (sha256 ${real:0:12}…)"
}

alvo="$(para_libpq "$ADMIN_DATABASE_URL")"
# --data-only --disable-triggers: carga na ordem certa sem brigar com FKs; exige superusuário.
restaurar() { pg_restore --data-only --disable-triggers --no-owner --dbname="$alvo" "$1"; }

case "$classe" in
  analitico)
    verificar_sha "$arquivo"
    log "restaurando ACERVO ANALÍTICO (data-only) como admin"
    restaurar "$arquivo"
    log "lembrete: recompute o IVM — REFRESH MATERIALIZED VIEW CONCURRENTLY ivm_municipio;"
    ;;
  app-pii)
    : "${BACKUP_PASSPHRASE:?defina BACKUP_PASSPHRASE para decifrar o dump de PII}"
    verificar_sha "$arquivo"
    log "restaurando PII (schema app) — decifrando AES256 em memória"
    tmp="$(mktemp)"; trap 'rm -f "$tmp"' EXIT
    gpg --batch --yes --pinentry-mode loopback --decrypt --passphrase-fd 3 \
        -o "$tmp" "$arquivo" 3<<<"$BACKUP_PASSPHRASE"
    restaurar "$tmp"
    ;;
  *)
    echo "classe inválida: ${classe} (use 'analitico' ou 'app-pii')" >&2; exit 2 ;;
esac

log "restauração concluída (${classe})."
