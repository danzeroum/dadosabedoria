# ADR-0015 — Provedor de LLM real para o narrador (DeepSeek/Ollama via API OpenAI-compatível)

- **Status:** aceito
- **Data:** 2026-06-05

## Contexto
A IA ancorada (ADR-0011) nasceu com um `NarradorTemplate` determinístico e um ponto de plugue para
um provedor real. O responsável escolheu o provedor: **DeepSeek ou Ollama**. Ambos expõem uma API
**OpenAI-compatível** (`/v1/chat/completions`), então um único adaptador serve aos dois — a escolha
vira **config**, sem mudança de código.

## Decisão
- **`NarradorLLM`** chama um endpoint OpenAI-compatível, configurado por ambiente (invariante 8):
  - DeepSeek (hospedado): `LLM_BASE_URL=https://api.deepseek.com/v1`, `LLM_MODEL=deepseek-chat`,
    `LLM_API_KEY=…`;
  - Ollama (local): `LLM_BASE_URL=http://ollama:11434/v1`, `LLM_MODEL=llama3.1` (sem key).
- **Seleção por config:** `narrador_padrao()` devolve o `NarradorLLM` só se `LLM_BASE_URL` **e**
  `LLM_MODEL` estiverem definidos; senão, o `NarradorTemplate`. Logo **dev/CI rodam offline e
  determinísticos** (sem rede, sem provedor) — os testes existentes seguem verdes.
- **Invariante 3 preservado por construção** (não por confiança no modelo):
  1. **Contexto fechado** — o LLM recebe SÓ os fatos recuperados (sem DB, sem PII; a IA roda como
     `role_analitica`). Citações continuam **determinísticas** (montadas pelo serviço, não pelo LLM).
  2. **Ancoragem numérica** — `validar_numeros_ancorados`: todo número (≥ 2 díg.) da resposta tem de
     constar dos fatos enviados; se o LLM cuspir um número inventado, **cai para o template**.
  3. **Prompt estrito + `temperature=0`** — proíbe conhecimento externo, cálculo de números,
     causalidade e projeção; manda citar a fonte e abster-se sem dados.
- **Degradação graciosa:** falha/timeout do provedor ou resposta não-ancorada ⇒ `NarradorTemplate`
  (o cidadão sempre recebe a descrição ancorada). O `narrador` na resposta identifica quem narrou
  (model card: `template-v1` ou `llm:<modelo>`).
- **Privacidade do provedor:** o que sai da máquina são apenas **agregados públicos** (a IA não lê
  `app`/PII). Ainda assim, com **DeepSeek** o dado público sai para um terceiro; com **Ollama** nada
  sai. Recomenda-se Ollama onde a saída de dados for indesejada (VPS/soberania).
- `narrar()` passou a ser **assíncrono** (chamada HTTP); `httpx` virou dependência de runtime.

## Consequências / a evoluir
- Trocar de provedor (ou desligar o LLM) é só variável de ambiente — zero deploy de código.
- A ancoragem numérica é conservadora (normaliza separador de milhar/decimal; ignora 1 dígito):
  pode, no limite, rejeitar uma resposta boa e cair para o template — falha **para o lado seguro**.
- Evolução: streaming de tokens, cache por pergunta (economia/§6), tratamento de rate-limit/custo do
  DeepSeek, e prompts/few-shot por domínio. A fronteira do serviço `ai` (processo isolado) já existe.
