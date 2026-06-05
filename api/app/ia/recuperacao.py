"""Recuperação ancorada: busca SÓ na camada pública (não-pessoal) do repositório canônico.

A IA narra apenas sobre o ``ContextoIA`` recuperado aqui — nunca sobre conhecimento externo.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from sqlalchemy import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from app.indicadores.repositorio import RepositorioIndicadores


@dataclass
class ContextoIA:
    indicador: RowMapping  # linha completa do indicador (inclui origem_sensivel) + meta da fonte
    valores: list[RowMapping]  # série pública (suprimidos marcados, valor já NULL)
    territorio: str | None


async def catalogo(session: AsyncSession) -> list[tuple[str, str]]:
    repo = RepositorioIndicadores()
    linhas, _ = await repo.listar_indicadores(session, dominio=None, pagina=1, por_pagina=1000)
    return [(r["codigo"], r["nome"]) for r in linhas]


async def recuperar(
    session: AsyncSession,
    *,
    indicador: str,
    territorio: str | None,
    de: date | None,
    ate: date | None,
) -> ContextoIA | None:
    repo = RepositorioIndicadores()
    ind = await repo.obter_indicador(session, indicador)
    if ind is None:
        return None
    linhas, _ = await repo.listar_valores(
        session,
        indicador_codigo=indicador,
        territorio_codigo=territorio,
        de=de,
        ate=ate,
        pagina=1,
        por_pagina=100,
    )
    return ContextoIA(indicador=ind, valores=linhas, territorio=territorio)
