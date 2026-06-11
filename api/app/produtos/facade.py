"""Facade dos produtos que leem o acervo real (cache + ``meta`` de proveniência do banco).

**Pulso Produtivo** lê o saldo CAGED **já no ar** via o mesmo Repository de ``/v1/valores`` —
reusa, não duplica a consulta. **Giro Local** reusa o mesmo repositório para CAGED + ESTBAN.
OndeFoi usa o seu próprio ``RepositorioOndeFoi``.
"""

from __future__ import annotations

from sqlalchemy import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_leitura
from app.core.erros import NaoEncontradoError
from app.indicadores.modelos import MetaProveniencia
from app.indicadores.repositorio import RepositorioIndicadores
from app.produtos.giro_local import (
    NOTA_HONESTA as NOTA_GIRO,
)
from app.produtos.giro_local import (
    calcular as calcular_giro,
)
from app.produtos.modelos import GiroLocalOut, MesSaldoOut, PulsoProdutivoOut
from app.produtos.pulso_produtivo import NOTA_HONESTA, MesSaldo, calcular

CODIGO_CAGED = "trabalho.emprego.saldo_caged"
CODIGO_ESTBAN = "credito.operacoes.saldo_total"
_POR_PAGINA = 1000  # série mensal de um município cabe folgada numa página.


def _meta(row: RowMapping) -> MetaProveniencia:
    return MetaProveniencia(
        indicador=row["codigo"],
        nome=row["nome"],
        fonte=row["fonte_nome"],
        metodologia=row["metodologia"],
        lag_tipico_dias=row["fonte_lag"],
        licenca=row["fonte_licenca"],
    )


class PulsoProdutivoFacade:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session
        self._repo = RepositorioIndicadores()

    @cache_leitura("v1:pulso")
    async def pulso_produtivo(self, *, codigo_ibge: str) -> PulsoProdutivoOut:
        terr = await self._repo.obter_territorio(self._s, codigo_ibge)
        if terr is None:
            raise NaoEncontradoError(f"território '{codigo_ibge}'")
        meta_row = await self._repo.meta_indicador(self._s, CODIGO_CAGED)
        if meta_row is None:  # pragma: no cover - indicador sempre semeado
            raise NaoEncontradoError(f"indicador '{CODIGO_CAGED}'")

        linhas, _ = await self._repo.listar_valores(
            self._s,
            indicador_codigo=CODIGO_CAGED,
            territorio_codigo=codigo_ibge,
            de=None,
            ate=None,
            pagina=1,
            por_pagina=_POR_PAGINA,
        )
        # Só meses divulgados (valor não suprimido); o saldo CAGED nunca suprime (n_minimo=0).
        meses = [
            MesSaldo(periodo=r["periodo"].strftime("%Y-%m"), saldo=int(r["valor"]))
            for r in linhas
            if r["valor"] is not None
        ]
        if not meses:
            raise NaoEncontradoError(f"Pulso Produtivo para município '{codigo_ibge}'")

        p = calcular(terr["codigo_ibge"], terr["nome"], terr["uf"], meses)
        return PulsoProdutivoOut(
            codigo_ibge=p.codigo_ibge,
            nome=p.nome,
            uf=p.uf,
            periodo=p.periodo,
            saldo_mes=p.saldo_mes,
            saldo_acumulado=p.saldo_acumulado,
            pulso=p.pulso,
            tendencia=p.tendencia,
            meses_positivos=p.meses_positivos,
            meses_negativos=p.meses_negativos,
            meses=[MesSaldoOut(periodo=m.periodo, saldo=m.saldo) for m in p.meses],
            nota=NOTA_HONESTA,
            meta=_meta(meta_row),
        )


class GiroLocalFacade:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session
        self._repo = RepositorioIndicadores()

    @cache_leitura("v1:giro")
    async def giro_local(self, *, codigo_ibge: str) -> GiroLocalOut:
        terr = await self._repo.obter_territorio(self._s, codigo_ibge)
        if terr is None:
            raise NaoEncontradoError(f"território '{codigo_ibge}'")

        meta_caged = await self._repo.meta_indicador(self._s, CODIGO_CAGED)
        meta_estban = await self._repo.meta_indicador(self._s, CODIGO_ESTBAN)

        # CAGED: último mês disponível (saldo do mês mais recente)
        linhas_caged, _ = await self._repo.listar_valores(
            self._s,
            indicador_codigo=CODIGO_CAGED,
            territorio_codigo=codigo_ibge,
            de=None,
            ate=None,
            pagina=1,
            por_pagina=_POR_PAGINA,
        )
        caged_rows = [r for r in linhas_caged if r["valor"] is not None]
        saldo_emprego: int | None = None
        periodo_emprego: str | None = None
        if caged_rows:
            ultimo_caged = caged_rows[-1]
            saldo_emprego = int(ultimo_caged["valor"])
            periodo_emprego = ultimo_caged["periodo"].strftime("%Y-%m")

        # ESTBAN: último mês disponível
        linhas_estban, _ = await self._repo.listar_valores(
            self._s,
            indicador_codigo=CODIGO_ESTBAN,
            territorio_codigo=codigo_ibge,
            de=None,
            ate=None,
            pagina=1,
            por_pagina=_POR_PAGINA,
        )
        estban_rows = [r for r in linhas_estban if r["valor"] is not None]
        saldo_credito: int | None = None
        periodo_credito: str | None = None
        if estban_rows:
            ultimo_estban = estban_rows[-1]
            saldo_credito = int(ultimo_estban["valor"])
            periodo_credito = ultimo_estban["periodo"].strftime("%Y-%m")

        if saldo_emprego is None and saldo_credito is None:
            raise NaoEncontradoError(f"Giro Local para município '{codigo_ibge}'")

        g = calcular_giro(
            terr["codigo_ibge"],
            terr["nome"],
            terr["uf"],
            terr["populacao"],
            periodo_emprego=periodo_emprego,
            saldo_emprego=saldo_emprego,
            periodo_credito=periodo_credito,
            saldo_credito=saldo_credito,
        )
        return GiroLocalOut(
            codigo_ibge=g.codigo_ibge,
            nome=g.nome,
            uf=g.uf,
            populacao=g.populacao,
            periodo_emprego=g.periodo_emprego,
            saldo_emprego=g.saldo_emprego,
            saldo_emprego_per_1000=g.saldo_emprego_per_1000,
            nivel_emprego=g.nivel_emprego,
            periodo_credito=g.periodo_credito,
            saldo_credito=g.saldo_credito,
            saldo_credito_per_hab=g.saldo_credito_per_hab,
            nivel_credito=g.nivel_credito,
            nota=NOTA_GIRO,
            meta_emprego=_meta(meta_caged) if meta_caged else None,
            meta_credito=_meta(meta_estban) if meta_estban else None,
        )
