"""Rotas REST de leitura (camada pública, só GET) — versão no caminho (``/v1``), aditiva (§7)."""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.erros import ValidacaoError
from app.indicadores.facade import IndicadoresFacade
from app.indicadores.ivm import IVMFacade
from app.indicadores.modelos import (
    IndicadorOut,
    PanoramaOut,
    RespostaBuscaTerritorios,
    RespostaFontes,
    RespostaIndicadores,
    RespostaIVM,
    RespostaIVMSerie,
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


@router.get("/fontes", response_model=RespostaFontes, tags=["proveniencia"])
async def listar_fontes(session: AsyncSession = Depends(get_session)) -> RespostaFontes:
    """As fontes por trás de cada número: órgão, licença, cadência, lag e base legal (LGPD).

    Proveniência consolidada (invariante 5) — a transparência das fontes tornada verificável. Lê a
    tabela ``fonte``/``base_legal`` do acervo; cobertura (domínios, nº de indicadores) só dos
    indicadores **públicos**.
    """
    return await IndicadoresFacade(session).listar_fontes()


@router.get("/territorios", response_model=RespostaBuscaTerritorios)
async def buscar_territorios(
    q: str = Query(..., min_length=2, description="nome ou prefixo do código IBGE"),
    nivel: str = Query("municipio", description="nível territorial (municipio | uf)"),
    limit: int = Query(20, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
) -> RespostaBuscaTerritorios:
    """Busca municípios por nome ou prefixo de código IBGE — campo de busca das telas."""
    return await IndicadoresFacade(session).buscar_territorios(q=q, nivel=nivel, limit=limit)


@router.get("/territorios/{codigo_ibge}", response_model=TerritorioOut)
async def obter_territorio(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> TerritorioOut:
    return await IndicadoresFacade(session).obter_territorio(codigo_ibge=codigo_ibge)


@router.get("/territorios/{codigo_ibge}/panorama", response_model=PanoramaOut, tags=["panorama"])
async def panorama_territorio(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> PanoramaOut:
    """Panorama do município: o último valor de cada indicador público, com proveniência por fonte.

    404 só se o território não existir; território sem dado retorna lista vazia (honesto: existe,
    ainda sem indicadores). Célula suprimida aparece como protegida (valor nulo), nunca exposta.
    """
    return await IndicadoresFacade(session).panorama(codigo_ibge=codigo_ibge)


@router.get("/ivm", response_model=RespostaIVM, tags=["ivm"])
async def ivm_por_periodo(
    periodo: str | None = Query(None, description="período YYYY-MM (padrão: mais recente)"),
    pagina: int = Query(1, ge=1),
    por_pagina: int = Query(1000, ge=1, le=_POR_PAGINA_MAX),
    session: AsyncSession = Depends(get_session),
) -> RespostaIVM:
    """IVM de todos os municípios num período — base do mapa semafórico."""
    return await IVMFacade(session).por_periodo(
        periodo=_parse_mes(periodo, "periodo"), pagina=pagina, por_pagina=por_pagina
    )


@router.get("/ivm/{codigo_ibge}", response_model=RespostaIVMSerie, tags=["ivm"])
async def ivm_municipio(
    codigo_ibge: str,
    de: str | None = Query(None, description="período inicial YYYY-MM"),
    ate: str | None = Query(None, description="período final YYYY-MM"),
    session: AsyncSession = Depends(get_session),
) -> RespostaIVMSerie:
    """Série do IVM de um município — drill-down."""
    return await IVMFacade(session).serie(
        codigo_ibge=codigo_ibge, de=_parse_mes(de, "de"), ate=_parse_mes(ate, "ate")
    )


@router.get("/ivm/{codigo_ibge}/similares", response_model=RespostaIVMSerie, tags=["ivm"])
async def ivm_similares(
    codigo_ibge: str,
    session: AsyncSession = Depends(get_session),
) -> RespostaIVMSerie:
    """Cidades parecidas: mesma UF, IVM mais próximo no período recente — comparar no contexto."""
    return await IVMFacade(session).similares(codigo_ibge=codigo_ibge)


@router.get("/mapa/ivm", tags=["ivm"])
async def ivm_malha(
    uf: str = Query(..., description="sigla da UF (ex.: SP)"),
    periodo: str | None = Query(None, description="período YYYY-MM (padrão: mais recente)"),
    session: AsyncSession = Depends(get_session),
) -> dict:
    """GeoJSON do IVM por município de uma UF — base da coropleta geográfica."""
    return await IVMFacade(session).malha(uf=uf.upper(), periodo=_parse_mes(periodo, "periodo"))
