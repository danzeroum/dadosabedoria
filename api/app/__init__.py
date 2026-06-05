"""DadoSabedoria backend — monólito modular plugável.

Pacotes:
- ``core``: configuração, banco, cache, observabilidade, erros, registro de plugins.
- ``indicadores``: serviço de leitura (Facade + Repository) da camada analítica pública.
- ``ingestao``: regra única de supressão (k-anonimato) + caminho de escrita ouro compartilhado.
- ``seed``: povoamento inicial — passa pelo MESMO caminho ouro da ingestão.
- ``ia`` / ``consentimento``: fronteiras isoladas (não construídas nesta fatia).
"""

__version__ = "0.1.0"
