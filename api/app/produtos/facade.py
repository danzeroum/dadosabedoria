"""Facade dos produtos que leem o acervo real (cache + ``meta`` de proveniência do banco).

**Pulso Produtivo** lê o saldo CAGED **já no ar** via o mesmo Repository de ``/v1/valores`` —
reusa, não duplica a consulta. OndeFoi usa o seu próprio ``RepositorioOndeFoi``.
"""

from __future__ import annotations

from sqlalchemy import RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_leitura
from app.core.erros import NaoEncontradoError
from app.indicadores.modelos import MetaProveniencia
from app.indicadores.repositorio import RepositorioIndicadores
from app.produtos.modelos import MesSaldoOut, PulsoProdutivoOut
from app.produtos.pulso_produtivo import NOTA_HONESTA, MesSaldo, calcular

CODIGO_CAGED = "trabalho.emprego.saldo_caged"
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
