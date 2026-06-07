# ADR-0028 — SICONFI/DCA: forma real confirmada no #0 (fiel-à-forma) e re-ancoragem do OndeFoi

- **Status:** aceito (forma confirmada); **1 ponto 🟡 para o dono** (re-ancoragem do OndeFoi — §5)
- **Data:** 2026-06-07
- **Relaciona:** ADR-0021 (domínio `financas`/SICONFI), ADR-0026 (contrato OndeFoi), ADR-0003
  (expand-and-contract)

## Contexto — o #0 abriu
Nesta sessão **nova**, a sonda do bilhete-ponte deu **aberto** para o egress liberado pelo dono
(modo Custom): `apidatalake.tesouro.gov.br` (SICONFI) → `HTTP/2 200`, `servicodados.ibge.gov.br`
(IBGE) → `301`, `www4.bcb.gov.br` (BCB) → `302`, **sem** `x-deny-reason`. (INEP/PNCP/DATASUS seguem
`403 host_not_allowed`.) Conforme o CLAUDE.md, **furei a fila** e rodei a validação real do SICONFI
**uma vez**, contra a DCA ao vivo, para confirmar as **três incógnitas de forma** que o ADR-0026
deixou marcadas e **promover a fixture de fiel-ao-contrato → fiel-à-forma**. Este ADR **fecha o loop
no papel**: as marcas "confirmar no #0" viram "confirmado: X".

**O que foi consultado** (ORDS REST, `…/ords/siconfi/tt/dca`): Anexo **I-C** (receitas) e Anexo
**I-E** (despesas por função), São Paulo (3550308) 2022/2024, um município pequeno (3165537/2022) para
ver **ausência** de função, e checagem de disponibilidade por exercício.

## Decisão / achados — a forma real (capturada, não suposta)

### (a) Nomes de campo reais — o mock estava errado na forma
A API devolve `{"items": [ {…} ]}` com as chaves:
`exercicio`(int), `instituicao`(str), `cod_ibge`(**int**), `uf`(str), `anexo`(str), `rotulo`(str),
`coluna`(str), `cod_conta`(str), `conta`(str), `valor`(**float/num**), `populacao`(int).

Diferenças vs. o mock antigo (`{cod_ibge: "str", conta, valor: "str"}`):
- **`cod_ibge` é inteiro** e **`valor` é numérico** (o mock usava strings).
- existe a dimensão **`coluna`** — cada `conta` aparece em **várias colunas**: em I-C
  (`Receitas Brutas Realizadas`, `Deduções - FUNDEB`, `Outras Deduções da Receita`); em I-E
  (`Despesas Empenhadas`, `Despesas Liquidadas`, `Despesas Pagas`, `Inscrição de Restos a Pagar
  Processados/Não Processados`). **Somar sem filtrar a coluna dobra/contamina o valor.**
- a `conta` é **prefixada por código** (`1.7.0.0.00.0.0 - Transferências Correntes`) e há uma
  **homônima intra-orçamentária** (`7.7.0.0.00.0.0 - Transferências Correntes`, `cod_conta` com
  prefixo `RI…` vs. `RO…`). Casar pelo **`cod_conta`** (`RO1.7.0.0.00.0.0`), nunca pelo texto.

**Correção aplicada já** (o #0 revelou bugs no indicador `financas.transferencias.correntes` que
existia em grau-contrato): o `AdaptadorSiconfi` agora casa `cod_conta == "RO1.7.0.0.00.0.0"` **e**
`coluna == "Receitas Brutas Realizadas"`, com `cast` de `cod_ibge`→str e `valor`→float; o contrato de
borda passou a exigir `coluna` e `cod_conta`. (Antes, o filtro por texto `"Transferências Correntes"`
**não casava nenhuma linha real** e a soma por todas as colunas misturaria deduções.)

### (b) Classificação de função = os membros da dimensão — vocabulário DA FONTE
No **Anexo I-E**, a **função vive no texto `conta`** no formato **`"NN - Nome"`** (ex.: `10 - Saúde`,
`12 - Educação`, `08 - Assistência Social`); o `cod_conta` é **constante `"TotalDespesas"`** para todo
o demonstrativo por função — logo a detecção de função **parseia `conta`, não `cod_conta`**.
Hierarquia: **função** = `"NN - Nome"`; **subfunção** = `"NN.NNN - Nome"` (ex.: `10.301 - Atenção
Básica`); agregados = `"Total Geral da Despesa por Função"`, `"Despesas Exceto Intraorçamentárias"`,
`"Despesas Intraorçamentárias"`, `"FUxx - Demais Subfunções"`.

A classificação é a **Portaria MOG nº 42/1999** (vocabulário oficial), **como o SICONFI a rotula**.
Promovido ao código em `FUNCOES_SICONFI` (`código→nome`, 28 funções) + helpers `e_funcao`/
`parse_funcao`, **travados por teste contra a fixture real** (todo membro detectado no dado real está
no vocabulário, com o mesmo nome). **24 funções observadas** nas capturas (cada município reporta só
as que executou — SP/2022 teve 22; o pequeno teve 16, incluindo `20 - Agricultura`, ausente em SP).
Isto substitui o vocabulário **provisório do mock** (texto livre: "Saúde", "Assistência social",
"Urbanismo"…) pela classificação real (com código).

### (c) Função ausente vs. retida → conjunto válido **`{valor, sem_cobertura}`** confirmado
**Não há nenhum campo de sigilo/supressão** na resposta (nenhuma chave `sigil*`/`supr*`), **nenhum
`valor` nulo**, nenhum marcador-sentinela. Uma função que o município **não executou simplesmente não
tem linha** (ausência = linha inexistente, não um flag). Isto **confirma a hipótese forte do
ADR-0026**: orçamento por função é agregado público **sem PII** → o conjunto válido do `exe_estado` do
OndeFoi é **`{valor, sem_cobertura}`**, **sem `suprimido`**. O cadeado `"suprimido"` só se renderiza
com **base legal de sigilo nomeada** — que aqui não existe. (`sem_cobertura` = função sem linha no DCA.)

## §5 — Achado que muda o produto: **"recebido por função" não existe na fonte** 🟡
O ADR-0026 modelou o OndeFoi como **recebido × executado _por função_**. A validação real mostra que
**a fonte não classifica receita/transferência por função**: as transferências estão no **Anexo I-C**
(receita, taxonomia `1.7… Transferências Correntes`), **não** por função orçamentária; a classificação
funcional (`10 - Saúde`…) só existe nas **despesas** (Anexo I-E), com as colunas
**Empenhado → Liquidado → Pago**. Logo **não há um "recebido da função Saúde"** a cruzar.

**Re-ancoragem proposta (default, source-grounded), para o dono confirmar:** medir, _por função_,
**Liquidado / Empenhado** — "do que a prefeitura **empenhou** (comprometeu) em cada área, quanto
**liquidou** (de fato virou despesa)?". Encaixa melhor na honestidade do produto ("executar ≠
entregar" ↔ "empenhar ≠ liquidar") e é **inteiramente sustentado pela fonte**. A camada pura do
OndeFoi (`onde_foi.calcular`: denominador de base única, banda como sinal de atenção) **permanece** —
muda só o **significado das colunas** (recebido→empenhado, exe→liquidado) e a moldura do selo. (Em
municípios grandes Liquidado/Empenhado é alto, 92–99% em SP/2024 — a banda "merece a pergunta"
disparará mais por **município/área** com baixa liquidação do que como regra; calibrar com dado real.)

> Por que isto **não** travou a fatia: é um 🟡 de produto (reversível, direcional). Pré-autorização do
> dono (#5) → seguir o default e registrar. **A tela do OndeFoi segue em grau-demo** até o dono
> referendar a moldura; a forma e o vocabulário (este ADR) já estão presos.

## Outros achados de operação (para a esteira viva)
- **Disponibilidade por exercício (em 2026-06):** 2022/2023/2024 completos; **2025 recém-aberto**
  (prazo legal da DCA = 31/mai do ano seguinte). A esteira deve **derivar o exercício mais recente**
  da própria resposta (`exercicio`) e o frescor do `meta`, **nunca hardcoded** (a `META_DEMO` atual diz
  "exercício 2025"/atraso 75 — coerente por ora, mas precisa virar derivado na esteira viva).
- **Busca nacional é paginada:** sem `id_ente`, a API devolve todos os entes do exercício com
  paginação (`offset`/`hasMore`); o `FetcherSiconfiHTTP` foi corrigido para **codificar os espaços** do
  `no_anexo` (o URL com espaço cru quebrava o `urlopen`), mas a **paginação nacional** fica para a
  fatia da esteira viva (`run_siconfi` por função).

## Consequências
- **ADR-0026 atualizado de fato:** as três marcas "confirmar no #0" estão **confirmadas** aqui
  (a/b/c). O conjunto `{valor, sem_cobertura}` é definitivo; o vocabulário de função é o da fonte.
- **Fixtures promovidas a fiel-à-forma** (`tests/fixtures/siconfi.py`: `AMOSTRA` = I-C real;
  `AMOSTRA_FUNCOES` = I-E real, valores reais de SP/2024) — exercitam a forma no CI por fetcher fake,
  no mesmo nível de CAGED/ESTBAN.
- **Próxima fatia (pós-este ADR):** esteira viva de **despesa por função** — `AdaptadorSiconfi`
  (Anexo I-E) → prata por função (parse de `conta`, coluna Empenhado/Liquidado) → **função como
  dimensão no ouro** (ADR-0026 §"Modelagem") → `run_siconfi`/Dagster, com paginação nacional. A tela
  do OndeFoi migra de demo→vivo **após** o dono referendar a re-ancoragem (§5).
- **Gate do #0 — resolvido para SICONFI/IBGE/BCB.** A 1ª busca real foi exercida; a fixture virou
  contrato gravado. Resta o lote INEP/PNCP/DATASUS (ainda `403`) na Lista de desbloqueio.
