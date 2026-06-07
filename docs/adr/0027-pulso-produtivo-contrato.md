# ADR-0027 — Pulso Produtivo (TRAB-01): contrato do saldo de emprego formal (nível, momento, honestidade)

- **Status:** aceito
- **Data:** 2026-06-07

## Contexto

O Pulso Produtivo responde **"como está o pulso do emprego formal no meu município?"** sobre o sinal
que já estava no acervo: o **saldo do Novo CAGED** (admissões − desligamentos com carteira), por
município/mês, servido pela API genérica em `/v1/valores`. O pivô do roadmap (2026-06-06) pede
**produto por valor até a tela** sobre o que a fonte já desbloqueou — o saldo CAGED é o primeiro
candidato (dado real, sem rede nova, reexecutável).

Um saldo mensal é um número **traiçoeiro** para um produto: é um **fluxo volátil e sazonal**. Uma
única leitura, ou um agregado mal-escolhido, vira veredito indevido ("o emprego despencou") ou
falso alívio ("está criando vagas"). Como no OndeFoi (ADR-0026), travamos aqui o **contrato do
número** — o que é nível, o que é momento, o que é contexto — antes da tela, para que o produto
**conte a verdade, não um susto**.

## Decisão

### 1. Pergunta e sinal — emprego **formal**, fluxo com sinal

O sinal é o `saldo` mensal do Novo CAGED. O **sinal importa**: positivo = criou mais do que destruiu
vagas formais no mês; negativo = o contrário. A unidade é **contagem líquida** (não R$, não taxa).

### 2. Nível — a **batida atual** (sinal do saldo do último mês)

`pulso ∈ {aquecido, estável, esfriando}` = sinal do `saldo_mes` (o mês mais recente). É a "batida"
do pulso — a leitura corrente, **não** um agregado que pode mascarar o presente. (Campinas no seed:
acumulado +100, mas a batida atual é negativa → `esfriando`; o agregado não esconde a batida.)

### 3. Momento — a **tendência** (mês vs. mês anterior)

`tendencia ∈ {melhorando, estável, piorando}` = sinal de `saldo_mes − saldo_mes_anterior`
(`null` com 1 só mês — não se inventa momento). Captura a nuance honesta que um único rótulo perde:
**"ainda perde vagas, mas a um ritmo melhor que o mês passado"** (SP no seed: `-9100 > -15400` ⇒
`esfriando` **e** `melhorando` — desacelerando a perda). Nível e momento juntos contam o que um só
não conta.

### 4. Janela = **contexto explícito**, nunca veredito

`saldo_acumulado` (soma da janela), `meses_positivos`/`meses_negativos` e a **série inteira** vão na
resposta. Uma janela curta pode ser puxada por um único mês — então a volatilidade fica **à vista**,
não resumida num número que engana. O acumulado é rotulado como contexto, não como nota.

### 5. **Sem cadeado de privacidade** — só `valor` (refino do ADR-0026)

Diferente da saúde (SIH, `origem_sensivel`), o saldo CAGED é **agregado público sem PII**
(`n_minimo=0`, `origem_sensivel=false`) → **nunca suprime**. O Pulso **não** usa o estado
`"suprimido"`: todo mês divulgado é `valor`. Não se finge proteção que não há — mesma fronteira
semântica "validade por indicador" que o ADR-0026 fixou para o OndeFoi.

### 6. **Fluxo, não estoque** — comparar o comparável

O saldo é um **fluxo** (vagas criadas/perdidas), **não** normalizado ao **estoque** local de
empregos (que não temos no acervo). Logo, ele compara melhor **no tempo dentro do município** do que
**entre municípios** de portes diferentes (a magnitude de São Paulo e de Ribeirão das Neves não é
comparável de cara). A `nota` do produto diz isso explicitamente.

### 7. Honestidade — `nota` + proveniência do banco

A resposta carrega uma `nota` fixa: emprego **formal** (carteira) — **não** capta informal/autônomo;
fluxo volátil/sazonal — saldo negativo **merece a pergunta**, não é diagnóstico. A `meta` de
proveniência (fonte "Novo CAGED", `lag_tipico_dias`, licença, metodologia) vem do **banco** (via o
mesmo Repository de `/v1/valores`), **não** hardcoded no produto.

### 8. Onde vive (camadas)

- **`app/produtos/pulso_produtivo.py`** — contrato **puro** (dataclasses + `classificar_pulso` +
  `classificar_tendencia` + `calcular`), TDD, sem rede/DB (regra pura testada a 100%).
- **`app/produtos/facade.py`** — `PulsoProdutivoFacade` **reusa** `RepositorioIndicadores`
  (`obter_territorio` + `meta_indicador` + `listar_valores`) + cache de leitura; não duplica consulta.
- **`app/produtos/rotas.py`** — `GET /v1/pulso-produtivo/{codigo_ibge}` (aditivo, `/v1`); `404` para
  território inexistente **ou** sem saldo CAGED (sem dado do produto, honesto).
- **`web/app/pulso/[codigo]`** — a tela: selo de nível + tendência + série a partir do **zero** +
  contexto + a nota; acessível (cor nunca sozinha, ADR-0009).

## Consequências

- O produto nasce **honesto e reexecutável**: lê dado real, não inventa relação, e mostra a
  volatilidade em vez de escondê-la. A tela é certificada no **screenshot de CI**.
- O primitivo `EstadoSupressao` (IVM/OndeFoi) **não** é usado aqui — e isso é correto: o Pulso não
  tem o que proteger. A ausência do cadeado é uma decisão, não um esquecimento.
- Quando houver **estoque** de empregos (ou recorte per capita), abre-se uma v2 com normalização que
  permita comparação **entre** municípios — versionada, sem quebrar este contrato (expand-and-contract).
- O mesmo molde (módulo puro → facade reusando o Repository → rota `/v1` → tela) serve os próximos
  produtos sobre indicadores já no ar (compras, finanças, educação) sem tocar no núcleo.

## Alternativas consideradas

- **Nível pelo acumulado da janela** (em vez da batida do mês): rejeitado — mascara o presente
  (o caso Campinas), justamente o que um "pulso" não pode fazer.
- **Dead-zone para `estável`** (faixa morta perto de zero): rejeitado por ora — exigiria um limiar
  arbitrário; com a magnitude e a série à vista, o sinal puro é mais honesto. Reabrível com dado real.
- **`meta` de proveniência fixa no produto**: rejeitado — a proveniência tem de vir da fonte (banco),
  ou mente quando a fonte mudar (invariante 5).
