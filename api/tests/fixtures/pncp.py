"""Fixture do PNCP (amostra JSON de contratos, com o município aninhado) — testes sem rede."""

from __future__ import annotations

import json

from app.ingestao.adaptadores.base import Janela


def _unidade(ibge: str, nome: str) -> dict[str, str]:
    return {"codigoIbge": ibge, "municipioNome": nome, "ufSigla": "SP"}


_ITENS = [
    {"valorGlobal": 1000000.00, "unidadeOrgao": _unidade("3550308", "São Paulo")},
    {"valorGlobal": 500000.00, "unidadeOrgao": _unidade("3550308", "São Paulo")},
    {"valorGlobal": 250000.00, "unidadeOrgao": _unidade("3509502", "Campinas")},
    {"valorGlobal": None, "unidadeOrgao": _unidade("3509502", "Campinas")},  # sem valor → filtrado
]
AMOSTRA = json.dumps({"data": _ITENS}).encode("utf-8")


class FetcherFake:
    """Fetcher injetável que devolve a amostra (sem rede)."""

    def __init__(self, bruto: bytes) -> None:
        self._bruto = bruto

    def baixar(self, janela: Janela) -> tuple[bytes, str]:
        return self._bruto, "fixture://pncp"
