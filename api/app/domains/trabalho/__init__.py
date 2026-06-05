"""Módulo de domínio ``trabalho`` (plugin) — primeiro uso concreto do contrato ``ModuloDominio``.

Registra o adaptador do CAGED e o catálogo do indicador de emprego. A API de leitura genérica já
serve o domínio, então ``registrar_rotas_api`` é no-op nesta fatia. Prova que o encaixe de plugins
(§6) funciona sem alterar o núcleo.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from app.core.observabilidade import get_logger
from app.ingestao.adaptadores.base import FetcherFonte
from app.ingestao.adaptadores.caged import CODIGO_INDICADOR, AdaptadorCaged, FetcherCagedFTP

if TYPE_CHECKING:
    from fastapi import APIRouter

_log = get_logger("dominio.trabalho")


class ModuloTrabalho:
    codigo = "trabalho"
    versao_core = "0.1"

    def __init__(self, fetcher: FetcherFonte | None = None) -> None:
        self._adaptador = AdaptadorCaged(fetcher or FetcherCagedFTP())

    def registrar_indicadores(self) -> list[object]:
        catalogo: list[object] = [
            {
                "codigo": CODIGO_INDICADOR,
                "dominio": "trabalho",
                "subdominio": "emprego_formal",
                "fonte": "novo_caged",
            }
        ]
        return catalogo

    def registrar_adaptadores_fonte(self) -> list[object]:
        adaptadores: list[object] = [self._adaptador]
        return adaptadores

    def registrar_rotas_api(self, router: APIRouter) -> None:
        return None  # a API genérica de indicadores já serve este domínio

    def registrar_paineis(self) -> list[object]:
        return []

    def ativar(self) -> None:
        _log.info("modulo_ativado", modulo=self.codigo)

    def desativar(self) -> None:
        _log.info("modulo_desativado", modulo=self.codigo)
