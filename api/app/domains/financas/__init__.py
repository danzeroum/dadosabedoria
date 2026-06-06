"""Módulo de domínio ``financas`` (plugin, Onda 2A) — prova o contrato ``ModuloDominio`` (§6) com
**dado externo real** (SICONFI/STN), sem tocar o núcleo (Open/Closed). A API genérica de leitura já
serve o domínio, então ``registrar_rotas_api`` é no-op.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.observabilidade import get_logger
from app.ingestao.adaptadores.base import FetcherFonte
from app.ingestao.adaptadores.siconfi import (
    CODIGO_INDICADOR,
    AdaptadorSiconfi,
    FetcherSiconfiHTTP,
)

if TYPE_CHECKING:
    from fastapi import APIRouter

_log = get_logger("dominio.financas")


class ModuloFinancas:
    codigo = "financas"
    versao_core = "0.1"

    def __init__(self, fetcher: FetcherFonte | None = None) -> None:
        self._adaptador = AdaptadorSiconfi(fetcher or FetcherSiconfiHTTP())

    def registrar_indicadores(self) -> list[object]:
        return [
            {
                "codigo": CODIGO_INDICADOR,
                "dominio": "financas",
                "subdominio": "transferencias",
                "fonte": "siconfi",
            }
        ]

    def registrar_adaptadores_fonte(self) -> list[object]:
        return [self._adaptador]

    def registrar_rotas_api(self, router: APIRouter) -> None:
        return None  # a API genérica de indicadores já serve este domínio

    def registrar_paineis(self) -> list[object]:
        return []

    def ativar(self) -> None:
        _log.info("modulo_ativado", modulo=self.codigo)

    def desativar(self) -> None:
        _log.info("modulo_desativado", modulo=self.codigo)
