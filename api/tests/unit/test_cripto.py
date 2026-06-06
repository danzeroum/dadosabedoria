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


def test_anel_decifra_e_reconhece_chave_antiga(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.consentimento.cripto import cifrar, decifrar, hash_contato, hashes_contato

    # cifra/pseudonimiza com a chave A (primária, sem antigas).
    monkeypatch.setenv("APP_FIELD_KEY", "chave-A")
    monkeypatch.delenv("APP_FIELD_KEYS_ANTIGAS", raising=False)
    get_settings.cache_clear()
    token_a = cifrar("asma")
    hash_a = hash_contato("foo@bar.com")

    # rotaciona: B vira primária, A fica aposentada.
    monkeypatch.setenv("APP_FIELD_KEY", "chave-B")
    monkeypatch.setenv("APP_FIELD_KEYS_ANTIGAS", "chave-A")
    get_settings.cache_clear()
    assert decifrar(token_a) == "asma"  # decifra com a antiga
    assert hash_contato("foo@bar.com") != hash_a  # hash primário mudou (agora B)
    hs = hashes_contato("foo@bar.com")
    assert hs[0] == hash_contato("foo@bar.com")  # primária primeiro
    assert hash_a in hs  # o hash antigo ainda é reconhecido (re-chave preguiçoso)


def test_recifrar_para_primaria(monkeypatch: pytest.MonkeyPatch) -> None:
    from app.consentimento.cripto import cifrar, decifrar, recifrar

    monkeypatch.setenv("APP_FIELD_KEY", "chave-A")
    monkeypatch.delenv("APP_FIELD_KEYS_ANTIGAS", raising=False)
    get_settings.cache_clear()
    token_a = cifrar("diabetes")

    monkeypatch.setenv("APP_FIELD_KEY", "chave-B")
    monkeypatch.setenv("APP_FIELD_KEYS_ANTIGAS", "chave-A")
    get_settings.cache_clear()
    token_b = recifrar(token_a)

    # aposenta a antiga: o token re-cifrado ainda decifra (está sob a primária B).
    monkeypatch.delenv("APP_FIELD_KEYS_ANTIGAS", raising=False)
    get_settings.cache_clear()
    assert decifrar(token_b) == "diabetes"
