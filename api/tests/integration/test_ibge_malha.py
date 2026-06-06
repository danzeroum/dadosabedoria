"""Integração IBGE: carga de geometrias + endpoint GeoJSON do IVM, contra PostGIS real."""

from __future__ import annotations

import pytest

from app.core.config import get_settings
from app.core.db import connect
from app.indicadores.ivm import refrescar_ivm
from app.ingestao.adaptadores.ibge import AdaptadorIbge
from app.ingestao.territorios import executar_ibge
from tests.fixtures.ibge import LOCALIDADES, MALHA_SP, FetcherIbgeFake

pytestmark = pytest.mark.integration


async def _carregar_sp() -> None:
    adaptador = AdaptadorIbge(FetcherIbgeFake(LOCALIDADES, MALHA_SP))
    async with connect(get_settings().database_url) as conn:
        resumo = await executar_ibge(conn, adaptador, "SP")
    assert resumo["geometrias"] >= 2  # SP + Campinas ganham geometria


async def test_carrega_geometria_e_serve_geojson(client) -> None:
    await _carregar_sp()
    await refrescar_ivm()

    r = await client.get("/v1/mapa/ivm", params={"uf": "SP", "periodo": "2026-04"})
    assert r.status_code == 200
    fc = r.json()
    assert fc["type"] == "FeatureCollection"
    por_cod = {f["properties"]["codigo_ibge"]: f for f in fc["features"]}

    # São Paulo: tem geometria e IVM (seed 2026-04).
    sp = por_cod["3550308"]
    assert sp["geometry"]["type"] in ("Polygon", "MultiPolygon")
    assert sp["properties"]["ivm"] is not None
    assert sp["properties"]["semaforo"] in ("verde", "amarelo", "vermelho")

    # Campinas: tem geometria E IVM (crédito semeado no período) — entra no mapa com semáforo.
    cps = por_cod["3509502"]
    assert cps["geometry"] is not None
    assert cps["properties"]["ivm"] is not None
    assert cps["properties"]["semaforo"] in ("verde", "amarelo", "vermelho")


async def test_uf_sem_geometria_retorna_vazio(client) -> None:
    r = await client.get("/v1/mapa/ivm", params={"uf": "AC"})  # Acre, sem dados
    assert r.status_code == 200
    fc = r.json()
    assert fc["type"] == "FeatureCollection"
    assert fc["features"] == []
