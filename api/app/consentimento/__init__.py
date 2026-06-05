"""Fronteira do serviço ISOLADO de consentimento (schema ``app``) — runtime NÃO construído aqui.

Nesta fatia entregamos apenas o isolamento (schema ``app``, role ``role_consentimento``, grants,
RLS, rede) e o teste de permissão negada. O caminho de escrita de PII (assinatura de alerta,
cifragem de campo, trilha de auditoria) vem em fatia futura — e é o ÚNICO componente que recebe
``CONSENT_DATABASE_URL`` / ``APP_FIELD_KEY``.
"""
