# ADR-0025 — IVM multidomínio: incorpora saúde; min-max mantido; z-score é a v2 (cobertura nacional)

- **Status:** aceito
- **Data:** 2026-06-06

## Contexto
A fundação acumulou **largura** (financas/SICONFI, educacao/INEP, compras/PNCP, saude/DATASUS no ar
pelo `ModuloDominio`), mas nenhuma fatia chegou à **tela** e o produto-âncora **TRANSP-01 (IVM)**
seguia com 2 subíndices (emprego + finanças, ADR-0008/0018). Decisão do dono: **fechar o 1º ciclo
ponta-a-ponta** — IVM completo (multidomínio) → mapa semafórico (primeira tela) — e daí mudar a lente
de "empurrar fonte" para "puxar produto até a tela".

## Decisão
**Elevar o IVM de 2 para 3 subíndices, somando saúde, mantendo a normalização min-max** (migração
0015, `versao_metodologia = "v1.1"`):
- **Subíndices:** emprego (saldo CAGED) e finanças (crédito ESTBAN) **invertidos** (maior valor →
  menor vulnerabilidade); **saúde** = internações respiratórias (SIH/DATASUS) **não invertida**
  (mais internações → mais vulnerável). Polaridade por subíndice, explícita.
- **Peso dinâmico:** IVM = média dos subíndices **disponíveis**. Emprego+crédito são o núcleo
  (exigidos, como na v1); **saúde é opcional** (entra no período onde há dado não suprimido). Assim,
  município sem saúde não é diluído por um neutro nem sai do índice — e a **supressão k-anon** da
  saúde é respeitada (célula suprimida não entra).
- **Aditivo (expand-and-contract):** mantém `v_emprego`/`v_financas`/`ivm`/`semaforo`; **acrescenta
  `v_saude`** (pode ser `null`) na MV, na API (`/v1/ivm`, `/v1/ivm/{ibge}`, `/v1/mapa/ivm`) e no
  `meta.componentes`. A MV é recomputada do zero (não há série a preservar — ADR-0018).

## Por que NÃO trocar para z-score agora (honestidade — o ativo é a confiança)
O dono pediu "z-score v2". Mas a **pré-condição da v2 (ADR-0018/pré-autorização #1) é cobertura
nacional**, e o acervo tem **poucos municípios por período**. Nesse regime:
- o z-score é **degenerado/comprimido** (2 pontos → ±0,7σ → tudo na faixa central), o que **apaga o
  contraste verde→vermelho** justamente na primeira tela que se quer acender;
- o min-max é **robusto a poucos pontos** (`max==min → 50`) e dá um mapa interpretável agora.

Portanto: **min-max na v1.1**; o **z-score continua sendo a v2**, com **gatilho objetivo = cobertura
nacional** (muitos municípios/período). Quando disparar: z-score por período (`stddev`, guarda
`stddev=0 → 50`, reescala 0–100), comparar v1×v2 com dado real antes de promover, e **bumpar
`versao_metodologia` para "v2"** (o cliente já vê a versão no `meta`).

## Consequências / a evoluir
- TRANSP-01 deixa de ser "básico": índice **multidomínio** (trabalho + finanças + saúde), pronto para
  a **primeira tela** (mapa semafórico + drill-down, próxima fatia).
- Subíndices direcionais futuros (ex.: atendimento de água do SNIS = `maior_melhor`, IDEB) entram pelo
  mesmo molde. Indicadores **neutros** já ingeridos (matrículas, transferências, valor de contratos)
  permanecem **descritivos** (servidos pela API, fora do índice) até existir recorte direcional/per
  capita — não se força total bruto num índice de vulnerabilidade (confiança).
- z-score (v2) ao atingir cobertura nacional, como acima.
