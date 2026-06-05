"""Unidade da cifragem de campo e pseudonimização do contato (consentimento)."""

from __future__ import annotations

import pytest

from app.core.config import get_settings


@pytest.fixture(autouse=True)
def _chave(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("APP_FIELD_KEY", "chave-de-teste")
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


def test_hash_contato_deterministico_e_normalizado() -> None:
    from app.consentimento.cripto import hash_contato

    h1 = hash_contato("Foo@Bar.com")
    h2 = hash_contato("  foo@bar.com ")
    assert h1 == h2  # case/espaços normalizados
    assert len(h1) == 64  # sha256 hex
    assert "foo" not in h1  # não guarda o contato bruto


def test_cifrar_decifrar_roundtrip() -> None:
    from app.consentimento.cripto import cifrar, decifrar

    token = cifrar("asma")
    assert token != "asma"  # cifrado
    assert decifrar(token) == "asma"
