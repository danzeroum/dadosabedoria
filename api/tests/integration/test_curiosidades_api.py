"""Integração — rota 'Você Sabia?' (/v1/territorios/{ibge}/curiosidades).

Comportamento ancorado (Invariante 3): 404 só se o território não existir; sem fato nítido → lista
vazia (honesto); toda curiosidade traz fonte. Campinas tem água≫esgoto no seed → dispara o gap.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration


async def test_curiosidades_404_territorio_inexistente(client) -> None:
    r = await client.get("/v1/territorios/0000000/curiosidades")
    assert r.status_code == 404
    assert r.json()["erro"] == "nao_encontrado"


async def test_curiosidades_campinas_dispara_gap_agua_esgoto(client) -> None:
    r = await client.get("/v1/territorios/3509502/curiosidades")
    assert r.status_code == 200
    b = r.json()
    assert b["codigo_ibge"] == "3509502"
    assert b["nome"] == "Campinas"
    gaps = [c for c in b["curiosidades"] if c["produto"] == "esgoto-invisivel"]
    assert len(gaps) == 1
    c = gaps[0]
    assert "88%" in c["texto"] and "35%" in c["texto"]  # ancorado nos valores recuperados
    assert c["fonte"]  # proveniência sempre


async def test_curiosidades_envelope_honesto_e_lista(client) -> None:
    # SP existe; o envelope é válido e 'curiosidades' é uma lista. Se houver fato, tem fonte.
    r = await client.get("/v1/territorios/3550308/curiosidades")
    assert r.status_code == 200
    b = r.json()
    assert b["nome"] == "São Paulo"
    assert isinstance(b["curiosidades"], list)
    for c in b["curiosidades"]:
        assert c["fonte"]
        assert "texto" in c
