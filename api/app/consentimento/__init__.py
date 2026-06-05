"""Serviço ISOLADO de consentimento (schema ``app``) — runtime de PII (§6, §8.1).

Único componente com acesso ao schema ``app``, via ``role_consentimento`` em rede isolada
(``net_consentimento``), com ``CONSENT_DATABASE_URL`` / ``APP_FIELD_KEY``. Implementa o ciclo LGPD:
consentir (assinatura de alerta + condição sensível cifrada) → acessar → revogar → eliminar (Art.
18), com trilha de auditoria. A api/worker/ai **não** acessam este schema (invariante 2).
"""
