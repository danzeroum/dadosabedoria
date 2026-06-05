"""Amostras do IBGE: Localidades (municípios) e Malhas (GeoJSON)."""

from __future__ import annotations

import json


def _uf(id_: int, sigla: str, nome: str) -> dict:
    return {"microrregiao": {"mesorregiao": {"UF": {"id": id_, "sigla": sigla, "nome": nome}}}}


LOCALIDADES = json.dumps(
    [
        {"id": 3550308, "nome": "São Paulo", **_uf(35, "SP", "São Paulo")},
        {"id": 3509502, "nome": "Campinas", **_uf(35, "SP", "São Paulo")},
        {"id": 3304557, "nome": "Rio de Janeiro", **_uf(33, "RJ", "Rio de Janeiro")},
    ]
).encode("utf-8")


def _quadrado(cod: str, lon: float, lat: float) -> dict:
    d = 0.2
    anel = [[lon, lat], [lon + d, lat], [lon + d, lat + d], [lon, lat + d], [lon, lat]]
    return {
        "type": "Feature",
        "properties": {"codarea": cod},
        "geometry": {"type": "Polygon", "coordinates": [anel]},
    }


MALHA_SP = json.dumps(
    {
        "type": "FeatureCollection",
        "features": [
            _quadrado("3550308", -46.8, -23.7),
            _quadrado("3509502", -47.2, -23.0),
        ],
    }
).encode("utf-8")


class FetcherIbgeFake:
    def __init__(self, localidades: bytes, malha: bytes) -> None:
        self._localidades = localidades
        self._malha = malha

    def localidades_municipios(self) -> bytes:
        return self._localidades

    def malha_uf(self, uf: str) -> bytes:
        return self._malha
