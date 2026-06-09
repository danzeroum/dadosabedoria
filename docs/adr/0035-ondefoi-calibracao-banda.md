# ADR-0035 — OndeFoi: calibração dos limiares de banda com dado real

**Data:** 2026-06-09  
**Status:** Aceito  
**Contexto:** PASSO 3 da sessão 2026-06-09 — calibrar os limiares de banda (80/55) com a distribuição
real de 5.541 municípios (ingestão nacional 2024, 83.444 linhas)

---

## Contexto

O ADR-0029 previa "calibrar os limiares com dado real após a primeira ingestão nacional". Com a
ingestão de 2024 gravada (`execucao_funcao`, 83.444 linhas, 5.541 municípios), foi possível medir a
distribuição real dos percentuais de execução (liquidado/empenhado por função).

---

## Distribuição real (2024, n=5.541)

```sql
SELECT
    count(*) FILTER (WHERE pct >= 80)  AS old_alta,   -- limiar antigo
    count(*) FILTER (WHERE pct >= 55 AND pct < 80) AS old_parcial,
    count(*) FILTER (WHERE pct < 55)  AS old_baixa,
    percentile_cont(0.05) WITHIN GROUP (ORDER BY pct) AS p5,
    percentile_cont(0.10) WITHIN GROUP (ORDER BY pct) AS p10,
    percentile_cont(0.50) WITHIN GROUP (ORDER BY pct) AS p50
FROM (
    SELECT round(sum(liquidado)::numeric / nullif(sum(empenhado), 0) * 100) AS pct
    FROM execucao_funcao ef
    JOIN territorio t ON t.id = ef.territorio_id
    WHERE ef.periodo = '2024-01-01' AND t.nivel = 'municipio'
    GROUP BY ef.territorio_id
) s;
```

| Métrica | Valor |
|---------|-------|
| old_alta (≥80%) | 5.515 (99,5%) |
| old_parcial (55–79%) | 21 (0,4%) |
| old_baixa (<55%) | 5 (0,1%) |
| p5 | 89% |
| p10 | 92% |
| p50 | 98% |

**Conclusão:** com os limiares 80/55, 99,5% dos municípios caem em "alta" — a banda não diferencia.
A mediana é 98%, o p10 é 92%, o p5 é 89%. A distribuição está fortemente concentrada no extremo alto.

---

## Decisão

**Novos limiares: 95/90**

| Banda | Critério | n (2024) | % |
|-------|----------|----------|---|
| alta | ≥ 95% | 4.504 | 81,3% |
| parcial | 90–94% | 742 | 13,4% |
| baixa | < 90% | 295 | 5,3% |

### Princípio de calibração

O objetivo da banda é sinalizar **quem destoa**, não pintar todos de verde. Os limiares calibrados
distribuem os municípios em três faixas com diferenciação real:
- "alta" — execução acima de 95% (típico brasileiro, bom executor)
- "parcial" — entre 90–94% (abaixo da mediana, merece atenção mas não é alarme)
- "baixa" — abaixo de 90% (outlier de baixa execução, merece a pergunta)

### Por que 95/90 e não percentis exatos?

1. **Legibilidade**: números redondos têm interpretação imediata ("liquidou 95% do empenhado").
2. **Estabilidade**: percentis mudam a cada ingestão; limiares redondos são documentáveis em ADR.
3. **Conservadorismo**: p5=89%, p10=92% — o limiar "baixa" em 90% cobre os ~5% de outliers reais.

### Honestidade (ADR-0026 mantido)

A banda continua sendo **sinal de atenção**, não veredito. O comentário da tela permanece:
*"do que foi empenhado (comprometido), quanto foi liquidado (virou despesa de fato)?"*.

---

## Consequências

- `banda()` em `app/produtos/onde_foi.py` atualizada: 95/90 (era 80/55).
- Testes unitários `test_banda_limiares` atualizados para os novos limiares.
- Dado demo (DEMO_MUNICIPIOS) tem pcts fictícios (50–88%) — todos caem em "baixa" com os novos
  limiares. Isso é esperado e reflete que o dado demo **não representa a distribuição real**; os
  testes de contrato (base-única, empenhado_fora_base) continuam válidos.
- Re-calibrar a cada ingestão anual: verificar se os limiares seguem diferenciando ~80/15/5%.
- 1.792 municípios com pct ≥ 100% (sobre-execução vs. empenhado) classificam como "alta". Isso é
  correto: sobre-execução não é anomalia no orçamento público (suplementações ao longo do exercício).

---

## Comparação antes/depois (SP/Saúde/2024 — dado real)

| Métrica | Valor real | Banda antiga | Banda nova |
|---------|-----------|-------------|-----------|
| SP pct (all funcs) | ≈ 96% | alta | alta ✓ |
| Rio pct (all funcs) | depende do real | parcial/alta | conforme 95/90 |

> Nota: SP real (2024) tem pct ≈ 96% (21,9 bi / 22,7 bi ≈ 96%) → "alta" com os novos limiares ✓.
> O dado demo de SP tem pct=88 (fictício) → "baixa" nos novos limiares — demo foi desenhado para
> testar o contrato, não para ser fiel à distribuição real.
