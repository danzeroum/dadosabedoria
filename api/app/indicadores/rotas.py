"""Rotas REST de leitura (camada pública, só GET) — versão no caminho (``/v1``), aditiva (§7)."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.erros import ValidacaoError
from app.indicadores.facade import IndicadoresFacade
from app.indicadores.modelos import (
    IndicadorOut,
    RespostaIndicadores,
    RespostaValores,
    TerritorioOut,
)

router = APIRouter(prefix="/v1", tags=["indicadores"])

_POR_PAGINA_MAX = 1000


def _parse_mes(valor: str | None, campo: str) -> date | None:
    if valor is None:
        return None
    try:
        ano, mes = valor.split("-")
        return date(int(ano), int(mes), 1)
    except (ValueError, TypeError) as exc:
        raise ValidacaoError(f"'{campo}' deve estar no formato YYYY-MM") from exc


@router.get("/indicadores", response_model=RespostaIndicadores)
async def listar_indicadores(
    dominio: str | None = None,
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(100, ge=1, le=_POR_PAGINA_MAX),
    session: AsyncSession = Depends(get_session),
) -> RespostaIndicadores:
    return await IndicadoresFacade(session).listar_indicadores(
        dominio=dominio, pagina=pagina, por_pagina=por_pagina
    )


@router.get("/indicadores/{codigo}", response_model=IndicadorOut)
async def obter_indicador(
    codigo: str, session: AsyncSession = Depends(get_session)
) -> IndicadorOut:
    return await IndicadoresFacade(session).obter_indicador(codigo=codigo)


@router.get("/valores", response_model=RespostaValores)
async def listar_valores(
    indicador: str = Query(..., description="código namespaced do indicador (obrigatório)"),
    territorio: str | None = Query(None, description="codigo_ibge do território"),
    de: str | None = Query(None, description="período inicial YYYY-MM"),
    ate: str | None = Query(None, description="período final YYYY-MM"),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(100, ge=1, le=_POR_PAGINA_MAX),
    session: AsyncSession = Depends(get_session),
) -> RespostaValores:
    return await IndicadoresFacade(session).listar_valores(
        indicador=indicador,
        territorio=territorio,
        de=_parse_mes(de, "de"),
        ate=_parse_mes(ate, "ate"),
        pagina=pagina,
        por_pagina=por_pagina,
    )


@router.get("/territorios/{codigo_ibge}", response_model=TerritorioOut)
async def obter_territorio(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> TerritorioOut:
    return await IndicadoresFacade(session).obter_territorio(codigo_ibge=codigo_ibge)
