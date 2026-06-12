"""Módulo de domínio ``saneamento`` (plugin, Onda 2C) — SNIS/MDR via ModuloDominio (§6)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.observabilidade import get_logger
from app.ingestao.adaptadores.base import FetcherFonte
from app.ingestao.adaptadores.saneamento import (
    CODIGO_AGUA,
    CODIGO_ESGOTO,
    AdaptadorSnis,
    FetcherSnisHTTP,
)

if TYPE_CHECKING:
    from fastapi import APIRouter

_log = get_logger("dominio.saneamento")


class ModuloSaneamento:
    codigo = "saneamento"
    versao_core = "0.1"

    def __init__(self, fetcher: FetcherFonte | None = None) -> None:
        self._adaptador = AdaptadorSnis(fetcher or FetcherSnisHTTP())

    def registrar_indicadores(self) -> list[object]:
        return [
            {
                "codigo": CODIGO_AGUA,
                "dominio": "saneamento",
                "subdominio": "agua",
                "fonte": "snis",
            },
            {
                "codigo": CODIGO_ESGOTO,
                "dominio": "saneamento",
                "subdominio": "esgoto",
                "fonte": "snis",
            },
        ]

    def registrar_adaptadores_fonte(self) -> list[object]:
        return [self._adaptador]

    def registrar_rotas_api(self, router: APIRouter) -> None:
        return None

    def registrar_paineis(self) -> list[object]:
        return []

    def ativar(self) -> None:
        _log.info("modulo_ativado", modulo=self.codigo)

    def desativar(self) -> None:
        _log.info("modulo_desativado", modulo=self.codigo)
