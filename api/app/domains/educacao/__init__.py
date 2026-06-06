"""Módulo de domínio ``educacao`` (plugin, Onda 2A) — prova o contrato ``ModuloDominio`` (§6) com
**dado externo real** (INEP/Censo Escolar), sem tocar o núcleo (Open/Closed). A API genérica de
leitura já serve o domínio, então ``registrar_rotas_api`` é no-op.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.observabilidade import get_logger
from app.ingestao.adaptadores.base import FetcherFonte
from app.ingestao.adaptadores.inep import (
    CODIGO_INDICADOR,
    AdaptadorInep,
    FetcherInepHTTP,
)

if TYPE_CHECKING:
    from fastapi import APIRouter

_log = get_logger("dominio.educacao")


class ModuloEducacao:
    codigo = "educacao"
    versao_core = "0.1"

    def __init__(self, fetcher: FetcherFonte | None = None) -> None:
        self._adaptador = AdaptadorInep(fetcher or FetcherInepHTTP())

    def registrar_indicadores(self) -> list[object]:
        return [
            {
                "codigo": CODIGO_INDICADOR,
                "dominio": "educacao",
                "subdominio": "matriculas",
                "fonte": "inep",
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
