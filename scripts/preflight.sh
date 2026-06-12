#!/usr/bin/env bash
# Pre-flight check do .env antes de `docker compose up`.
# Valida que todos os segredos críticos foram trocados e as configurações essenciais são
# coerentes. Aborta com erro descritivo em vez de subir uma stack com credenciais padrão.
#
# Uso:  scripts/preflight.sh [caminho-do-.env]
# Saída: 0 = passou (pode ter alertas); 1 = falhou (bloqueante).
#
# Verificações BLOQUEANTES (falha → exit 1):
#   • Arquivo .env existe e é legível.
#   • Vars críticas não contêm o prefixo "change_me_" (senha padrão do .env.example).
#   • JWT_SECRET tem comprimento ≥ 32 caracteres.
#   • BACKUP_PASSPHRASE tem comprimento ≥ 16 caracteres.
#   • POSTGRES_PASSWORD é consistente com a senha em ADMIN_DATABASE_URL.
#
# Verificações de ALERTA (imprime aviso mas não bloqueia — exit 0):
#   • PUBLIC_DOMAIN / ACME_EMAIL não definidos → TLS inativo (dev-mode).
#   • LLM_API_KEY / LLM_BASE_URL não definidos → IA em template (degradação graciosa).
#   • CORS_ORIGINS ainda com valor padrão de dev (localhost:3000).
#   • DEEP_API_KEYS não definido → tier profundo só pelo break-glass do env.

set -Eeuo pipefail

ENV_FILE="${1:-.env}"

RED=$'\033[0;31m'
YEL=$'\033[1;33m'
GRN=$'\033[0;32m'
NC=$'\033[0m'

FALHAS=0
ALERTAS=0

# SC2059: variáveis ANSI nos argumentos (%s), nunca no formato.
falha()  { printf '%s[ERRO]%s  %s\n' "$RED" "$NC" "$1" >&2; FALHAS=$(( FALHAS + 1 )); }
alerta() { printf '%s[AVISO]%s %s\n' "$YEL" "$NC" "$1";    ALERTAS=$(( ALERTAS + 1 )); }
ok()     { printf '%s[OK]%s    %s\n' "$GRN" "$NC" "$1"; }

# -------------------------------------------------------------------------- 1. leitura do .env

if [ ! -f "$ENV_FILE" ]; then
    falha "Arquivo '${ENV_FILE}' não encontrado."
    falha "Execute: cp .env.example .env  e preencha os segredos antes de subir a stack."
    exit 1
fi

# Carrega o .env: ignora linhas comentadas, vazias e exporta o restante.
# shellcheck disable=SC2046
export $(grep -v '^\s*#' "$ENV_FILE" | grep -v '^\s*$' | xargs)

# -------------------------------------------------------------------------- 2. funções auxiliares

# Extrai a senha da DSN postgresql+asyncpg://user:senha@host:port/db
senha_de_dsn() {
    local dsn="$1"
    # Remove o prefixo de driver; extrai user:senha da parte antes do @
    local sem_driver
    sem_driver="$(printf '%s' "$dsn" | sed -E 's|^[^:]+://||')"
    local credenciais
    credenciais="$(printf '%s' "$sem_driver" | sed -E 's|@.*||')"
    printf '%s' "$credenciais" | cut -d: -f2-
}

# -------------------------------------------------------------------------- 3. verificações bloqueantes

printf '\n=== Pre-flight DadoSabedoria (%s) ===\n\n' "$ENV_FILE"

# Vars que NÃO podem conter "change_me_"
_CRITICAS="POSTGRES_PASSWORD ADMIN_DATABASE_URL DATABASE_URL CONSENT_DATABASE_URL APP_FIELD_KEY JWT_SECRET BACKUP_PASSPHRASE"

for var in $_CRITICAS; do
    val="${!var:-}"
    if [ -z "$val" ]; then
        falha "${var}: não definido — verifique o .env."
    elif printf '%s' "$val" | grep -q 'change_me_'; then
        falha "${var}: ainda contém o valor padrão 'change_me_*'. Troque por um segredo real."
    else
        ok "${var}: definido."
    fi
done

# Comprimento mínimo de JWT_SECRET
if [ -n "${JWT_SECRET:-}" ] && ! printf '%s' "$JWT_SECRET" | grep -q 'change_me_'; then
    JWT_LEN="$(printf '%s' "$JWT_SECRET" | wc -c | tr -d ' ')"
    if [ "$JWT_LEN" -lt 32 ]; then
        falha "JWT_SECRET tem apenas ${JWT_LEN} caracteres — mínimo 32 (use openssl rand -hex 32)."
    else
        ok "JWT_SECRET: comprimento ${JWT_LEN} >= 32 caracteres."
    fi
fi

# Comprimento mínimo de BACKUP_PASSPHRASE
if [ -n "${BACKUP_PASSPHRASE:-}" ] && ! printf '%s' "$BACKUP_PASSPHRASE" | grep -q 'change_me_'; then
    BP_LEN="$(printf '%s' "$BACKUP_PASSPHRASE" | wc -c | tr -d ' ')"
    if [ "$BP_LEN" -lt 16 ]; then
        falha "BACKUP_PASSPHRASE tem apenas ${BP_LEN} caracteres — mínimo 16."
    else
        ok "BACKUP_PASSPHRASE: comprimento ${BP_LEN} >= 16 caracteres."
    fi
fi

# Consistência: POSTGRES_PASSWORD deve coincidir com a senha em ADMIN_DATABASE_URL
if [ -n "${POSTGRES_PASSWORD:-}" ] && [ -n "${ADMIN_DATABASE_URL:-}" ]; then
    if ! printf '%s' "$POSTGRES_PASSWORD" | grep -q 'change_me_'; then
        ADMIN_SENHA="$(senha_de_dsn "$ADMIN_DATABASE_URL")"
        if [ "$POSTGRES_PASSWORD" != "$ADMIN_SENHA" ]; then
            falha "POSTGRES_PASSWORD e a senha em ADMIN_DATABASE_URL são DIFERENTES."
            falha "  → POSTGRES_PASSWORD define a senha do superusuário; ADMIN_DATABASE_URL deve usá-la."
        else
            ok "POSTGRES_PASSWORD coincide com ADMIN_DATABASE_URL."
        fi
    fi
fi

# -------------------------------------------------------------------------- 4. verificações de alerta

printf '\n--- Verificações de alerta ---\n\n'

# TLS / domínio
if [ -z "${PUBLIC_DOMAIN:-}" ] || [ -z "${ACME_EMAIL:-}" ]; then
    alerta "PUBLIC_DOMAIN e/ou ACME_EMAIL não definidos → Traefik em dev-mode (sem TLS real)."
    alerta "  → Para produção: defina ambos e reinicie o proxy (docs/runbooks/deploy.md §2)."
else
    ok "TLS: PUBLIC_DOMAIN=${PUBLIC_DOMAIN}, ACME_EMAIL=${ACME_EMAIL}."
fi

# LLM
if [ -z "${LLM_API_KEY:-}" ] && [ -z "${LLM_BASE_URL:-}" ]; then
    alerta "LLM_API_KEY / LLM_BASE_URL não definidos → IA responde em template (degradação graciosa)."
else
    ok "LLM: provedor configurado."
fi

# CORS em prod
if [ "${CORS_ORIGINS:-}" = "http://localhost:3000" ]; then
    alerta "CORS_ORIGINS ainda com valor dev (localhost:3000)."
    alerta "  → Em produção: defina como a URL pública do frontend (ex.: https://seudominio.com)."
else
    ok "CORS_ORIGINS: ${CORS_ORIGINS:-<não definido>}."
fi

# Tier profundo
if [ -z "${DEEP_API_KEYS:-}" ]; then
    alerta "DEEP_API_KEYS vazio → tier profundo (/v1/consultas-lote) só acessível via break-glass."
fi

# Subnets
if [ -n "${CORE_SUBNET:-}" ] || [ -n "${CONSENT_SUBNET:-}" ]; then
    ok "Subnets customizadas: CORE=${CORE_SUBNET:-padrão}, CONSENT=${CONSENT_SUBNET:-padrão}."
fi

# -------------------------------------------------------------------------- 5. resumo

printf '\n=== Resumo ===\n'
if [ "$FALHAS" -gt 0 ]; then
    printf '%sFALHOU: %d erro(s) bloqueante(s). Corrija antes de subir a stack.%s\n' \
        "$RED" "$FALHAS" "$NC" >&2
    exit 1
elif [ "$ALERTAS" -gt 0 ]; then
    printf '%sPASSOU com %d alerta(s). Revise os avisos acima se for produção.%s\n' \
        "$GRN" "$ALERTAS" "$NC"
else
    printf '%sPASSOU. Stack pronta para subir.%s\n' "$GRN" "$NC"
fi
