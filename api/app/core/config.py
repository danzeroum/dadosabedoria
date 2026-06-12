"""Configuração 12-factor: tudo por variável de ambiente (invariante 8).

Três connection strings distintas materializam a política de isolamento de PII (§8.1):

- ``database_url``       → role_analitica (api/worker/ai).      Sem acesso ao schema ``app``.
- ``consent_database_url`` → role_consentimento (serviço de consentimento APENAS).
- ``admin_database_url``  → superusuário, usado SÓ pelo migrator (cria roles/grants/RLS).

Os contêineres api/worker/ai NÃO recebem ``consent_database_url``/``app_field_key`` — verificado
por checagem estática do docker-compose no quality gate.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", case_sensitive=False)

    # --- ambiente ---
    environment: str = Field(default="dev")  # dev | staging | prod
    service_name: str = Field(default="dadosabedoria-api")

    # --- banco analítico (role_analitica) ---
    database_url: str = Field(
        default="postgresql+asyncpg://role_analitica:dev@localhost:5432/dadosabedoria"
    )

    # --- caminhos privilegiados (NÃO entregues à api/worker/ai) ---
    admin_database_url: str | None = Field(default=None)
    consent_database_url: str | None = Field(default=None)
    app_field_key: str | None = Field(default=None)  # chave de campo PRIMÁRIA (cifra/HMAC novos)
    # Chaves aposentadas (CSV), aceitas só p/ DECIFRAR/VERIFICAR durante a rotação (anel de chaves).
    # Vazio ⇒ comportamento de chave única. Ver runbook docs/runbooks/rotacao-de-segredos.md.
    app_field_keys_antigas: str | None = Field(default=None)

    # --- cache / eventos ---
    redis_url: str = Field(default="redis://localhost:6379/0")
    cache_ttl_segundos: int = Field(default=300)

    # --- segurança / gateway ---
    jwt_secret: str = Field(default="dev-only-change-me")
    cors_origins: list[str] = Field(default_factory=lambda: ["http://localhost:3000"])
    doc_url_base: str = Field(default="https://docs.dadosabedoria.org/erros")

    # --- object storage (MinIO) — só usado quando a ingestão chegar ---
    s3_endpoint: str | None = Field(default=None)
    s3_key: str | None = Field(default=None)
    s3_secret: str | None = Field(default=None)
    s3_bucket_bronze: str = Field(default="bronze")

    # --- Tier profundo (open-core pago): SHA-256 (hex, CSV) das chaves de API emitidas a clientes.
    # Guarda-se o HASH, não a chave bruta. Vazio ⇒ tier profundo sem chaves válidas (tudo 401).
    deep_api_keys: str | None = Field(default=None)
    # Limite de requisições por hora por chave de API (tier profundo). Padrão: 1000/h.
    rate_limit_profundo: int = Field(default=1000)
    # Máximo de consultas em paralelo dentro de um lote (semáforo asyncio). Padrão: 5 = pool_size.
    concorrencia_lote: int = Field(default=5)

    # --- IA (fronteira; placeholder) ---
    llm_api_key: str | None = Field(default=None)
    # Provedor do narrador via API OpenAI-compatível: DeepSeek (hospedado) ou Ollama (local).
    # ``llm_base_url`` inclui /v1 — ex.: https://api.deepseek.com/v1 ou http://ollama:11434/v1.
    # Vazio (padrão) ⇒ narrador template determinístico (sem LLM; usado em dev/CI).
    llm_base_url: str | None = Field(default=None)
    llm_model: str | None = Field(default=None)  # ex.: deepseek-chat | llama3.1
    llm_timeout_segundos: float = Field(default=30.0)

    # --- observabilidade ---
    otel_exporter_otlp_endpoint: str | None = Field(default=None)
    paginacao_max: int = Field(default=1000)
    paginacao_padrao: int = Field(default=100)

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_origins(cls, v: object) -> object:
        """Aceita CSV (``a,b``) ou lista. Nunca usar ``*`` (§8)."""
        if isinstance(v, str):
            return [o.strip() for o in v.split(",") if o.strip()]
        return v

    @property
    def is_prod(self) -> bool:
        return self.environment.lower() == "prod"


@lru_cache
def get_settings() -> Settings:
    return Settings()
