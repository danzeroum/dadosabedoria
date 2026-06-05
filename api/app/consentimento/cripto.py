"""Cifragem em nível de campo e pseudonimização do contato (§8.1.4).

Chave do ``app`` (``APP_FIELD_KEY``) distinta da analítica, em gestor de segredos. Aceita qualquer
string (deriva a chave Fernet por SHA-256). Contato pseudonimizado por HMAC determinístico (permite
dedup/lookup sem guardar o dado bruto).
"""

from __future__ import annotations

import base64
import hashlib
import hmac

from cryptography.fernet import Fernet

from app.core.config import get_settings


def _segredo() -> bytes:
    chave = get_settings().app_field_key or ""
    if not chave:
        raise RuntimeError("APP_FIELD_KEY não configurada (cifragem de campo).")
    return chave.encode("utf-8")


def _fernet() -> Fernet:
    derivada = base64.urlsafe_b64encode(hashlib.sha256(_segredo()).digest())
    return Fernet(derivada)


def hash_contato(contato: str) -> str:
    """Pseudonimização determinística do e-mail/telefone (pepper = APP_FIELD_KEY)."""
    normalizado = contato.strip().lower().encode("utf-8")
    return hmac.new(_segredo(), normalizado, hashlib.sha256).hexdigest()


def cifrar(texto: str) -> str:
    return _fernet().encrypt(texto.encode("utf-8")).decode("ascii")


def decifrar(token: str) -> str:
    return _fernet().decrypt(token.encode("ascii")).decode("utf-8")
