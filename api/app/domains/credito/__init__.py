"""Módulo de domínio ``credito`` (plugin) — registra o adaptador BCB/ESTBAN e o indicador de
crédito por município (insumo do subíndice de finanças do IVM).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.observabilidade import get_logger
from app.ingestao.adaptadores.base import FetcherFonte
from app.ingestao.adaptadores.estban import CODIGO_INDICADOR, AdaptadorEstban, FetcherEstbanHTTP

if TYPE_CHECKING:
    from fastapi import APIRouter

_log = get_logger("dominio.credito")


class ModuloCredito:
    codigo = "credito"
    versao_core = "0.1"

    def __init__(self, fetcher: FetcherFonte | None = None) -> None:
        self._adaptador = AdaptadorEstban(fetcher or FetcherEstbanHTTP())

    def registrar_indicadores(self) -> list[object]:
        catalogo: list[object] = [
            {
                "codigo": CODIGO_INDICADOR,
                "dominio": "credito",
                "subdominio": "operacoes",
                "fonte": "bcb_estban",
            }
        ]
        return catalogo

    def registrar_adaptadores_fonte(self) -> list[object]:
        adaptadores: list[object] = [self._adaptador]
        return adaptadores

    def registrar_rotas_api(self, router: APIRouter) -> None:
        return None

    def registrar_paineis(self) -> list[object]:
        return []

    def ativar(self) -> None:
        _log.info("modulo_ativado", modulo=self.codigo)

    def desativar(self) -> None:
        _log.info("modulo_desativado", modulo=self.codigo)
