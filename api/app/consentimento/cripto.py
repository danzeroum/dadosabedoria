"""Cifragem em nível de campo e pseudonimização do contato (§8.1.4) — com ANEL DE CHAVES.

Chave do ``app`` distinta da analítica, em gestor de segredos. A ``APP_FIELD_KEY`` é a chave
**primária** (cifra e gera o hash canônico). ``APP_FIELD_KEYS_ANTIGAS`` (CSV) lista chaves
**aposentadas**, aceitas só para DECIFRAR/VERIFICAR durante a rotação:

- **Cifragem** (condição sensível): ``MultiFernet`` — cifra com a primária, decifra com qualquer
  uma; ``recifrar`` re-cifra um token para a primária (rotação em lote, sem o dado bruto).
- **Pseudônimo** (contato → ``contato_hash``): HMAC determinístico. ``hash_contato`` usa a primária
  (hash atual); ``hashes_contato`` devolve o hash de cada chave (login: casa qualquer versão e
  migra a linha para a primária — re-chave preguiçoso).

Sem ``APP_FIELD_KEYS_ANTIGAS``, o comportamento é idêntico ao de chave única (compatível-para-trás).
"""

from __future__ import annotations

import base64
import hashlib
import hmac

from cryptography.fernet import Fernet, MultiFernet

from app.core.config import get_settings


def _chaves() -> list[bytes]:
    """Anel de chaves: a primária primeiro, depois as aposentadas (ordem importa)."""
    s = get_settings()
    primaria = s.app_field_key or ""
    if not primaria:
        raise RuntimeError("APP_FIELD_KEY não configurada (cifragem de campo).")
    antigas = [k.strip() for k in (s.app_field_keys_antigas or "").split(",") if k.strip()]
    return [primaria.encode("utf-8"), *[a.encode("utf-8") for a in antigas]]


def _fernet_de(chave: bytes) -> Fernet:
    return Fernet(base64.urlsafe_b64encode(hashlib.sha256(chave).digest()))


def _multifernet() -> MultiFernet:
    # MultiFernet cifra com a 1ª (primária) e decifra tentando todas (primária → aposentadas).
    return MultiFernet([_fernet_de(k) for k in _chaves()])


def _hmac(chave: bytes, contato: str) -> str:
    normalizado = contato.strip().lower().encode("utf-8")
    return hmac.new(chave, normalizado, hashlib.sha256).hexdigest()


def hash_contato(contato: str) -> str:
    """Pseudônimo determinístico do contato com a chave PRIMÁRIA (o hash canônico atual)."""
    return _hmac(_chaves()[0], contato)


def hashes_contato(contato: str) -> list[str]:
    """Hash do contato com cada chave do anel (primária primeiro) — para login/re-chave."""
    return [_hmac(k, contato) for k in _chaves()]


def cifrar(texto: str) -> str:
    return _multifernet().encrypt(texto.encode("utf-8")).decode("ascii")


def decifrar(token: str) -> str:
    return _multifernet().decrypt(token.encode("ascii")).decode("utf-8")


def recifrar(token: str) -> str:
    """Re-cifra um token para a chave primária (rotação em lote). Idempotente se já é primária."""
    return _multifernet().rotate(token.encode("ascii")).decode("ascii")
