"""Facade — orquestra Repository + cache e monta os modelos de resposta com ``meta``."""

from __future__ import annotations

from datetime import date

from sqlalchemy import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_leitura
from app.core.erros import NaoEncontradoError
from app.indicadores.modelos import (
    IndicadorOut,
    MetaProveniencia,
    Paginacao,
    RespostaIndicadores,
    RespostaValores,
    TerritorioOut,
    TerritorioRef,
    ValorOut,
)
from app.indicadores.repositorio import RepositorioIndicadores


def _meta(row: RowMapping) -> MetaProveniencia:
    return MetaProveniencia(
        indicador=row["codigo"],
        nome=row["nome"],
        fonte=row["fonte_nome"],
        metodologia=row["metodologia"],
        lag_tipico_dias=row["fonte_lag"],
        licenca=row["fonte_licenca"],
    )


def _indicador_out(row: RowMapping) -> IndicadorOut:
    return IndicadorOut(
        codigo=row["codigo"],
        nome=row["nome"],
        descricao=row["descricao"],
        dominio=row["dominio"],
        subdominio=row["subdominio"],
        unidade=row["unidade"],
        polaridade=row["polaridade"],
        atualizacao=row["atualizacao"],
        nivel_minimo_agregacao=row["nivel_minimo_agregacao"],
        metodologia=row["metodologia"],
        versao_metodologia=row["versao_metodologia"],
        meta=_meta(row),
    )


class IndicadoresFacade:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session
        self._repo = RepositorioIndicadores()

    @cache_leitura("v1:indicadores")
    async def listar_indicadores(
        self, *, dominio: str | None = None, pagina: int = 1, por_pagina: int = 100
    ) -> RespostaIndicadores:
        linhas, total = await self._repo.listar_indicadores(
            self._s, dominio=dominio, pagina=pagina, por_pagina=por_pagina
        )
        return RespostaIndicadores(
            dados=[_indicador_out(r) for r in linhas],
            paginacao=Paginacao(pagina=pagina, por_pagina=por_pagina, total=total),
        )

    @cache_leitura("v1:indicador")
    async def obter_indicador(self, *, codigo: str) -> IndicadorOut:
        row = await self._repo.obter_indicador(self._s, codigo)
        if row is None:
            raise NaoEncontradoError(f"indicador '{codigo}'")
        return _indicador_out(row)

    @cache_leitura("v1:valores")
    async def listar_valores(
        self,
        *,
        indicador: str,
        territorio: str | None = None,
        de: date | None = None,
        ate: date | None = None,
        pagina: int = 1,
        por_pagina: int = 100,
    ) -> RespostaValores:
        meta_row = await self._repo.meta_indicador(self._s, indicador)
        if meta_row is None:
            raise NaoEncontradoError(f"indicador '{indicador}'")
        linhas, total = await self._repo.listar_valores(
            self._s,
            indicador_codigo=indicador,
            territorio_codigo=territorio,
            de=de,
            ate=ate,
            pagina=pagina,
            por_pagina=por_pagina,
        )
        dados = [
            ValorOut(
                periodo=r["periodo"].strftime("%Y-%m"),
                valor=float(r["valor"]) if r["valor"] is not None else None,
                confiabilidade=r["confiabilidade"],
                suprimido=r["suprimido"],
                motivo_supressao=r["motivo_supressao"],
            )
            for r in linhas
        ]
        return RespostaValores(
            dados=dados,
            meta=_meta(meta_row),
            paginacao=Paginacao(pagina=pagina, por_pagina=por_pagina, total=total),
        )

    @cache_leitura("v1:territorio")
    async def obter_territorio(self, *, codigo_ibge: str) -> TerritorioOut:
        row = await self._repo.obter_territorio(self._s, codigo_ibge)
        if row is None:
            raise NaoEncontradoError(f"territorio '{codigo_ibge}'")
        pai = None
        if row["pai_codigo_ibge"] is not None:
            pai = TerritorioRef(
                codigo_ibge=row["pai_codigo_ibge"],
                nome=row["pai_nome"],
                nivel=row["pai_nivel"],
            )
        return TerritorioOut(
            codigo_ibge=row["codigo_ibge"],
            nome=row["nome"],
            nivel=row["nivel"],
            uf=row["uf"],
            populacao=row["populacao"],
            pai=pai,
        )
