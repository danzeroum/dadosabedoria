"""Recuperação ancorada: busca SÓ na camada pública (não-pessoal) do repositório canônico.

A IA narra apenas sobre o ``ContextoIA`` recuperado aqui — nunca sobre conhecimento externo.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from sqlalchemy import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from app.indicadores.repositorio import RepositorioIndicadores


@dataclass
class ContextoIA:
    indicador: RowMapping  # linha completa do indicador (inclui origem_sensivel) + meta da fonte
    valores: list[RowMapping]  # série pública (suprimidos marcados, valor já NULL)
    territorio: str | None
    territorio_nome: str | None = field(default=None)  # nome legível do território (se resolvido)


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
    # Resolve nome do território para exibição legível no narrador.
    territorio_nome: str | None = None
    if territorio:
        terr = await repo.obter_territorio(session, territorio)
        if terr is not None:
            uf = terr["uf"]
            territorio_nome = f"{terr['nome']}{f' ({uf})' if uf else ''}"
    return ContextoIA(
        indicador=ind,
        valores=linhas,
        territorio=territorio,
        territorio_nome=territorio_nome,
    )
