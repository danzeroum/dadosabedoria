# Runbook de Deploy — DadoSabedoria

Procedimentos para implantar e atualizar a stack na VPS. Leia do início ao fim antes
do primeiro deploy; nas atualizações rotineiras, vá direto ao §3.

---

## 0. Pre-flight (sempre, antes de qualquer `docker compose up`)

```bash
# Valida que o .env tem todos os segredos trocados e está coerente.
# Falha com mensagem descritiva se ainda houver 'change_me_*'.
bash scripts/preflight.sh

# Ou apontando para um .env específico:
bash scripts/preflight.sh /caminho/para/.env
```

**O que verifica:**
- Nenhuma variável crítica contém o placeholder `change_me_*`.
- `JWT_SECRET` tem ≥ 32 caracteres.
- `BACKUP_PASSPHRASE` tem ≥ 16 caracteres.
- `POSTGRES_PASSWORD` é consistente com a senha em `ADMIN_DATABASE_URL`.
- Alertas (não bloqueantes) para ausência de `PUBLIC_DOMAIN`/`ACME_EMAIL` (TLS inativo)
  e `LLM_API_KEY` (IA em template).

---

## 1. Primeiro deploy (VPS nova / contêiner limpo)

```bash
# 1. Clonar o repositório
git clone https://github.com/danzeroum/dadosabedoria.git
cd dadosabedoria

# 2. Criar o .env a partir do exemplo e preencher TODOS os valores
cp .env.example .env
nano .env   # troque todos os "change_me_*"

# 3. Construir as imagens
docker compose --profile app build

# 4. Subir a stack (banco, api, web, proxy)
docker compose --profile app up -d

# 5. Verificar saúde
docker compose ps
curl -s http://localhost/health | jq .
```

### Checklist do .env antes de subir

| Variável | O que colocar |
|---|---|
| `POSTGRES_PASSWORD` | senha do superusuário PostgreSQL |
| `ADMIN_DATABASE_URL` | mesma senha acima |
| `DATABASE_URL` | senha da role_analitica (definida na migração 0009) |
| `CONSENT_DATABASE_URL` | senha da role_consentimento |
| `JWT_SECRET` | string aleatória longa (≥32 bytes) |
| `CORS_ORIGINS` | URL pública do frontend (ex.: `https://seudominio.com`) |
| `BACKUP_PASSPHRASE` | passphrase longa para backup cifrado de PII |

Variáveis opcionais até ter o provedor real:
- `LLM_*` — IA roda em template sem elas
- `ACME_EMAIL` / `PUBLIC_DOMAIN` — TLS ativo só com domínio real
- `DATAJUD_API_KEY` — só para fontes restritas

---

## 2. Ativar TLS de produção (quando o domínio estiver apontado)

```bash
# No .env:
PUBLIC_DOMAIN=seudominio.com
ACME_EMAIL=seuemail@exemplo.com

# Reiniciar só o proxy para emitir o certificado Let's Encrypt
docker compose restart proxy
```

O Traefik emite o cert via TLS-ALPN-01 automaticamente ao detectar as variáveis.

---

## 3. Atualização de código (após git pull)

Fluxo normal após um PR mergeado:

```bash
# Atualizar o código
git pull origin main

# Reconstruir as imagens que mudaram (api + web)
docker compose --profile app build

# Recriar os contêineres com as novas imagens
docker compose --profile app up -d
```

Se o pull trouxer **nova migração de banco** (arquivo em `api/alembic/versions/`):

```bash
# O migrator rodará automaticamente no 'up -d' acima, pois o contêiner foi recriado.
# Verifique os logs para confirmar:
docker compose logs migrator
```

---

## 4. Ingestão de dados (popular execucao_funcao, CAGED etc.)

A ingestão usa o profile `ingestion` e requer MinIO (S3 local):

```bash
# SICONFI — execução orçamentária por função (OndeFoi), exercício 2024
docker compose --profile ingestion run --rm worker \
  python -m app.ingestao.run_siconfi_funcoes 2024

# Acompanhar em tempo real (substitua --rm por -it para ver o log)
docker compose --profile ingestion run -it worker \
  python -m app.ingestao.run_siconfi_funcoes 2024
```

A ingestão é **idempotente**: re-executar o mesmo exercício atualiza os dados sem duplicar.

---

## 5. Host compartilhado (Traefik já rodando para outro stack)

Se o VPS já tem um Traefik gerenciando outros serviços, a segunda instância falhará ao
tentar vincular as portas 80/443.

**Opção A — pular o proxy do DadoSabedoria e usar o Traefik externo:**

```bash
# Não iniciar o serviço proxy (escalar para 0)
docker compose --profile app up -d --scale proxy=0
```

Os serviços `api` e `web` já têm as labels do Traefik (`traefik.enable=true`) — o Traefik
externo as lerá automaticamente se estiver na mesma rede Docker. Conecte os serviços à rede
do Traefik externo adicionando-a ao `docker-compose.override.yml`:

```yaml
# docker-compose.override.yml (NÃO commitar no repo; é local da VPS)
services:
  api:
    networks:
      - traefik_externo   # nome da rede do Traefik existente
  web:
    networks:
      - traefik_externo

networks:
  traefik_externo:
    external: true
```

**Opção B — subnets em conflito:**

Se `172.28.0.0/16` ou `172.29.0.0/16` já estão em uso, defina no `.env`:

```bash
CORE_SUBNET=172.30.0.0/16
CONSENT_SUBNET=172.31.0.0/16
```

---

## 6. Diagnóstico rápido

```bash
# Ver estado de todos os contêineres
docker compose --profile app ps

# Logs da API (últimas 100 linhas)
docker compose logs --tail=100 api

# Logs do migrator (verificar se migrations rodaram)
docker compose logs migrator

# Testar endpoint de saúde
curl -s http://localhost/health

# Testar OndeFoi (requer execucao_funcao populada)
curl -s "http://localhost/v1/onde-foi/3550308" | jq '{nome, pct, banda}'

# Ver se a tabela tem dados
docker compose exec db psql -U postgres dadosabedoria \
  -c "SELECT COUNT(*), MAX(periodo) FROM execucao_funcao;"
```

---

## 7. Rollback

```bash
# Ver commits recentes
git log --oneline -10

# Voltar para o commit anterior (sem perder dados do banco)
git checkout <commit-hash>
docker compose --profile app build
docker compose --profile app up -d
```

Dados do banco (volume `pgdata`) **não são afetados** por rollback de código.
Se uma migration precisar ser revertida, consulte o runbook de Alembic no `api/alembic/README.md`.

---

## 8. Deploy canário (zero-downtime com rollback automático)

O script `scripts/canary_deploy.sh` implementa a estratégia blue/green via Traefik:

1. Constrói nova imagem e tagueia como `:canary`.
2. Sobe o contêiner canário na porta `127.0.0.1:8001` (sem expor externamente).
3. Aguarda warmup (15 s) e executa health checks em `/health` (até 10 tentativas × 10 s).
4. Se saudável: aguarda a janela de observação (padrão 300 s) e faz segunda verificação.
5. Se ainda saudável: **promove** — para o canário e recria o serviço de produção com a nova imagem.
6. Se falhou em qualquer etapa: **rollback automático** — para o canário, produção anterior intacta.

```bash
# Deploy com janela padrão (5 min de observação)
scripts/canary_deploy.sh

# Deploy com janela reduzida (útil em dev/homologação)
scripts/canary_deploy.sh 60
```

**Pré-requisitos:**
- `.env` validado por `scripts/preflight.sh`
- Traefik rodando e conectado à rede `net_core`
- Variáveis do `.env` exportadas no shell (ou usar `set -a; source .env; set +a`)

**Códigos de saída:** `0` = promovido com sucesso; `1` = rollback (versão anterior em produção).

> **Nota:** o WAF completo (OWASP CRS via Coraza/plugin Traefik) aguarda domínio real e plugin
> disponível. O WAF-lite atual (CSP, Permissions-Policy, body-limit 64 KB) já está ativo em
> `infra/traefik/dynamic/middlewares.yml`.
