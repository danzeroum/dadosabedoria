"""Integração da rota do Pulso Produtivo (``/v1/pulso-produtivo/{ibge}``) — dado real do seed."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


async def test_pulso_sp_esfriando_melhorando_com_proveniencia(client) -> None:
    r = await client.get("/v1/pulso-produtivo/3550308")
    assert r.status_code == 200
    b = r.json()
    assert b["nome"] == "São Paulo"
    assert b["periodo"] == "2026-04"
    assert b["saldo_mes"] == -9100  # batida atual
    assert b["saldo_acumulado"] == -16300  # 8200 - 15400 - 9100
    assert b["pulso"] == "esfriando"
    assert b["tendencia"] == "melhorando"  # menos negativo que o mês anterior
    assert b["meses_positivos"] == 1
    assert b["meses_negativos"] == 2
    assert [m["saldo"] for m in b["meses"]] == [8200, -15400, -9100]
    # proveniência REAL vinda do banco (não hardcoded no produto).
    assert b["meta"]["indicador"] == "trabalho.emprego.saldo_caged"
    assert b["meta"]["fonte"] == "Novo CAGED"
    assert b["meta"]["lag_tipico_dias"] == 40
    # honestidade do produto: emprego formal, fluxo que "merece a pergunta".
    assert "formal" in b["nota"]
    assert "merece a pergunta" in b["nota"]


async def test_pulso_campinas_acumulado_positivo_mas_batida_esfria(client) -> None:
    b = (await client.get("/v1/pulso-produtivo/3509502")).json()
    assert b["saldo_acumulado"] == 100  # +1200 -800 -300, puxado por janeiro
    assert b["pulso"] == "esfriando"  # a batida atual não some no agregado
    assert b["tendencia"] == "melhorando"


async def test_pulso_territorio_inexistente_404(client) -> None:
    r = await client.get("/v1/pulso-produtivo/0000000")
    assert r.status_code == 404
    assert r.json()["erro"] == "nao_encontrado"


async def test_pulso_territorio_sem_caged_404(client) -> None:
    # Brasil existe como território, mas não tem saldo CAGED → 404 (sem dado do produto, honesto).
    r = await client.get("/v1/pulso-produtivo/1")
    assert r.status_code == 404
    assert r.json()["erro"] == "nao_encontrado"
