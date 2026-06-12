# ADR-0037 — Avaliação dos Gatilhos de Infra (§1.1): estado atual e limiares

**Data:** 2026-06-12  
**Status:** Aceito  
**Contexto:** Roadmap `[ ] 🔵 Avaliar gatilhos §1.1` — primeira revisão formal.

---

## Contexto

O documento técnico §1.1 define três gatilhos que, quando atingidos, disparam a migração da
infra de desenvolvimento (VPS única, docker-compose) para camadas gerenciadas:

| Gatilho | Limiar | Ação |
|---|---|---|
| Postgres | > 60 GB **ou** p95 de consulta > 300 ms | Migrar para instância gerenciada (RDS/Supabase) |
| MinIO | > 200 GB | Migrar para S3 gerenciado |
| Observabilidade | Qualquer métrica de latência/erro crônica | Externalizar stack OTel com retenção curta |

---

## Estado em 2026-06-12

### Banco de dados (PostgreSQL 16 / PostGIS)

| Métrica | Valor atual | Limiar | Estado |
|---|---|---|---|
| Tamanho total do banco | < 200 MB (seed + SICONFI 2024 + PNCP jan/2024 + IBGE 5.571 municípios) | 60 GB | 🟢 muito abaixo |
| Linhas em `valor` | ~15 k (seed + ingestão real PNCP/SICONFI) | — | 🟢 |
| Linhas em `execucao_funcao` | ~83 k (SICONFI 2024 nacional, 5.541 municípios × ~15 funções) | — | 🟢 |
| p95 das consultas de leitura | < 10 ms (IVM, OndeFoi, panorama — medido em dev) | 300 ms | 🟢 muito abaixo |
| Conexões simultâneas | < 20 (só dev; prod estimada < 100 antes do gatilho) | — | 🟢 |

**Conclusão:** nenhum indicador se aproxima do limiar. O banco cabe confortavelmente
na VPS padrão (4 vCPU / 16 GB RAM recomendada). O tuning em `infra/postgres/postgresql.conf`
(shared_buffers, effective_cache_size, work_mem) já está calibrado para esse perfil (ADR-0005).

### Armazenamento de objetos (MinIO)

| Métrica | Valor atual | Limiar | Estado |
|---|---|---|---|
| Dados em bronze | < 1 MB (testes; ingestão nacional não executada neste contêiner) | 200 GB | 🟢 muito abaixo |

**Conclusão:** MinIO permanece adequado. O limiar de 200 GB está a décadas de distância
com as fontes atuais (SICONFI/PNCP ~MB/ano; DATASUS ~5 GB/mês quando desbloqueado; CAGED ~500 MB/mês).
Revisitar quando o backfill histórico do DATASUS estiver em andamento.

### Observabilidade

A stack de observabilidade (Prometheus + Loki + Grafana + Tempo) é **opt-in** via profile
`observability` (ADR-0005). Em produção, uma instância separada da VPS principal é
recomendada para evitar co-residência de carga pesada com a API.

**Conclusão:** sem necessidade de externalizar neste momento. O OTel Collector leve com
retenção curta (padrão em `infra/otel-collector/`) já está configurado para produção básica.

---

## Decisão

**Nenhum gatilho foi atingido.** A infra atual (VPS 4 vCPU / 16 GB RAM, docker-compose)
é suficiente para todo o volume esperado até a chegada de dados reais das fontes bloqueadas
(DATASUS, CAGED, ESTBAN).

**Quando revisar:**
1. Após a primeira ingestão nacional do DATASUS (SIH, ~5 GB/mês × 27 UFs) — verificar
   tamanho do bronze e tempo de consulta do IVM com dado real.
2. Após o backfill histórico de 3+ anos de CAGED (estimativa: ~500 MB/mês × 36 meses = ~18 GB
   de bronze; banco muito menor após agregação).
3. Se o p95 de alguma rota monitorada ultrapassar 100 ms com dado real (metade do limiar —
   sinal precoce que justifica investigação antes de chegar a 300 ms).

**Sem migração de banco nem de storage. Sem externalização de observabilidade.**

---

## Consequências

- O item `[ ] 🔵 Avaliar gatilhos §1.1` do roadmap é **concluído** com este ADR.
- Próxima revisão: junto com o primeiro deploy de dados reais (DATASUS ou CAGED na VPS).
- O script `scripts/preflight.sh` documenta e valida a configuração mínima de produção
  (parte do hardening de deploy adicionado nesta mesma fatia — ADR-0037).
