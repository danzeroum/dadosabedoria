"""Segurança da camada de apresentação (§8): CORS por allowlist e cabeçalhos.

Leitura pública é sem login. Autenticação do tier profundo (OAuth2 client-credentials) e do
cidadão (OIDC + JWT em cookie HttpOnly) entram em fatias futuras — aqui ficam só os limites
seguros que valem para a camada pública.
"""

from __future__ import annotations

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.core.config import Settings


def configurar_cors(app: FastAPI, settings: Settings) -> None:
    # Nunca '*' (§8): allowlist explícita por ambiente.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )
