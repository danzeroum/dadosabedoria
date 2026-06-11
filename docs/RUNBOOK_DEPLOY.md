# RUNBOOK_DEPLOY — DadoSabedoria em produção

Domínio alvo: `dadosabedoria.buildtovalue.cloud`  
Stack: Docker Compose + Traefik v3 (ACME/TLS) + PostgreSQL 16 + Redis + Next.js

---

## Pré-requisitos

- VPS com Ubuntu 24.04 LTS (mínimo 2 vCPU, 4 GB RAM, 40 GB disco).
- Docker Engine ≥ 27 + Docker Compose plugin (`docker compose`).
- DNS A/AAAA apontando `dadosabedoria.buildtovalue.cloud` → IP da VPS.
- Portas 80 e 443 abertas no firewall (UFW ou grupo de segurança).
- Acesso SSH com sudo (ou usuário no grupo `docker`).

---

## 1. Clonar o repositório

```bash
git clone https://github.com/danzeroum/dadosabedoria.git
cd dadosabedoria
```

---

## 2. Criar o arquivo `.env`

```bash
cp .env.example .env   # se existir; senão crie manualmente (veja abaixo)
```

### Variáveis obrigatórias

| Variável | Descrição |
|---|---|
| `POSTGRES_PASSWORD` | Senha do superusuário Postgres. Gere: `openssl rand -hex 32` |
| `ADMIN_DATABASE_URL` | `postgresql+asyncpg://postgres:<POSTGRES_PASSWORD>@db/dadosabedoria` |
| `DATABASE_URL` | `postgresql+asyncpg://role_analitica:<SENHA_ROLE>@db/dadosabedoria` |
| `CONSENT_DATABASE_URL` | `postgresql+asyncpg://role_consentimento:<SENHA>@db/dadosabedoria` |
| `REDIS_URL` | `redis://redis:6379/0` |
| `JWT_SECRET` | Segredo HMAC para JWT. Gere: `openssl rand -hex 32` |
| `APP_FIELD_KEY` | Chave de campo cifrado (AES). Gere: `openssl rand -base64 32` |
| `CORS_ORIGINS` | `https://dadosabedoria.buildtovalue.cloud` |
| `PUBLIC_DOMAIN` | `dadosabedoria.buildtovalue.cloud` |
| `ACME_EMAIL` | Email para notificações de renovação do Let's Encrypt |

### Variáveis opcionais (deixar vazias ativa modo degradado)

| Variável | Descrição |
|---|---|
| `LLM_API_KEY` | Chave do provedor OpenAI-compatível. Vazio → modo template (sem IA). |
| `LLM_BASE_URL` | Endpoint base do provedor (ex.: `https://api.deepseek.com/v1`). |
| `LLM_MODEL` | Nome do modelo (ex.: `deepseek-chat`). |
| `DEEP_API_KEYS` | Chaves de acesso à API deep (ex.: análise avançada). |
| `S3_ENDPOINT` | Endpoint MinIO (profile `ingestion`). |
| `S3_KEY` | Usuário MinIO. |
| `S3_SECRET` | Senha MinIO. |
| `S3_BUCKET_BRONZE` | Bucket para camada bronze. |

### Variáveis de integração externa (somente em variável de ambiente, NUNCA no repo)

| Variável | Descrição |
|---|---|
| `DATAJUD_API_KEY` | Chave da API do DATAJUD (CNJ). Obter via portal do CNJ. **Nunca commitar.** |

Para exportar sem persistir no `.env`:

```bash
export DATAJUD_API_KEY="<valor>"
```

---

## 3. Ajustar CORS Origins para prod

Em `.env`:

```
CORS_ORIGINS=https://dadosabedoria.buildtovalue.cloud
```

Em `infra/traefik/dynamic/middlewares.yml`, substituir a lista `accessControlAllowOriginList`:

```yaml
accessControlAllowOriginList:
  - "https://dadosabedoria.buildtovalue.cloud"
```

---

## 4. Subir a stack mínima (API + frontend + proxy)

```bash
docker compose --profile app up -d
```

Isso sobe: `proxy` (Traefik), `db`, `redis`, `migrator` (one-shot), `api`, `web`.

Aguarde o migrator terminar:

```bash
docker compose logs -f migrator
# "Applied N migration(s)" → pode seguir
```

Verifique o certificado TLS:

```bash
curl -sv https://dadosabedoria.buildtovalue.cloud/health
# Deve retornar {"status":"ok"} com certificado Let's Encrypt válido
```

---

## 5. Subir a ingestão (opcional — dados vivos)

```bash
docker compose --profile ingestion up -d
```

Sobe MinIO, worker e orchestrator (Dagster). A UI do Dagster fica disponível em
`http://<IP_VPS>:3000` **somente pela rede interna/VPN** (não exposta pelo Traefik).

---

## 6. Subir a IA ancorada (opcional)

Defina `LLM_API_KEY`, `LLM_BASE_URL` e `LLM_MODEL` no `.env`, então:

```bash
docker compose --profile ai up -d
```

Se `LLM_API_KEY` estiver vazio, o serviço responde com templates determinísticos (sem IA
generativa). O produto `/perguntar` funciona, mas com respostas pré-formatadas.

---

## 7. Subir o consentimento (opcional — PII/auth do cidadão)

```bash
docker compose --profile consent up -d
```

---

## Traefik / TLS

- Config estática: `infra/traefik/traefik.yml` — lida na inicialização; mudanças exigem
  `docker compose restart proxy`.
- Config dinâmica: `infra/traefik/dynamic/middlewares.yml` — hot-reload sem restart.
- Certificados ACME: volume Docker `acme` (`/acme/acme.json`) — sobrevive a restarts.
- HTTP → HTTPS: redirect permanente definido no entrypoint `web` (traefik.yml).
- HSTS: `stsSeconds: 31536000` ativo no middleware `dsab-headers`.

---

## Dev local (sem TLS)

Para desenvolvimento local sem Traefik:

```bash
# API
cd api && uvicorn app.main:app --reload --port 8000

# Frontend
cd web && npm run dev
```

Ou, para usar docker-compose localmente ignorando o redirect HTTPS:

```bash
# Override temporário: desabilita o redirect no entrypoint web
docker compose -f docker-compose.yml -f docker-compose.dev.yml up
```

(Criar `docker-compose.dev.yml` com o bloco proxy sem redirections — não commitado; é local.)

---

## Renovação de certificados

O Let's Encrypt renova automaticamente via Traefik (tlsChallenge). Nenhuma ação manual
necessária. Para verificar:

```bash
docker compose exec proxy traefik healthcheck
```

---

## Backup

```bash
# Banco de dados
docker compose exec db pg_dump -U postgres dadosabedoria | gzip > backup_$(date +%Y%m%d).sql.gz

# Certificados ACME
docker run --rm -v dadosabedoria_acme:/data alpine tar czf - /data > acme_$(date +%Y%m%d).tar.gz
```

---

## Contrato de variáveis de ambiente — produção

Checklist antes do go-live:

- [ ] `POSTGRES_PASSWORD` gerado com `openssl rand -hex 32`
- [ ] `JWT_SECRET` gerado com `openssl rand -hex 32`
- [ ] `APP_FIELD_KEY` gerado com `openssl rand -base64 32`
- [ ] `ACME_EMAIL` válido (recebe alertas de expiração do cert)
- [ ] `PUBLIC_DOMAIN` = `dadosabedoria.buildtovalue.cloud`
- [ ] `CORS_ORIGINS` = `https://dadosabedoria.buildtovalue.cloud`
- [ ] DNS A record apontando para o IP da VPS
- [ ] Portas 80 e 443 abertas
- [ ] `.env` **fora do controle de versão** (`.gitignore`)
- [ ] `DATAJUD_API_KEY` exportado via variável de ambiente, **não** no `.env` commitado

---

## CAGED go-live (ingestão de emprego municipal)

### Pré-requisito: allowlist FTP

O worker precisa de acesso FTP à rede do PDET/MTE. Liberar no firewall da VPS:

- Host: `ftp.mtps.gov.br`
- Porta: 21 (controle FTP) + range de portas passivas (tipicamente 1024–65535 saindo do servidor)

Verifique com:

```bash
nc -zv ftp.mtps.gov.br 21
# Connection to ftp.mtps.gov.br 21 port [tcp/ftp] succeeded! → porta aberta
```

### Diagnóstico com volume montado

Execute o diagnóstico no worker (salva a amostra diretamente no host via volume):

```bash
docker compose --profile ingestion run --rm \
  -v /opt/btv/dadosabedoria/api/tests/fixtures:/app/tests/fixtures \
  worker python scripts/diagnostico_caged.py
```

O script imprime a forma do arquivo (colunas, encoding, shape) e salva
`api/tests/fixtures/caged_amostra_real.csv` no host via volume montado.

### Commit da amostra

Após o diagnóstico (ou com a fixture já commitada):

```bash
cd /opt/btv/dadosabedoria
git add api/tests/fixtures/caged_amostra_real.csv
git commit -m 'fixture: amostra real CAGEDMOV <competencia>'
git push
```

### Ingestão FTP na VPS (em tmux)

```bash
tmux new -s caged
docker compose --profile ingestion run --rm worker \
  python -m app.ingestao.run_caged <ano> <mes>
# ex.: python -m app.ingestao.run_caged 2026 4
```

O processo pode demorar alguns minutos (arquivo ~300 MB comprimido). O tmux garante que o
processo não seja interrompido por desconexão SSH.

### Verificação de cobertura

```bash
curl https://dadosabedoria.buildtovalue.cloud/v1/cobertura/caged | jq .
# Esperado: { "n_municipios": ~5500, "demo": false, "competencia": "202604" }
```

`demo: false` confirma que o dado é real (não fixture/seed).

### Spot-check de município

```bash
# São Paulo (IBGE 3550308 → 6 dígitos: 355030)
curl https://dadosabedoria.buildtovalue.cloud/v1/pulso-produtivo/3550308 | jq .
# Deve retornar saldo_caged e salario_medio_admissao com valores reais
```

---

## OIDC (futuro — 🔴 gate externo)

O provedor OIDC ainda não está configurado. Quando disponível:

| Variável | Descrição |
|---|---|
| `OIDC_ISSUER` | URL do issuer (ex.: `https://accounts.google.com`) |
| `OIDC_CLIENT_ID` | Client ID obtido no console do provedor |
| `OIDC_CLIENT_SECRET` | Segredo do cliente — **nunca commitado** |

Referência: Lista de desbloqueio no `docs/roadmap.md`.
