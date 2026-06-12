"""Módulo de domínio ``energia`` (plugin, Onda 2C) — ANEEL DEC/FEC via ModuloDominio (§6)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.observabilidade import get_logger
from app.ingestao.adaptadores.base import FetcherFonte
from app.ingestao.adaptadores.energia import (
    CODIGO_DEC,
    CODIGO_FEC,
    AdaptadorAneel,
    FetcherAneelHTTP,
)

if TYPE_CHECKING:
    from fastapi import APIRouter

_log = get_logger("dominio.energia")


class ModuloEnergia:
    codigo = "energia"
    versao_core = "0.1"

    def __init__(self, fetcher: FetcherFonte | None = None) -> None:
        self._adaptador = AdaptadorAneel(fetcher or FetcherAneelHTTP())

    def registrar_indicadores(self) -> list[object]:
        return [
            {
                "codigo": CODIGO_DEC,
                "dominio": "energia",
                "subdominio": "qualidade",
                "fonte": "aneel",
            },
            {
                "codigo": CODIGO_FEC,
                "dominio": "energia",
                "subdominio": "qualidade",
                "fonte": "aneel",
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
