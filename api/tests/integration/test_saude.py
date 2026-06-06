"""Domínio `saude` (DATASUS/SIH) na API genérica — fatia vertical via seed, contra DB real.

Origem sensível: o catálogo expõe o indicador e a API serve as células não suprimidas (a supressão
k-anon da célula sub-limiar é coberta em test_api.py).
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration

_IND = "saude.resp.internacoes_j"


async def test_indicador_saude_no_catalogo(client) -> None:
    r = await client.get("/v1/indicadores?dominio=saude")
    assert r.status_code == 200
    assert _IND in [i["codigo"] for i in r.json()["dados"]]


async def test_valores_saude_servidos(client) -> None:
    r = await client.get(f"/v1/valores?indicador={_IND}&territorio=3550308")
    assert r.status_code == 200
    dados = r.json()["dados"]
    assert any(d["valor"] == 660.0 for d in dados)  # internações jun/2026 (SP), via gold path
