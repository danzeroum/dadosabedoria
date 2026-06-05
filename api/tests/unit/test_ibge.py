"""Unidade do adaptador IBGE (parse de Localidades e Malhas) — puro, sem rede/DB."""

from __future__ import annotations

from app.ingestao.adaptadores.ibge import AdaptadorIbge
from tests.fixtures.ibge import LOCALIDADES, MALHA_SP, FetcherIbgeFake


def _adaptador() -> AdaptadorIbge:
    return AdaptadorIbge(FetcherIbgeFake(LOCALIDADES, MALHA_SP))


def test_parse_municipios() -> None:
    municipios = AdaptadorIbge.parse_municipios(LOCALIDADES)
    assert len(municipios) == 3
    sp = next(m for m in municipios if m["codigo_ibge"] == "3550308")
    assert sp["nome"] == "São Paulo"
    assert sp["uf"] == "SP"
    assert sp["uf_id"] == "35"


def test_parse_malha() -> None:
    malha = AdaptadorIbge.parse_malha(MALHA_SP)
    assert set(malha.keys()) == {"3550308", "3509502"}
    assert '"Polygon"' in malha["3550308"]


def test_adaptador_municipios_e_malha() -> None:
    a = _adaptador()
    assert len(a.municipios()) == 3
    assert len(a.malha("SP")) == 2
