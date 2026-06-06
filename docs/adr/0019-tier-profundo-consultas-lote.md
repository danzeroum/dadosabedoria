# ADR-0019 — Tier profundo (open-core pago): consultas em lote + auth por chave de API

- **Status:** aceito
- **Data:** 2026-06-06

## Contexto
O modelo **Open-Core Cívico** prevê duas faixas: leitura pública (grátis, rate-limited) e uma
**camada profunda** (autenticada/cobrada). A `seguranca.py` já antecipava "autenticação do tier
profundo em fatia futura". Faltava a primeira capacidade profunda e o gate de tier.

## Decisão
- **`POST /v1/consultas-lote`** (aditivo, §7): várias consultas de valores num só request. **Reusa o
  Facade público** por item — é o **mesmo acervo público** (`role_analitica`, **sem PII**); o que se
  cobra é a **conveniência/escala**, não acesso a dado privado (coerente com o open-core).
- **Auth por chave de API:** `Authorization: Bearer <chave>` ou `X-API-Key`. O servidor guarda **só o
  SHA-256** das chaves emitidas (`DEEP_API_KEYS`, CSV) — **nunca a chave bruta** (invariante 8: env, e
  ainda assim só o hash). 401 se ausente/ inválida. A dependency devolve um **id curto** (12 hex do
  hash) p/ correlação/log, sem o segredo.
- **Lote resiliente e limitado:** teto de 50 consultas; uma consulta com erro (indicador inexistente,
  período inválido) vira `erro` **naquele item**, sem derrubar o lote (4xx só para auth/má-formação).
- **Tier:** a chave **é** o gate do tier (nível de app). A leitura pública segue rate-limited no
  gateway; um entrypoint autenticado com rate-limit próprio no Traefik é refino de infra futuro.

## Consequências / a evoluir
- Primeira fatia monetizável no ar, sem afrouxar isolamento (a IA e o público continuam iguais;
  OpenAPI atualizado; testes cobrem 401 ausente/ inválido, lote misto ok+erro, e `X-API-Key`).
- **Emissão/revogação de chaves** por cliente (tabela + ferramenta de admin) é o próximo passo — o
  hash-em-env é o MVP. Depois: cotas/billing, OAuth2 client-credentials, e uma consulta em lote
  **otimizada** (uma query só, em vez do laço por item) quando o volume pedir (economia, §6).
