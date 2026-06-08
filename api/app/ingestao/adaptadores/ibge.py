"""Adaptador IBGE — registro de municípios (Localidades) e geometrias (Malhas).

Fonte estrutural (não tem janela temporal): popula `territorio` (códigos/nomes/UF) e
`territorio.geom` (PostGIS, SIRGAS 2000 / SRID 4674). Fetcher injetável → testável sem rede.
"""

from __future__ import annotations

import json
from typing import Any, Protocol


class FetcherIbge(Protocol):
    def localidades_municipios(self) -> bytes: ...
    def malha_uf(self, uf: str) -> bytes: ...


def _uf_de_municipio(m: dict[str, Any]) -> dict[str, Any]:
    """Extrai a UF do município, tolerando a hierarquia antiga e a nova do IBGE."""
    micro = m.get("microrregiao") or {}
    uf = (micro.get("mesorregiao") or {}).get("UF") or {}
    if not uf:  # hierarquia nova (regiões imediata/intermediária)
        imediata = m.get("regiao-imediata") or {}
        uf = (imediata.get("regiao-intermediaria") or {}).get("UF") or {}
    return uf


class AdaptadorIbge:
    codigo = "ibge"

    def __init__(self, fetcher: FetcherIbge) -> None:
        self._fetcher = fetcher

    def municipios(self) -> list[dict[str, Any]]:
        return self.parse_municipios(self._fetcher.localidades_municipios())

    def malha(self, uf: str) -> dict[str, str]:
        return self.parse_malha(self._fetcher.malha_uf(uf))

    @staticmethod
    def parse_municipios(bruto: bytes) -> list[dict[str, Any]]:
        dados = json.loads(bruto)
        out: list[dict[str, Any]] = []
        for m in dados:
            uf = _uf_de_municipio(m)
            out.append(
                {
                    "codigo_ibge": str(m["id"]),
                    "nome": m["nome"],
                    "uf": uf.get("sigla"),
                    "uf_id": str(uf["id"]) if uf.get("id") is not None else None,
                }
            )
        return out

    @staticmethod
    def parse_malha(bruto: bytes) -> dict[str, str]:
        """FeatureCollection → {codigo_ibge: geometria GeoJSON (string)}."""
        fc = json.loads(bruto)
        out: dict[str, str] = {}
        for feat in fc.get("features", []):
            props = feat.get("properties") or {}
            cod = str(props.get("codarea") or props.get("CD_MUN") or "")
            geom = feat.get("geometry")
            if cod and geom:
                out[cod] = json.dumps(geom)
        return out


class FetcherIbgeHTTP:  # pragma: no cover - rede
    """Fetcher real (servicodados.ibge.gov.br). URLs **confirmadas no #0** (2026-06-07, ADR-0028):
    ``v1/localidades/municipios`` (5571 itens: ``id``+``nome``+hierarquia micro/meso/UF, e também
    ``regiao-imediata``) e ``v3/malhas/estados/{uf}`` (FeatureCollection, ``properties.codarea``,
    geometria Polygon) respondem na forma que o parse espera — fixture já fiel-à-forma."""

    BASE = "https://servicodados.ibge.gov.br/api"

    def _get(self, url: str) -> bytes:
        import gzip
        import urllib.request

        req = urllib.request.Request(url, headers={"Accept-Encoding": "gzip"})
        with urllib.request.urlopen(req, timeout=120) as resp:  # noqa: S310  # nosec B310
            data = resp.read()
        # A API do IBGE retorna gzip quando solicitado; descomprimir se necessário.
        if data[:2] == b"\x1f\x8b":
            data = gzip.decompress(data)
        return data

    def localidades_municipios(self) -> bytes:
        return self._get(f"{self.BASE}/v1/localidades/municipios")

    def malha_uf(self, uf: str) -> bytes:
        return self._get(
            f"{self.BASE}/v3/malhas/estados/{uf}"
            "?formato=application/vnd.geo+json&qualidade=intermediaria&intrarregiao=municipio"
        )
