# ADR-0030 — Produto "Comparar municípios" (decisão #5, valor sobre o desbloqueado)

- **Status:** aceito (default MODO DEV; o dono escolheu "priorizar um produto" e pré-autorizou o #5).
- **Data:** 2026-06-08
- **Contexto:** com o handoff de design reconciliado e todo o resto em gate do dono, o dono pediu para
  **priorizar um produto** (sem nomear qual). O #5 ("ordem fina de produtos") está pré-autorizado:
  o dev escolhe **por valor dentro do que a fonte já desbloqueou**. O acervo (seed) tem **dois
  municípios** (São Paulo e Campinas) com dado **cross-domínio** (trabalho, crédito, saúde, finanças,
  educação, compras) — fundo raso em municípios, mas rico em domínios.

## Decisão

Construir **"Comparar municípios"** (`/comparar?a=&b=`): dois municípios **lado a lado**, indicador por
indicador, agrupados por domínio, com **fonte e período** e **supressão honesta** (a célula protegida
mostra o cadeado, nunca o número por baixo). É o produto de **maior valor por esforço** sobre a forma
real do dado: o seed de 2 municípios serve perfeitamente a um comparativo 1-a-1.

- **Reusa a API existente** (`/v1/territorios/{ibge}/panorama` + `/v1/ivm` p/ a lista do seletor) —
  **sem novo endpoint, sem mudança de contrato/OpenAPI**. Regra pura `alinharIndicadores` testada.
- **Sem JS no cliente:** o seletor são `<Link>` que setam `?a=`/`?b=` (server components).
- **Honesto, não ranking:** a copy enquadra "descritivo — contexto para perguntar, não melhor/pior";
  unidades/períodos diferem entre indicadores. Alinha com a IA ancorada (sem veredito/causalidade).

## Consequências

- Escala sozinho: quando mais municípios entrarem no acervo (dado real, host liberado), o seletor
  cresce e o produto fica mais útil — **vivo-pronto**, sem retrabalho.
- **Reversível:** se o dono preferir priorizar outro produto do catálogo, este sai sem tocar contrato
  (é uma tela + 1 lib pura). A escolha do #5 fica registrada aqui, transparente.
- Entra na **porta de entrada** (`/`) como mais uma pergunta-produto.
