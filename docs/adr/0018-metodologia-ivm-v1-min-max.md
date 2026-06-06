# ADR-0018 — Metodologia do IVM: manter min-max v1; z-score é a calibração v2 (adiada)

- **Status:** aceito (decisão do dono: **adiar o z-score**)
- **Data:** 2026-06-06

## Contexto
O IVM (ADR-0008) normaliza os subíndices de emprego e finanças por **min-max** por período e pondera
**50/50** (`versao_metodologia = "v1"`). O roadmap marcava como 🟡 a calibração da metodologia, com
*default proposto* de **z-score**. Era preciso decidir se trocar agora.

## Decisão
**Manter o min-max v1 agora; o z-score fica como calibração v2, adiada até haver cobertura nacional.**

Por quê (honestidade técnica — o ativo do projeto é a confiança):
- O IVM é uma **view materializada recomputada** do zero a cada refresh — não há série histórica "v1"
  a preservar; trocar a fórmula só muda os números atuais (não é questão de expand-and-contract).
- Com o seed atual (1–2 municípios), o **z-score é degenerado**: 1 ponto → desvio-padrão 0; 2 pontos →
  ambos caem na faixa central. O min-max v1 é justamente **robusto a poucos pontos**
  (`max == min → 50`).
- Trocar agora **não traz ganho estatístico** (sem dado nacional para calibrar) e **desestabilizaria**
  o produto-âncora (inclusive quebraria o cenário de "vermelho" do teste de consumo de alertas).
- Os **pesos 50/50** seguem como escolha explícita e versionada; recalibração de pesos também espera
  dado real.

## Quando fazer a v2 (gatilho)
Ao entrar **cobertura nacional** (Onda 2 — muitos municípios por período), implementar a v2:
- z-score por período (`stddev_pop`), com **guarda de `stddev = 0 → 50`**, reescalado para 0–100
  (ex.: `clamp(z, -3, 3)` → linear), invertendo o sinal (maior emprego/crédito = menor
  vulnerabilidade), pesos calibráveis;
- nova migração que redefine a MV e **bumpa `versao_metodologia` para "v2"** — a API já expõe
  `versao_metodologia` no `meta`, então o cliente vê a mudança;
- comparar v1×v2 num período com dado real antes de promover (não enshrine sem evidência).

## Consequências
- Nenhuma mudança de número agora; o produto-âncora segue estável e a decisão fica **registrada**
  (não é uma lacuna esquecida). O item 🟡 do roadmap é resolvido por esta decisão.
