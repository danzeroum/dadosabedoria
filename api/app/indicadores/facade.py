"""Facade — orquestra Repository + cache e monta os modelos de resposta com ``meta``."""

from __future__ import annotations

from datetime import date

from sqlalchemy import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_leitura
from app.core.erros import NaoEncontradoError
from app.indicadores.modelos import (
    CoberturaCAGED,
    CoberturaDatasus,
    CoberturaInep,
    CoberturaPncp,
    CoberturaSiconfi,
    CoberturaSnis,
    FonteAcervoOut,
    IndicadorOut,
    IndicadorValorOut,
    MetaProveniencia,
    Paginacao,
    PanoramaOut,
    RespostaBuscaTerritorios,
    RespostaFontes,
    RespostaIndicadores,
    RespostaValores,
    TerritorioOut,
    TerritorioRef,
    TerritorioSimples,
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

    @cache_leitura("v1:panorama")
    async def panorama(self, *, codigo_ibge: str) -> PanoramaOut:
        terr = await self._repo.obter_territorio(self._s, codigo_ibge)
        if terr is None:
            raise NaoEncontradoError(f"território '{codigo_ibge}'")
        linhas = await self._repo.panorama_municipio(self._s, codigo_ibge=codigo_ibge)
        indicadores = [
            IndicadorValorOut(
                codigo=r["codigo"],
                nome=r["nome"],
                dominio=r["dominio"],
                subdominio=r["subdominio"],
                unidade=r["unidade"],
                polaridade=r["polaridade"],
                periodo=r["periodo"].strftime("%Y-%m"),
                valor=float(r["valor"]) if r["valor"] is not None else None,
                suprimido=r["suprimido"],
                motivo_supressao=r["motivo_supressao"],
                fonte=r["fonte_nome"],
                lag_tipico_dias=r["fonte_lag"],
                metodologia=r["metodologia"],
            )
            for r in linhas
        ]
        return PanoramaOut(
            codigo_ibge=terr["codigo_ibge"],
            nome=terr["nome"],
            nivel=terr["nivel"],
            uf=terr["uf"],
            indicadores=indicadores,
        )

    @cache_leitura("v1:fontes")
    async def listar_fontes(self) -> RespostaFontes:
        linhas = await self._repo.listar_fontes(self._s)
        dados = [
            FonteAcervoOut(
                codigo=r["codigo"],
                nome=r["nome"],
                orgao=r["orgao"],
                url_doc=r["url_doc"],
                licenca=r["licenca"],
                atualizacao=r["atualizacao"],
                lag_tipico_dias=r["lag_tipico_dias"],
                permite_uso_comercial=r["permite_uso_comercial"],
                permite_redistribuicao=r["permite_redistribuicao"],
                base_legal_artigo=r["base_legal_artigo"],
                base_legal_hipotese=r["base_legal_hipotese"],
                dominios=sorted(d for d in (r["dominios"] or []) if d is not None),
                n_indicadores=r["n_indicadores"],
            )
            for r in linhas
        ]
        return RespostaFontes(dados=dados, total=len(dados))

    async def buscar_territorios(
        self, *, q: str, nivel: str = "municipio", limit: int = 20
    ) -> RespostaBuscaTerritorios:
        q = q.strip()
        if not q:
            return RespostaBuscaTerritorios(dados=[], total=0)
        rows = await self._repo.buscar_territorios(self._s, q=q, nivel=nivel, limit=limit)
        dados = [
            TerritorioSimples(codigo_ibge=r["codigo_ibge"], nome=r["nome"], uf=r["uf"])
            for r in rows
        ]
        return RespostaBuscaTerritorios(dados=dados, total=len(dados))

    @cache_leitura("v1:cobertura:caged")
    async def cobertura_caged(self) -> CoberturaCAGED:
        """Cobertura atual do CAGED — detecta modo demonstração automaticamente."""
        n = await self._repo.contar_municipios_caged(self._s)
        demo = n < 50
        aviso = (
            (
                f"Dados de demonstração: {n} município{'s' if n != 1 else ''} no acervo (seed de "
                "teste). O aviso cai automaticamente após a ingestão nacional do CAGED (~5.500 "
                "municípios)."
            )
            if demo
            else None
        )
        return CoberturaCAGED(n_municipios=n, demo=demo, aviso=aviso)

    @cache_leitura("v1:cobertura:snis")
    async def cobertura_snis(self) -> CoberturaSnis:
        """Cobertura atual do SNIS — detecta modo demonstração automaticamente."""
        n = await self._repo.contar_municipios_snis(self._s)
        demo = n < 50
        aviso = (
            (
                f"Dados de demonstração: {n} município{'s' if n != 1 else ''} no acervo (seed de "
                "teste). O aviso cai automaticamente após a ingestão nacional do SNIS (~5.500 "
                "municípios)."
            )
            if demo
            else None
        )
        return CoberturaSnis(n_municipios=n, demo=demo, aviso=aviso)

    @cache_leitura("v1:cobertura:datasus")
    async def cobertura_datasus(self) -> CoberturaDatasus:
        """Cobertura atual do DATASUS/SIH — detecta modo demonstração automaticamente."""
        n = await self._repo.contar_municipios_datasus(self._s)
        demo = n < 50
        aviso = (
            (
                f"Dados de demonstração: {n} município{'s' if n != 1 else ''} no acervo (seed de "
                "teste). O aviso cai automaticamente após a ingestão nacional do DATASUS/SIH "
                "(~5.500 municípios)."
            )
            if demo
            else None
        )
        return CoberturaDatasus(n_municipios=n, demo=demo, aviso=aviso)

    @cache_leitura("v1:cobertura:inep")
    async def cobertura_inep(self) -> CoberturaInep:
        """Cobertura atual do INEP/Censo Escolar — detecta modo demonstração automaticamente."""
        n = await self._repo.contar_municipios_inep(self._s)
        demo = n < 50
        aviso = (
            (
                f"Dados de demonstração: {n} município{'s' if n != 1 else ''} no acervo (seed de "
                "teste). O aviso cai automaticamente após a ingestão nacional do INEP/Censo "
                "Escolar (~5.500 municípios)."
            )
            if demo
            else None
        )
        return CoberturaInep(n_municipios=n, demo=demo, aviso=aviso)

    @cache_leitura("v1:cobertura:pncp")
    async def cobertura_pncp(self) -> CoberturaPncp:
        """Cobertura atual do PNCP — detecta modo demonstração automaticamente."""
        n = await self._repo.contar_municipios_pncp(self._s)
        demo = n < 50
        aviso = (
            (
                f"Dados de demonstração: {n} município{'s' if n != 1 else ''} no acervo (seed de "
                "teste). O aviso cai automaticamente após a ingestão nacional do PNCP (~5.500 "
                "municípios)."
            )
            if demo
            else None
        )
        return CoberturaPncp(n_municipios=n, demo=demo, aviso=aviso)

    @cache_leitura("v1:cobertura:siconfi")
    async def cobertura_siconfi(self) -> CoberturaSiconfi:
        """Cobertura atual do SICONFI/STN — detecta modo demonstração automaticamente."""
        n = await self._repo.contar_municipios_siconfi(self._s)
        demo = n < 50
        aviso = (
            (
                f"Dados de demonstração: {n} município{'s' if n != 1 else ''} no acervo (seed de "
                "teste). O aviso cai automaticamente após a ingestão nacional do SICONFI "
                "(~5.500 municípios)."
            )
            if demo
            else None
        )
        return CoberturaSiconfi(n_municipios=n, demo=demo, aviso=aviso)

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
