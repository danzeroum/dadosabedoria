# ADR-0004 — Seeds passam pelo mesmo caminho de supressão da ingestão

- **Status:** aceito
- **Data:** 2026-06-05

## Contexto
A regra de supressão por k-anonimato (invariante 1) precisa existir em **um** lugar e ser aplicada
**antes** de gravar. O esquema canônico (§4.3) mostra `INSERT INTO valor` cru de exemplo — o que
**conflita** com a exigência de que o endpoint de leitura nasça idêntico ao que a ingestão vai
alimentar. (Conflito sinalizado; o canônico prevalece nos invariantes, mas a forma do seed segue a
decisão do produto.)

## Decisão
- A regra vive só em `app/ingestao/supressao.py`; o **único ponto de chamada** é
  `app/ingestao/ouro.py::escrever_ouro`, que aplica a supressão, grava `valor` (célula suprimida →
  `valor=NULL, suprimido=true`) e registra `linhagem` (proveniência).
- O **seed** (`app/seed`) faz upsert das dimensões (governança, não-fatos) e empurra os **fatos**
  pelo `escrever_ouro` — nada de INSERT cru em `valor`. Os INSERTs do §4.3 viram **fixtures** de
  teste (saída esperada).
- Inclui de propósito uma célula sub-limiar de origem sensível (Campinas) para exercer a supressão
  ponta a ponta já no seed.

## Enforcement (quality gate)
- **Single-call-site test:** `.aplicar(` e a escrita na fato (`t_valor`) só aparecem em
  `ouro.py`/`supressao.py`; nenhum `INSERT INTO valor` cru no código.
- **Linhagem por lote:** o banco semeado tem uma linha de `linhagem` por lote — prova que o caminho
  ouro rodou (um INSERT cru deixaria `linhagem` vazia).
- Cobertura **100%** em `supressao.py` e `ouro.py`.

## Semânticas resolvidas (doc silenciosa → fail-closed)
- `n_minimo = 0` → supressão desligada (saldo CAGED: `n_amostra=None` é normal).
- `n_minimo > 0` e `n_amostra is None` → **suprime** (não dá para provar k-anonimato).
- origem sensível → piso `max(n_minimo, 5)`. Fronteira `<` (n == limiar é mantido).
