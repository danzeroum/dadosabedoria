"""Fixture do INEP (amostra CSV do Censo Escolar, nível escola) — testes sem rede.

Encodada em **latin-1** (com acento em ``NO_MUNICIPIO``) de propósito, para exercer o caminho
``utf8-lossy`` do adaptador: as colunas numéricas (IBGE, matrículas) sobrevivem ao decode tolerante.
"""

from __future__ import annotations

from app.ingestao.adaptadores.base import Janela

_CABECALHO = "NU_ANO_CENSO;CO_MUNICIPIO;NO_MUNICIPIO;QT_MAT_FUND"
_LINHAS = [
    "2024;3550308;São Paulo;800",
    "2024;3550308;São Paulo;200",
    "2024;3509502;Campinas;150",
    "2024;3509502;Campinas;",  # escola sem matrícula no fundamental → filtrada na prata
]
AMOSTRA = ("\n".join([_CABECALHO, *_LINHAS]) + "\n").encode("latin-1")


class FetcherFake:
    """Fetcher injetável que devolve a amostra (sem rede)."""

    def __init__(self, bruto: bytes) -> None:
        self._bruto = bruto

    def baixar(self, janela: Janela) -> tuple[bytes, str]:
        return self._bruto, "fixture://inep"
