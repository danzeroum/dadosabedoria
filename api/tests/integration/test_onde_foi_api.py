"""Integração da rota do OndeFoi (``/v1/onde-foi/{ibge}``) — contrato do ADR-0026."""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


async def test_onde_foi_contrato_sp(client) -> None:
    r = await client.get("/v1/onde-foi/3550308")
    assert r.status_code == 200
    b = r.json()
    assert b["nome"] == "São Paulo"
    # denominador base-única (ADR-0026): % e recebido_base sobre as funções divulgadas.
    assert b["recebido_base"] == 54200
    assert b["executado"] == 47800
    assert b["pct"] == 88
    assert b["pct"] == round(b["executado"] / b["recebido_base"] * 100)
    # a parcela fora é explícita; o total NUNCA é o denominador.
    assert b["recebido_fora_base"] == b["recebido_total"] - b["recebido_base"]
    assert b["recebido_total"] > b["recebido_base"]
    # honestidade: execução orçamentária, não serviço entregue.
    assert "serviço entregue" in b["meta"]["metodologia"]
    assert b["meta"]["periodo_rotulo"] == "exercício 2025"
    # sem cadeado de privacidade em orçamento público (refino do ADR-0026).
    assert {f["exe_estado"] for f in b["funcoes"]} <= {"valor", "sem_cobertura"}


async def test_onde_foi_sem_cobertura_fora_da_base(client) -> None:
    # Rio: Saneamento + Cultura sem cobertura → fora do numerador e do denominador, explícito.
    b = (await client.get("/v1/onde-foi/3304557")).json()
    assert b["recebido_base"] == 26000
    assert b["pct"] == 76
    sem = [f for f in b["funcoes"] if f["exe_estado"] == "sem_cobertura"]
    assert {f["funcao"] for f in sem} == {"Saneamento", "Cultura"}
    assert all(f["exe"] is None and f["pct"] is None for f in sem)


async def test_onde_foi_404(client) -> None:
    r = await client.get("/v1/onde-foi/0000000")
    assert r.status_code == 404
    assert r.json()["erro"] == "nao_encontrado"
