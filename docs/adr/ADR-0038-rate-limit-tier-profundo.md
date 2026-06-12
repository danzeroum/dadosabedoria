# ADR-0038 — Rate-Limiting Fixed-Window por Chave de API (Tier Profundo)

**Data:** 2026-06-12  
**Status:** Aceito  
**Contexto:** Roadmap Onda 2D — "Cotas/billing + rate-limit autenticado no gateway + consulta-lote
otimizada: próximos" (mencionado após a entrega da camada profunda paga, PR #132).

---

## Contexto

O endpoint `POST /v1/consultas-lote` já tinha autenticação por chave de API (ADR-0019/0020), mas
sem qualquer controle de volume de requisições. Um cliente com chave válida poderia enviar requisições
ilimitadas, impactando a disponibilidade para outros clientes e impossibilitando qualquer modelo de
billing baseado em uso.

---

## Decisão

Implementar **rate-limiting por chave de API** usando **fixed-window counter no Redis**:

| Dimensão | Decisão | Razão |
|---|---|---|
| Algoritmo | Fixed-window | Simples, O(1) no Redis, boa UX (janela previsível) |
| Janela | 1 hora | Granularidade adequada para billing mensal; suficientemente curta para evitar burst |
| Limite padrão | 1.000 req/h | Generoso para uso legítimo de API; configurável via `RATE_LIMIT_PROFUNDO` |
| Backend | Redis (mesmo do cache) | Já disponível na stack, sem infra nova |
| Chave Redis | `rl:hora:{cliente}:{YYYYMMDDH}` | Isola por cliente e janela; TTL 1h |
| Degradação | Graceful (permite se Redis offline) | Disponibilidade > controle em falha de infra |

### Alternativas consideradas

- **Sliding window log** (sorted set): mais preciso, mas mais memória e latência por requisição.
- **Token bucket**: permite burst controlado; mais complexo de implementar corretamente.
- **Rate-limit no Traefik (gateway)**: possível, mas duplicaria a lógica e não teria visibilidade
  do `cliente` (identificador semântico pós-autenticação). Fica como camada adicional no futuro
  (e.g., proteção antes da auth).

### Cabeçalhos de resposta

Seguem o padrão de facto da indústria (GitHub/Stripe/etc.):

```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 742
X-RateLimit-Reset: 1749747600   # Unix timestamp da próxima janela
Retry-After: 3542               # Só em resposta 429
```

---

## Consequências

- **Positivo:** protege a infraestrutura de abuso; estabelece a base para billing por uso; UX
  previsível (clientes sabem quando podem voltar).
- **Positivo:** `RATE_LIMIT_PROFUNDO` em env → sem hardcode; ajustável por cliente (futuro:
  limites por chave individualmente no banco).
- **Neutro:** algoritmo fixed-window tem o efeito "double-burst" na virada de janela (ex.: 1000
  req ao final da hora N + 1000 req no início da hora N+1 = 2000 req em ~1 min). Aceitável
  neste estágio; sliding window ou token bucket mitigam se virar problema.
- **Futuro:** billing mensal pode agregar contagens horárias do Redis antes do TTL (ou logar
  eventos de billing em tabela separada para reconciliação).
- **Futuro:** limites individuais por chave (tabela `chave_api` já existe) — hoje todos os
  clientes compartilham o mesmo `RATE_LIMIT_PROFUNDO`.
