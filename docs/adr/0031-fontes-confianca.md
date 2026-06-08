# ADR-0031 — "Fontes & confiança": proveniência consolidada (`/v1/fontes` + `/fontes`)

- **Status:** aceito (default MODO DEV; #5 pré-autorizado — valor não-gated sobre o acervo existente).
- **Data:** 2026-06-08
- **Contexto:** o ativo do produto é a **confiança** (privacidade, proveniência, qualidade). A
  proveniência já existia **por número** (envelope `meta` em cada resposta), mas **não havia uma
  vista consolidada** — nenhuma página respondia, de uma vez, "de onde vêm os dados, com que licença,
  com que atraso, e como vocês protegem?". Os produtos por valor restantes estão **gated** (hosts
  INEP/PNCP/DATASUS em 403; OndeFoi aguarda o referendo do dono). O #5 pré-autoriza valor sobre o que
  já está desbloqueado — e a transparência das fontes é valor **não-gated**, sobre dado que já existe.

## Decisão

Expor a **proveniência consolidada** como fatia vertical até a tela:

- **`GET /v1/fontes`** — lista as fontes do acervo direto da tabela `fonte`/`base_legal` (órgão,
  licença, cadência, lag, uso comercial/redistribuição, base legal LGPD) + **cobertura** (domínios e
  nº de indicadores **públicos**, via outer join). A confiança como **fato verificável**, não texto
  fixo: se o acervo muda, a página muda. Aditivo ao contrato `/v1` (invariante 4) — só adiciona
  `FonteAcervoOut`/`RespostaFontes`/`/v1/fontes`, **zero deleção** no `openapi.yaml`.
- **Tela `/fontes`** — as fontes (prova) **e** o modelo de privacidade/proveniência em linguagem
  simples (promessa): supressão antes de gravar, isolamento de PII, proveniência sempre, IA ancorada.
  Server-side, sem JS; na porta de entrada (link no rodapé da home).

## Consequências

- **Honesto sobre cobertura vazia:** uma fonte conectada sem indicador público aparece com
  `dominios=[]` ("ainda sem indicador no acervo") — não some. (Detalhe técnico: `array_agg(DISTINCT
  dominio)` + filtro do `NULL` na facade — sem bind de NULL sem-tipo no SQL; `count(DISTINCT)` já
  ignora NULL.)
- **Escala sozinho:** cada nova fonte/indicador entra na página sem código. **Reversível** (1 rota +
  1 tela + 1 lib de leitura; nada destrutivo).
- Coberto pelo screenshot/axe (`/fontes` em `captura.mjs`) e por integração (`test_fontes_api.py`:
  licença/base legal presentes, cobertura por domínio, caso vazio, ordenação por nome).
