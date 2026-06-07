# ADR-0029 — OndeFoi re-ancorado: Liquidado ÷ Empenhado por função (esteira viva)

- **Status:** aceito (default em MODO DEV) · **aguarda referendo do dono** (re-enquadramento do produto)
- **Data:** 2026-06-07
- **Relaciona:** ADR-0026 (contrato OndeFoi), ADR-0028 (#0 — forma real), ADR-0002 (privacidade),
  ADR-0003 (expand-and-contract)

## Contexto
O #0 (ADR-0028) mostrou que **"recebido por função" não existe na fonte**: o SICONFI classifica
**despesa** por função (Anexo I-E: Empenhado→Liquidado→Pago), mas **não** a receita/transferência
(Anexo I-C, sem recorte por função). O modelo original do OndeFoi (recebido × executado por função,
ADR-0026) é, portanto, **impossível de sustentar com o dado real**. O dono, em **MODO DEV** (autonomia
ampliada, sessão 2026-06-07), autorizou **seguir no default sem esperar** e gravar a decisão aqui.

## Decisão
**Re-ancorar o OndeFoi em Liquidado ÷ Empenhado por função** — *"do que a prefeitura **empenhou**
(comprometeu) em cada área, quanto **liquidou** (de fato virou despesa)?"*. É **inteiramente
sustentado pela fonte** e preserva a honestidade do produto:
- **executar ≠ serviço entregue** (empenho/liquidação não é serviço prestado) — moldura, não veredito;
- **empenhar ≠ liquidar** mapeia o "merece a pergunta": liquidação baixa sobre o empenhado **merece a
  pergunta** (pode ser *timing*/lag, não desvio — nunca insinua corrupção; ADR-0026 §3 mantido);
- a **camada pura** `onde_foi.calcular` (denominador de base única, banda de atenção, parcela fora
  explícita) **permanece intacta** — muda só o **significado das colunas** (recebido→empenhado,
  exe→liquidado) e a **pergunta-título** da tela.

**Reversível (expand-and-contract):** se o dono redirecionar o enquadramento, troca-se a leitura sobre
a mesma fato; nada do dado bruto se perde. **A tela do OndeFoi segue em grau-demo até o referendo.**

## Modelagem — função como **dimensão** (não indicador codificado)
Execução por função é **agregado público sem PII** (ADR-0028: a fonte não tem campo de sigilo;
`exe_estado` válido = `{valor, sem_cobertura}`). Logo:
- **Fato dedicada `execucao_funcao`** (migração 0017): `território × período × função` com `empenhado`
  e `liquidado`. **Não é a fato `valor`** e **não passa pela supressão k-anon** (não há PII por baixo)
  — o guard do único ponto de escrita protege `valor`/`.aplicar(`, intactos. A **função é dimensão**
  (colunas `funcao_cod`/`funcao_nome`), no espírito ADR-0026 §Modelagem — não 48 indicadores
  codificados que poluiriam o panorama.
- **Vocabulário = Portaria MOG 42/1999, da fonte** (Anexo I-E; confirmado no #0 — `FUNCOES_SICONFI`):
  função de 1º nível `"NN - Nome"`; subfunção (`"NN.NNN - "`), totais e agregados ficam fora.

## Esteira viva (esta fatia)
`FetcherSiconfiFuncoesHTTP` (Anexo I-E) → `AdaptadorSiconfi.transformar_prata_funcoes`/`agregar_funcoes`
(Empenhado/Liquidado por função, puro, testado contra fixture **fiel-à-forma**) →
`executar_siconfi_funcoes` (bronze→fato `execucao_funcao`, idempotente, + linhagem). Exercício mais
recente disponível = **2024** (não o "2025" do mock — ADR-0028); o frescor deriva do dado, nunca
hardcoded. **Próximas fatias:** `run_siconfi_funcoes` (CLI) + **Dagster** (schedule anual) → endpoint
`/v1/onde-foi/{ibge}` lendo a fato viva → **reconciliar a copy/pergunta-título** da tela ao novo
enquadramento (sai do grau-demo após o referendo).

## Consequências
- O produto-âncora OndeFoi passa a ter **dado vivo defensável** (não mais um modelo impossível).
- Em municípios grandes, Liquidado/Empenhado é alto (SP/2024 ≈ 96%) — a banda "merece a pergunta"
  dispara mais por **área/município** específico do que como regra; **calibrar com dado real** (a banda
  do ADR-0026 segue como ponto de partida, versionável).
- **Pendência do dono:** referendar o re-enquadramento (`docs/PENDENCIAS_DO_DONO.md`). Sem ação, o dev
  segue no default; a tela não "congela" o enquadramento até o aval.
