"""Repository (SQLAlchemy Core) — consultas parametrizadas, sem N+1, sobre a camada analítica.

Privacidade: a série lê de ``valor`` apenas para indicadores ``publico=true`` e força ``NULL`` em
célula suprimida via ``CASE`` (dupla proteção — a camada ouro já grava NULL ao suprimir). Assim a
resposta pode sinalizar a célula protegida (UX, esquema §8) sem nunca expor um valor suprimido.
A view canônica ``valor_publico`` (valores-only) permanece como base das agregações/IVM.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import RowMapping, and_, case, distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.tables import base_legal, fonte, indicador, territorio, valor


def _cols_meta() -> list:
    return [
        indicador.c.codigo,
        indicador.c.nome,
        indicador.c.metodologia,
        fonte.c.nome.label("fonte_nome"),
        fonte.c.licenca.label("fonte_licenca"),
        fonte.c.lag_tipico_dias.label("fonte_lag"),
    ]


class RepositorioIndicadores:
    async def listar_indicadores(
        self, session: AsyncSession, *, dominio: str | None, pagina: int, por_pagina: int
    ) -> tuple[list[RowMapping], int]:
        j = indicador.join(fonte, fonte.c.id == indicador.c.fonte_id)
        base = select(indicador, *_cols_meta()[3:]).select_from(j)
        cont = select(func.count()).select_from(indicador)
        if dominio:
            base = base.where(indicador.c.dominio == dominio)
            cont = cont.where(indicador.c.dominio == dominio)
        base = base.order_by(indicador.c.codigo).limit(por_pagina).offset((pagina - 1) * por_pagina)
        linhas = (await session.execute(base)).mappings().all()
        total = (await session.execute(cont)).scalar_one()
        return list(linhas), int(total)

    async def obter_indicador(self, session: AsyncSession, codigo: str) -> RowMapping | None:
        j = indicador.join(fonte, fonte.c.id == indicador.c.fonte_id)
        stmt = (
            select(indicador, *_cols_meta()[3:]).select_from(j).where(indicador.c.codigo == codigo)
        )
        return (await session.execute(stmt)).mappings().first()

    async def meta_indicador(self, session: AsyncSession, codigo: str) -> RowMapping | None:
        j = indicador.join(fonte, fonte.c.id == indicador.c.fonte_id)
        stmt = select(*_cols_meta()).select_from(j).where(indicador.c.codigo == codigo)
        return (await session.execute(stmt)).mappings().first()

    async def listar_valores(
        self,
        session: AsyncSession,
        *,
        indicador_codigo: str,
        territorio_codigo: str | None,
        de: date | None,
        ate: date | None,
        pagina: int,
        por_pagina: int,
    ) -> tuple[list[RowMapping], int]:
        valor_seguro = case((valor.c.suprimido, None), else_=valor.c.valor).label("valor")
        j = valor.join(indicador, indicador.c.id == valor.c.indicador_id).join(
            territorio, territorio.c.id == valor.c.territorio_id
        )
        filtros = [indicador.c.codigo == indicador_codigo, indicador.c.publico.is_(True)]
        if territorio_codigo:
            filtros.append(territorio.c.codigo_ibge == territorio_codigo)
        if de:
            filtros.append(valor.c.periodo >= de)
        if ate:
            filtros.append(valor.c.periodo <= ate)

        base = (
            select(
                valor.c.periodo,
                valor_seguro,
                valor.c.confiabilidade,
                valor.c.suprimido,
                valor.c.motivo_supressao,
            )
            .select_from(j)
            .where(*filtros)
            .order_by(valor.c.periodo)
            .limit(por_pagina)
            .offset((pagina - 1) * por_pagina)
        )
        cont = select(func.count()).select_from(j).where(*filtros)
        linhas = (await session.execute(base)).mappings().all()
        total = (await session.execute(cont)).scalar_one()
        return list(linhas), int(total)

    async def panorama_municipio(
        self, session: AsyncSession, *, codigo_ibge: str
    ) -> list[RowMapping]:
        """Último valor de CADA indicador público para o território — uma consulta, sem N+1.

        ``DISTINCT ON (indicador.codigo)`` + ordem por período/versão desc ⇒ a célula mais recente
        por indicador. Lê de ``valor`` (não de ``valor_publico``) para **mostrar** a célula
        suprimida como protegida, forçando ``NULL`` no valor (nunca expõe o suprimido).
        """
        valor_seguro = case((valor.c.suprimido, None), else_=valor.c.valor).label("valor")
        j = (
            valor.join(indicador, indicador.c.id == valor.c.indicador_id)
            .join(territorio, territorio.c.id == valor.c.territorio_id)
            .join(fonte, fonte.c.id == indicador.c.fonte_id)
        )
        stmt = (
            select(
                indicador.c.codigo,
                indicador.c.nome,
                indicador.c.dominio,
                indicador.c.subdominio,
                indicador.c.unidade,
                indicador.c.polaridade,
                indicador.c.metodologia,
                valor.c.periodo,
                valor_seguro,
                valor.c.suprimido,
                valor.c.motivo_supressao,
                fonte.c.nome.label("fonte_nome"),
                fonte.c.lag_tipico_dias.label("fonte_lag"),
            )
            .select_from(j)
            .where(territorio.c.codigo_ibge == codigo_ibge, indicador.c.publico.is_(True))
            .distinct(indicador.c.codigo)
            .order_by(indicador.c.codigo, valor.c.periodo.desc(), valor.c.versao.desc())
        )
        return list((await session.execute(stmt)).mappings().all())

    async def listar_fontes(self, session: AsyncSession) -> list[RowMapping]:
        """Fontes do acervo + cobertura (domínios e nº de indicadores PÚBLICos), em uma consulta.

        Outer join nos indicadores públicos: uma fonte sem indicador público ainda aparece (com
        ``dominios=[]`` e ``n_indicadores=0``) — honesto sobre o que existe. A fonte sem casamento
        agrega ``{NULL}`` em ``dominios``; o ``None`` é descartado na facade (sem bind de NULL
        sem-tipo no SQL). ``count(distinct ...)`` já ignora NULL → 0 na cobertura vazia.
        """
        j = fonte.join(base_legal, base_legal.c.id == fonte.c.base_legal_id).outerjoin(
            indicador,
            and_(indicador.c.fonte_id == fonte.c.id, indicador.c.publico.is_(True)),
        )
        stmt = (
            select(
                fonte.c.codigo,
                fonte.c.nome,
                fonte.c.orgao,
                fonte.c.url_doc,
                fonte.c.licenca,
                fonte.c.atualizacao,
                fonte.c.lag_tipico_dias,
                fonte.c.permite_uso_comercial,
                fonte.c.permite_redistribuicao,
                base_legal.c.artigo.label("base_legal_artigo"),
                base_legal.c.hipotese.label("base_legal_hipotese"),
                func.array_agg(distinct(indicador.c.dominio)).label("dominios"),
                func.count(distinct(indicador.c.codigo)).label("n_indicadores"),
            )
            .select_from(j)
            .group_by(fonte.c.id, base_legal.c.id)
            .order_by(fonte.c.nome)
        )
        return list((await session.execute(stmt)).mappings().all())

    async def obter_territorio(self, session: AsyncSession, codigo_ibge: str) -> RowMapping | None:
        pai = territorio.alias("pai")
        j = territorio.outerjoin(pai, pai.c.id == territorio.c.pai_id)
        stmt = (
            select(
                territorio.c.codigo_ibge,
                territorio.c.nome,
                territorio.c.nivel,
                territorio.c.uf,
                territorio.c.populacao,
                pai.c.codigo_ibge.label("pai_codigo_ibge"),
                pai.c.nome.label("pai_nome"),
                pai.c.nivel.label("pai_nivel"),
            )
            .select_from(j)
            .where(territorio.c.codigo_ibge == codigo_ibge)
        )
        return (await session.execute(stmt)).mappings().first()
