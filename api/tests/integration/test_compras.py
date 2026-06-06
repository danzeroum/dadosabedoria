"""Domínio `compras` (PNCP) servido pela API genérica — fatia vertical via seed, contra DB real.

Prova o plugue de domínio (§6): com a dimensão + os fatos semeados pelo caminho ouro, a API de
leitura genérica já serve o novo domínio sem rota nova.
"""

from __future__ import annotations

import pytest

pytestmark = pytest.mark.integration

_IND = "compras.contratos.valor_total"


async def test_indicador_compras_no_catalogo(client) -> None:
    r = await client.get("/v1/indicadores?dominio=compras")
    assert r.status_code == 200
    assert _IND in [i["codigo"] for i in r.json()["dados"]]


async def test_valores_compras_servidos(client) -> None:
    r = await client.get(f"/v1/valores?indicador={_IND}&territorio=3550308")
    assert r.status_code == 200
    dados = r.json()["dados"]
    assert any(d["valor"] == 2_000_000_000.0 for d in dados)  # contratos 2024 (SP), via gold path
