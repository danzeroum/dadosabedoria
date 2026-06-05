"""Consumo dos alertas: IVM vermelho → notificação ao assinante (pull), contra Postgres real.

Cria um cenário determinístico (um município em vermelho num período isolado), assina um cidadão,
roda o job e verifica: notificação gravada com proveniência, idempotência, recuperação autenticada
e isolamento (role_analitica negada em ``app.notificacao``).
"""

from __future__ import annotations

import os
from datetime import date

import asyncpg
import pytest

from tests.helpers import asyncpg_dsn

pytestmark = pytest.mark.integration

_PERIODO = date(2000, 1, 1)  # período isolado: não mexe no "mais recente" de outros testes
_PIOR = "3509502"  # Campinas — fica em vermelho (pior) no cenário
_MELHOR = "3550308"  # São Paulo — fica em verde


async def _cenario_vermelho() -> None:
    """Insere valores p/ 2 municípios (role_analitica) e recomputa o IVM: o pior vira vermelho."""
    ana = await asyncpg.connect(asyncpg_dsn(os.environ["DATABASE_URL"]))
    try:
        for cod, caged, credito in ((_MELHOR, 1000, 1000), (_PIOR, -500, 10)):
            for indicador, val in (
                ("trabalho.emprego.saldo_caged", caged),
                ("credito.operacoes.saldo_total", credito),
            ):
                await ana.execute(
                    """
                    INSERT INTO valor (indicador_id, territorio_id, periodo, atualizacao, valor,
                                       suprimido, fonte_id, versao)
                    SELECT i.id, t.id, $1, (SELECT atualizacao FROM valor LIMIT 1), $2, false,
                           (SELECT fonte_id FROM valor LIMIT 1), 1
                    FROM indicador i, territorio t
                    WHERE i.codigo = $3 AND t.codigo_ibge = $4
                    ON CONFLICT (indicador_id, territorio_id, periodo, versao)
                      DO UPDATE SET valor = EXCLUDED.valor
                    """,
                    _PERIODO,
                    val,
                    indicador,
                    cod,
                )
    finally:
        await ana.close()
    from app.indicadores.ivm import refrescar_ivm

    await refrescar_ivm()


async def _limpar() -> None:
    # role_analitica não tem DELETE no acervo (só SELECT/INSERT/UPDATE) — limpa como admin.
    adm = await asyncpg.connect(asyncpg_dsn(os.environ["ADMIN_DATABASE_URL"]))
    try:
        await adm.execute("DELETE FROM valor WHERE periodo = $1", _PERIODO)
    finally:
        await adm.close()
    from app.indicadores.ivm import refrescar_ivm

    await refrescar_ivm()


async def test_consumo_gera_notificacao_idempotente_e_isolada(consent_client) -> None:
    from app.consentimento.db import consent_session
    from app.consentimento.repositorio import processar_alertas

    await _cenario_vermelho()
    try:
        # cidadão assina alertas de IVM no município que está vermelho.
        r = await consent_client.post("/v1/auth/login", json={"email": "alertado@exemplo.com"})
        sub = r.json()["sub"]
        await consent_client.delete("/v1/eu")  # começa limpo
        await consent_client.post("/v1/auth/login", json={"email": "alertado@exemplo.com"})
        r = await consent_client.post(
            "/v1/alertas", json={"territorio": _PIOR, "finalidade": "alerta_ivm"}
        )
        assert r.status_code == 201

        # roda o consumo (no período do cenário) — 1 nova; rodar de novo é idempotente.
        async with consent_session() as s:
            assert await processar_alertas(s, _PERIODO) == 1
        async with consent_session() as s:
            assert await processar_alertas(s, _PERIODO) == 0

        # recuperação autenticada (pull): a notificação chega com proveniência.
        r = await consent_client.get("/v1/notificacoes")
        assert r.status_code == 200
        notes = r.json()
        assert len(notes) == 1
        n = notes[0]
        assert n["territorio"] == _PIOR and n["semaforo"] == "vermelho"
        assert n["periodo"] == "2000-01" and n["ivm"] == 100.0
        assert n["fonte"] and n["metodologia"]  # invariante 5
        assert n["lida"] is False

        # isolamento: role_analitica NÃO lê app.notificacao.
        ana = await asyncpg.connect(asyncpg_dsn(os.environ["DATABASE_URL"]))
        try:
            with pytest.raises(asyncpg.InsufficientPrivilegeError):
                await ana.fetch("SELECT * FROM app.notificacao LIMIT 1")
        finally:
            await ana.close()

        # eliminar (Art. 18) remove a notificação em cascata.
        assert (await consent_client.delete("/v1/eu")).status_code == 204
        assert (await consent_client.get("/v1/notificacoes")).json() == []
        _ = sub
    finally:
        await _limpar()
