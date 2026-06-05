# ADR-0008 — IVM (Índice de Vulnerabilidade Municipal) como view materializada

- **Status:** aceito (metodologia **v1** — especificação proposta para um ponto antes
  subespecificado; sinalizada ao responsável do produto)
- **Data:** 2026-06-05

## Contexto
O IVM é a "vista de topo que agrega os domínios" (esquema §7): TRANSP-01, o coração do mapa
semafórico do Valor Triplo. A doc pede "subíndices de emprego e finanças, normalizados e
ponderados, como view materializada" (§15, §10), mas **não fixa** a fórmula. Conforme o briefing,
proponho uma especificação concreta e sinalizo.

## Decisão — IVM v1 (transparente e evolutivo)
- **Grão:** município × período (mensal). Considera só municípios com **ambos** os indicadores
  (`trabalho.emprego.saldo_caged` e `credito.operacoes.saldo_total`) no período, não suprimidos.
- **Normalização:** min-max por período (0–100) de cada componente.
- **Subíndices de vulnerabilidade** (maior = mais vulnerável): `v_emprego = 100 − norm(saldo)`,
  `v_financas = 100 − norm(crédito)` (mais emprego/crédito ⇒ menos vulnerável).
- **IVM = 0,5·v_emprego + 0,5·v_financas** (pesos iguais), em 0–100.
- **Semáforo:** `< 33` verde, `33–66` amarelo, `> 66` vermelho.
- Município único no período (min=max) → componente neutro (50).

## Implementação
- **MATERIALIZED VIEW `ivm_municipio`** (migração 0010, aditiva): window functions por período,
  `round` nos resultados. Pré-computado → **O(1) na leitura** (invariante 6).
- **Owner = `role_analitica`** → o runtime pode `REFRESH MATERIALIZED VIEW CONCURRENTLY` (índice
  único exigido) sem superusuário. `refrescar_ivm()` roda em AUTOCOMMIT e **invalida o cache**.
  Chamado após o seed e após cada ingestão (CAGED/ESTBAN, CLI e Dagster).
- **API:** `GET /v1/ivm?periodo=YYYY-MM` (mapa; padrão = período mais recente) e
  `GET /v1/ivm/{codigo_ibge}` (série/drill-down), com `meta` (metodologia, versão, componentes,
  faixas do semáforo).

## Consequências / a evoluir (sem quebrar — `versao_metodologia`)
- Pesos, normalização (z-score), **per capita** (já temos `populacao`), mais domínios (saúde, água)
  e suavização temporal são refinamentos de uma **v2** — a série v1 é preservada.
- Cobertura: validado contra Postgres real (2 municípios → verde/vermelho; semáforo; drill-down).
