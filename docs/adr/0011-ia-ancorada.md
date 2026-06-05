# ADR-0011 — IA ancorada (provider-agnóstica, com narrador-stub)

- **Status:** aceito
- **Data:** 2026-06-05

## Contexto
Invariante 3: a IA só afirma o que recupera do repositório, cita a fonte por afirmação e abstém-se
sem dado — nunca inventa número nem afirma causalidade (§9). O provedor de LLM ainda não foi
escolhido; a doc já prevê o LLM **atrás de um adaptador** (trocável).

## Decisão
- **Recuperação ancorada** (`app/ia/recuperacao.py`): reusa o serviço de leitura (camada pública,
  não-pessoal). A IA narra **apenas** sobre o `ContextoIA` recuperado.
- **Guardrails** (`app/ia/guardrails.py`): entrada tratada como não confiável (sanitização +
  truncamento); resolução de escopo (qual indicador) por correspondência com o catálogo, com
  **abstenção** quando não há match.
- **Narrador = adaptador** (`app/ia/narrador.py`): `NarradorTemplate` (padrão) é determinístico —
  templa só os valores recuperados e cita a fonte, **não inventa número e não afirma causalidade,
  por construção**. `NarradorLLM` é o ponto de plugue do provedor real (atrás de `LLM_API_KEY` +
  config); nos testes/CI usa-se o template.
- **Serviço** (`app/ia/servico.py`): orquestra guardrails → recuperação → (abster | narrar), e toda
  resposta carrega **citações** (fonte, indicador, período, método, lag) e **ressalvas** (sem
  causalidade; lag/confiabilidade; cautela em comparações). `revisao_humana=true` para indicadores
  de **origem sensível** (human-in-the-loop).
- **Isolamento (invariante 2):** roda como `role_analitica` — **sem** credencial do schema `app`
  (verificado pela checagem estática do compose: o serviço `ai` não recebe `CONSENT_*`/`APP_*`).
- **Arquitetura:** IA montada no monólito (`POST /v1/ia/perguntar`) para o v1 (monólito modular); o
  serviço `ai` (`python -m app.ia.server`, profile `ai`) reusa o mesmo router e é a **fronteira de
  extração** quando bater a dor (§1.1). `model card` = campo `narrador` na resposta.

## Consequências / a evoluir
- A IA é útil e **invariant-safe** já com o template (respostas 100% ancoradas e citadas).
- **Plugar o provedor real** (Anthropic/OpenAI-compatível) é só implementar `NarradorLLM` atrás do
  adaptador + `LLM_API_KEY` (decisão do responsável: provedor + chave/orçamento). O prompt do LLM
  recebe o mesmo `ContextoIA` e a instrução estrita de só usar os valores dados e abster-se.
- Próximo: interpretação de linguagem natural mais rica (hoje é correspondência simples), e
  frontend (caixa de pergunta) consumindo `/v1/ia/perguntar`.
