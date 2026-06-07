# ADR-0026 — OndeFoi (TRANSP-06): contrato do indicador de execução por função (denominador, exe_estado, honestidade)

- **Status:** aceito
- **Data:** 2026-06-07

## Contexto
O OndeFoi responde "a transferência da União virou serviço no meu município?" cruzando **recebido ×
execução** por função orçamentária (SICONFI/DCA). O protótipo do handoff de design revelou uma
armadilha de confiança: o **% geral** era calculado sobre a base das funções com execução divulgada,
mas o "recebido" exibido era o **total** — então `executado / recebido_exibido` **não batia** com a
pílula `%`. Para um produto de transparência, esse é o número que um jornalista refaz à mão; se não
fecha, a confiança vai junto. Por isso, **antes** de implementar a camada de dado/API (a) e a tela
(b), travamos aqui o **contrato do número**. (O `data.js` do protótipo já segue este contrato; este
ADR o eleva a decisão de produto, espelhada no backend.)

## Decisão

### 1. Denominador — comparar o comparável, base única (o número que sustenta o produto)
- **Unidade de comparação = por função:** recurso da função × **despesa liquidada** da função. Nunca
  misturar receita total com despesa por função.
- **Agregado:** `pct = executado / recebido_base`, onde
  - `executado` (numerador) = Σ despesa liquidada das funções **divulgadas** (`exe_estado = "valor"`);
  - `recebido_base` (denominador) = Σ recebido **das mesmas** funções divulgadas;
  - **a % e o "recebido" exibido usam a MESMA base** (`recebido_base`), nunca o total.
- **A parcela fora do cálculo é explícita, nunca silenciosa.** O endpoint expõe `recebido_total`,
  `recebido_base` e `recebido_fora_base` (= total − base; soma do protegido + sem cobertura + não
  detalhado por função). Ex.: *"executou 76% do que foi divulgado por função (R$ 19,8 de R$ 26 bi);
  R$ 15,2 bi não detalhados/protegidos — **fora deste %**."*

### 2. Supressão aditiva — `exe_estado` (mesmo padrão do ADR-0025/H-04; expand-and-contract, ADR-0003)
Por função: `exe: number | null` + **campo irmão** `exe_estado: "valor" | "suprimido" |
"sem_cobertura"`. Campo **separado** (não sobrecarrega o valor) e **aditivo** (não quebra consumidor):
- `"valor"` — valor divulgado → entra no numerador **e** no denominador;
- `"suprimido"` — valor **retido por sigilo** (proteção real, ex.: k-anon sobre PII) → só contexto, **fora** do %;
- `"sem_cobertura"` — sem dado para a célula → **fora** do %.

**Validade por indicador — fronteira semântica (refino 2026-06-07):** o primitivo `EstadoSupressao`
mantém os **três** estados, mas **quais são válidos é por indicador**. `"suprimido"` é um **cadeado de
privacidade**: só se aplica onde há PII por baixo e a fonte **realmente retém por sigilo, com a base
legal nomeada**. Execução orçamentária por função é **agregado público sem PII** (São Paulo gastar em
Saúde não protege ninguém): pôr o cadeado aí seria *honesty-theater* — sugerir uma proteção que não
existe, o oposto do que o produto vende. **Hipótese forte do OndeFoi (confirmar no #0 como o SICONFI
sinaliza função faltante e por quê): conjunto válido = `{valor, sem_cobertura}`, sem `"suprimido"`.**
Regra de contrato: só renderizar o cadeado `"suprimido"` quando houver **base legal de sigilo
nomeada**; senão, função faltante é `"sem_cobertura"`.

**Padrão transversal (implementar uma vez, servir os dois):** o mesmo contrato `*_estado` resolve a
supressão honesta do **IVM** — `/v1/ivm` ganha `v_saude_estado` distinguindo *null-por-supressão*
(k-anon sobre PII, ADR-0002 — aí `"suprimido"` é **legítimo**) de *null-por-cobertura*. ADR-0025 já
tornou `v_saude` aditivo; `v_saude_estado` é o complemento honesto, e o `EstadoSupressao` da tela é um
componente só (três estados), compartilhado IVM↔OndeFoi — muda só a **validade por indicador**.

### 3. Honestidade no contrato — executado ≠ virou serviço
- `meta.metodologia`: **"execução orçamentária (empenho/liquidação), não serviço entregue."** A
  pergunta-título é **enquadrada**, nunca respondida como equivalência.
- **Banda = sinal de atenção, não veredito.** `alta` (≥ 80% — *"executou quase tudo; confira se virou
  serviço"*), `parcial` (≥ 55%), `baixa` (< 55% — *"**merece a pergunta**"*). Subexecução **nunca**
  insinua corrupção: uma razão baixa pode ser *timing*/lag, não desvio — contextualizada por período
  e defasagem. (Evita o falso-positivo que assombra o Farol de Conluio; o ativo é a confiança.)

### 4. Frescor derivado do `meta`, não hardcoded (D-1 do handoff)
`meta` carrega fonte / lag / período; o selo do OndeFoi **deriva "exercício X"** de `meta.periodo`
(DCA é **anual** e defasada ~75 dias) — sem cheiro de tempo real.

## Forma do contrato — `GET /v1/onde-foi/{codigo_ibge}` (`/v1`, aditivo, snake_case)
```jsonc
{
  "codigo_ibge": "3550308", "nome": "São Paulo", "uf": "SP",
  "recebido_total": 78900, "recebido_base": 54900, "recebido_fora_base": 24000,
  "executado": 41730, "pct": 76, "banda": "parcial",
  "funcoes": [
    { "funcao": "Saúde", "recebido": 18200, "exe": 16930, "exe_estado": "valor",         "pct": 93 },
    { "funcao": "Saneamento", "recebido": 3200, "exe": null, "exe_estado": "sem_cobertura", "pct": null },
    { "funcao": "Cultura", "recebido": 1500, "exe": null, "exe_estado": "sem_cobertura",  "pct": null }
    // (orçamento público sem PII → sem "suprimido"; cadeado só com base legal de sigilo nomeada)
  ],
  "meta": {
    "metodologia": "Execução orçamentária (empenho/liquidação) por função, no exercício — NÃO serviço entregue.",
    "versao_metodologia": "v1", "periodo": "2025-01-01", "periodo_rotulo": "exercício 2025",
    "atraso_dias": 75,
    "fontes": [ { "sigla": "SICONFI", "orgao": "Tesouro Nacional/STN", "ate": "2025 (anual)" } ]
  }
}
```

## Modelagem de (a): função como dimensão — estrutura vs membros (refino 2026-06-07)
Função orçamentária **recorre** no pilar de orçamento (TRANSP-03/04/05 + despesa futura) → a direção é
**função como dimensão canônica no ouro** (reutilizável/navegável, no espírito `domínio→subdomínio→
indicador`), não codificada só no indicador do OndeFoi. Fronteira de verdade dentro da dimensão:
- **Estrutura = verdade-de-contrato (commitável já):** existe uma dimensão `função` e indicadores a
  referenciam. Instanciada **mínima e promovível** sobre a fixture; *fallback* indicador-codificado se
  nem a forma mínima couber numa fatia reset-safe (promove-se pós-#0).
- **Membros = forma-verdade (só no #0):** a **lista de funções + a classificação** são provisórias
  (seed do mock) e devem derivar da **classificação da própria fonte (SICONFI)** quando o #0 abrir —
  nunca do mock (senão recria "fixture-como-verdade" no nível do **vocabulário**). Vocabulário
  finalizado em expand-and-contract após a validação real.

## Consequências
- A camada (a) e a tela (b) implementam **este** contrato; a tela monta sobre `SeloConfianca`,
  `EstadoSupressao` e `SuperficieAgir` (handoff), compartilhados com o IVM — não forka.
- **Pipeline vivo:** `run_siconfi` (DCA por função: recebido = transferências; executado = despesa
  liquidada) → `executar_*` (bronze→prata→ouro + supressão + linhagem) → schedule Dagster anual.
- **Gate-free, mas grau-demo até o #0.** SICONFI é fonte aberta, porém o allowlist
  (`apidatalake.tesouro.gov.br`) é do dono do ambiente; constrói-se na **fixture fiel ao DCA**, e o
  **OndeFoi é a 1ª validação real** quando o #0 abrir — aí a fixture vira contrato gravado.
