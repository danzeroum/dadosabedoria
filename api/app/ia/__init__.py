"""Serviço de IA ancorada (§9, invariante 3).

Responde SÓ sobre o que recupera do repositório canônico (camada pública/não-pessoal), com citação
por afirmação e abstenção honesta; nunca inventa número nem afirma causalidade. Roda como
``role_analitica`` — **sem** credencial do schema ``app``.

Geração atrás de um adaptador (``narrador``): hoje um template determinístico; o provedor de LLM
real é um plugue de configuração (``LLM_API_KEY``), trocável sem mexer no serviço.
"""
