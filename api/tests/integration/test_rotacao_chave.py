"""Rotação da chave de campo (anel de chaves) contra Postgres real (ADR-0016).

Escreve sob a chave A, rotaciona (B primária, A aposentada) e prova: (1) o pseudônimo migra no
acesso — ``migrar_pseudonimo`` re-chaveia a linha de A→B; (2) a condição sensível segue decifrável
e ``recifrar_condicoes`` a re-cifra para a primária, decifrável só com B. Restaura as chaves no fim.
"""

from __future__ import annotations

import os

import pytest
from sqlalchemy import text

from app.core.config import get_settings

pytestmark = pytest.mark.integration

_EMAIL = "rotacao@exemplo.com"
_KEY_A = "rotacao-chave-A-de-teste"
_KEY_B = "rotacao-chave-B-de-teste"


def _set_keys(primaria: str, antigas: str | None = None) -> None:
    os.environ["APP_FIELD_KEY"] = primaria
    if antigas:
        os.environ["APP_FIELD_KEYS_ANTIGAS"] = antigas
    else:
        os.environ.pop("APP_FIELD_KEYS_ANTIGAS", None)
    get_settings.cache_clear()


async def test_rotacao_anel_de_chaves(db_pronto: None) -> None:
    from app.consentimento import repositorio
    from app.consentimento.cripto import decifrar, hash_contato
    from app.consentimento.db import consent_session, dispose_consent_engine

    orig_key = os.environ.get("APP_FIELD_KEY")
    orig_ant = os.environ.get("APP_FIELD_KEYS_ANTIGAS")
    aid: int | None = None
    try:
        # estado limpo de condições (o re-cifrar em lote toca todas; evita rows de outros testes
        # cifradas sob outra chave).
        _set_keys(_KEY_A)
        async with consent_session() as s:
            await s.execute(text("DELETE FROM app.condicao_sensivel"))

        # 1) escreve sob a chave A (pseudônimo e condição).
        hash_a = hash_contato(_EMAIL)
        async with consent_session() as s:
            aid = await repositorio.assinar(
                s,
                contato_hash=hash_a,
                territorio_codigo="3550308",
                finalidade="alerta_ivm",
                condicao_sensivel="asma",
            )

        # 2) rotaciona: B primária, A aposentada.
        _set_keys(_KEY_B, antigas=_KEY_A)
        hash_b = hash_contato(_EMAIL)
        assert hash_b != hash_a

        # 3) re-chave preguiçoso no acesso: a linha migra A → B.
        async with consent_session() as s:
            sub = await repositorio.migrar_pseudonimo(s, _EMAIL)
        assert sub == hash_b
        async with consent_session() as s:
            atual = (
                await s.execute(
                    text("SELECT contato_hash FROM app.assinante_alerta WHERE id = :i"), {"i": aid}
                )
            ).scalar_one()
        assert atual == hash_b  # re-chaveado

        # 4) re-cifra a condição para a primária; decifra só com B (sem a antiga).
        async with consent_session() as s:
            assert await repositorio.recifrar_condicoes(s) >= 1
        _set_keys(_KEY_B)
        async with consent_session() as s:
            cond = (
                await s.execute(
                    text("SELECT tipo FROM app.condicao_sensivel WHERE assinante_id = :i"),
                    {"i": aid},
                )
            ).scalar_one()
        assert decifrar(cond) == "asma"
    finally:
        if aid is not None:
            async with consent_session() as s:
                await s.execute(text("DELETE FROM app.assinante_alerta WHERE id = :i"), {"i": aid})
        if orig_key is None:
            os.environ.pop("APP_FIELD_KEY", None)
        else:
            os.environ["APP_FIELD_KEY"] = orig_key
        if orig_ant is None:
            os.environ.pop("APP_FIELD_KEYS_ANTIGAS", None)
        else:
            os.environ["APP_FIELD_KEYS_ANTIGAS"] = orig_ant
        get_settings.cache_clear()
        # usamos consent_session direto (sem a fixture consent_client): liberar o engine para não
        # vazar conexões presas a este event loop para o próximo teste.
        await dispose_consent_engine()
