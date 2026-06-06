"""Módulo de domínio ``saude`` (plugin, Onda 2B) — 1ª fonte de **origem sensível** (DATASUS/SIH).

Prova o ``ModuloDominio`` (§6) sem tocar o núcleo (Open/Closed); a supressão k-anon roda no
caminho ouro. A API genérica já serve o domínio, então ``registrar_rotas_api`` é no-op.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.observabilidade import get_logger
from app.ingestao.adaptadores.base import FetcherFonte
from app.ingestao.adaptadores.datasus import (
    CODIGO_INDICADOR,
    AdaptadorDatasus,
    FetcherDatasusFTP,
)

if TYPE_CHECKING:
    from fastapi import APIRouter

_log = get_logger("dominio.saude")


class ModuloSaude:
    codigo = "saude"
    versao_core = "0.1"

    def __init__(self, fetcher: FetcherFonte | None = None) -> None:
        self._adaptador = AdaptadorDatasus(fetcher or FetcherDatasusFTP())

    def registrar_indicadores(self) -> list[object]:
        return [
            {
                "codigo": CODIGO_INDICADOR,
                "dominio": "saude",
                "subdominio": "respiratorio",
                "fonte": "datasus_sih",
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
