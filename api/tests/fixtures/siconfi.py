"""Fixture do SICONFI (amostra JSON da DCA) — testes sem rede."""

from __future__ import annotations

import json

from app.ingestao.adaptadores.base import Janela

_ITENS = [
    {"cod_ibge": "3550308", "conta": "Transferências Correntes", "valor": "1000000.00"},
    {"cod_ibge": "3550308", "conta": "Transferências Correntes", "valor": "500000.00"},
    {"cod_ibge": "3509502", "conta": "Transferências Correntes", "valor": "250000.00"},
    {
        "cod_ibge": "3550308",
        "conta": "Receita Tributária",
        "valor": "9999.00",
    },  # fora da conta-alvo
]
AMOSTRA = json.dumps({"items": _ITENS}).encode("utf-8")


class FetcherFake:
    """Fetcher injetável que devolve a amostra (sem rede)."""

    def __init__(self, bruto: bytes) -> None:
        self._bruto = bruto

    def baixar(self, janela: Janela) -> tuple[bytes, str]:
        return self._bruto, "fixture://siconfi"
