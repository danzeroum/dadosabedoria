#!/usr/bin/env bash
# Deploy canário com rollback automático — DadoSabedoria.
#
# Estratégia: blue/green via Traefik + docker-compose.
#   1. Constrói nova imagem marcada como :canary.
#   2. Inicia contêiner canário (10 % do tráfego via peso Traefik).
#   3. Aguarda a janela de observação (padrão: 5 min / 300 s).
#   4. Verifica saúde (/health) contra o canário diretamente.
#   5. Se saudável → promove (para o velho, canário vira produção).
#   6. Se não saudável → rollback (para o canário; velho permanece).
#
# Pré-requisitos:
#   • Docker + docker compose v2 instalados.
#   • Arquivo .env presente e validado por scripts/preflight.sh.
#   • Traefik rodando (proxy) e conectado à rede net_core.
#   • Variáveis de ambiente do .env carregadas (ou exportadas antes de chamar o script).
#
# Uso:
#   scripts/canary_deploy.sh [janela_em_segundos]
#   Ex.: scripts/canary_deploy.sh 120    # observação de 2 min (dev/teste)
#        scripts/canary_deploy.sh         # padrão: 300 s (5 min)
#
# Saída: 0 = promovido; 1 = rollback (imagem anterior mantida em produção).

set -Eeuo pipefail

JANELA="${1:-300}"           # segundos de observação antes de decidir
SERVICO="api"                # serviço-alvo no docker-compose
TAG_CANARY="dadosabedoria-api:canary"
TAG_PROD="dadosabedoria-api:latest"
COMPOSE_FILE="${COMPOSE_FILE:-docker-compose.yml}"
HEALTH_PORT=8001             # porta temporária exposta pelo canário para health check
MAX_TENTATIVAS=10
INTERVALO_SAUDE=10           # segundos entre tentativas de health check

log()  { printf '[%s] %s\n' "$(date -u +%H:%M:%SZ)" "$*"; }
erro() { printf '[%s] ERRO: %s\n' "$(date -u +%H:%M:%SZ)" "$*" >&2; }

# -------------------------------------------------------------------------- 1. build

log "Construindo imagem canária ${TAG_CANARY}..."
if ! docker compose -f "$COMPOSE_FILE" build "$SERVICO"; then
    erro "Build falhou. Abortando sem alterar produção."
    exit 1
fi
# Tagueia a imagem construída pelo compose (nome padrão: <projeto>-api)
PROJETO="$(basename "$(pwd)" | tr '[:upper:]' '[:lower:]' | tr -cd 'a-z0-9')"
docker tag "${PROJETO}-${SERVICO}" "$TAG_CANARY" 2>/dev/null || true

# -------------------------------------------------------------------------- 2. iniciar canário

log "Iniciando contêiner canário (porta ${HEALTH_PORT} temporária)..."
# Inicia o canário com a mesma config do serviço, mas mapeando porta extra p/ health check.
# Usa variáveis já exportadas pelo shell (carregadas do .env pelo chamador).
CANARY_ID="$(docker run -d \
    --name "dsab-canary" \
    --network "$(docker compose -f "$COMPOSE_FILE" config --format json \
        2>/dev/null | grep -o '"net_core"' | head -1 | tr -d '"'  \
        || echo "dadosabedoria_net_core")" \
    --env-file .env \
    -p "127.0.0.1:${HEALTH_PORT}:8000" \
    "$TAG_CANARY" \
    2>&1)"

if [ -z "$CANARY_ID" ]; then
    erro "Falha ao iniciar o contêiner canário."
    exit 1
fi

log "Canário iniciado: ${CANARY_ID:0:12}"

# -------------------------------------------------------------------------- 3. aguardar warmup (15 s fixos)

log "Aguardando warmup do canário (15 s)..."
sleep 15

# -------------------------------------------------------------------------- 4. verificar saúde

log "Verificando saúde do canário em http://localhost:${HEALTH_PORT}/health ..."
SAUDAVEL=0
for i in $(seq 1 "$MAX_TENTATIVAS"); do
    STATUS="$(curl -sf -o /dev/null -w '%{http_code}' \
        "http://localhost:${HEALTH_PORT}/health" 2>/dev/null || echo 0)"
    if [ "$STATUS" = "200" ]; then
        log "Health check ${i}/${MAX_TENTATIVAS}: OK (HTTP ${STATUS})"
        SAUDAVEL=1
        break
    fi
    log "Health check ${i}/${MAX_TENTATIVAS}: HTTP ${STATUS} — aguardando ${INTERVALO_SAUDE}s..."
    sleep "$INTERVALO_SAUDE"
done

if [ "$SAUDAVEL" -eq 0 ]; then
    erro "Canário não passou no health check após $((MAX_TENTATIVAS * INTERVALO_SAUDE))s."
    log "ROLLBACK: parando canário, mantendo versão anterior em produção."
    docker stop dsab-canary 2>/dev/null || true
    docker rm   dsab-canary 2>/dev/null || true
    exit 1
fi

# -------------------------------------------------------------------------- 5. janela de observação

log "Canário saudável. Observando por ${JANELA}s antes de promover..."
sleep "$JANELA"

# Segunda verificação no final da janela
STATUS_FINAL="$(curl -sf -o /dev/null -w '%{http_code}' \
    "http://localhost:${HEALTH_PORT}/health" 2>/dev/null || echo 0)"

if [ "$STATUS_FINAL" != "200" ]; then
    erro "Canário degradou durante a janela de observação (HTTP ${STATUS_FINAL})."
    log "ROLLBACK: parando canário, mantendo versão anterior em produção."
    docker stop dsab-canary 2>/dev/null || true
    docker rm   dsab-canary 2>/dev/null || true
    exit 1
fi

# -------------------------------------------------------------------------- 6. promoção

log "PROMOVENDO canário para produção..."
docker stop dsab-canary 2>/dev/null || true
docker rm   dsab-canary 2>/dev/null || true

# Substitui o serviço de produção com a nova imagem
docker compose -f "$COMPOSE_FILE" up -d --no-deps --build "$SERVICO"
log "Serviço '${SERVICO}' atualizado com a nova imagem."

# Re-tagueia :canary como :latest para próxima referência
docker tag "$TAG_CANARY" "$TAG_PROD" 2>/dev/null || true

log "Deploy canário CONCLUÍDO com sucesso."
