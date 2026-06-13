"""Rotas de analytics inferencial — distribuição nacional e perfil orçamentário (SICONFI)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.erros import NaoEncontradoError
from app.inferencia import repositorio as repo
from app.inferencia.modelos import DistribuicaoFuncaoOut, FuncaoPerfilItem, PerfilOrcamentarioOut

router = APIRouter(prefix="/v1/inferencia", tags=["inferencia"])

_NOTA_PERFIL = (
    "Perfil orçamentário calculado sobre despesas liquidadas por função "
    "(SICONFI Anexo I-E, Portaria 42/1999). "
    "O percentil compara o município com todos os demais com dado no mesmo exercício: "
    "percentil 0 = menor gasto, percentil 100 = maior gasto per capita. "
    "Exceto a função específica ser a mais ou menos relevante para o município, "
    "o percentil NÃO implica boa ou má gestão — é só contexto de escala. "
    "Dado agregado por município — sem identificação de pessoas (dupla face §17). "
    "Lag típico: ~12 meses após o exercício de referência."
)


@router.get(
    "/distribuicao-funcao/{funcao_cod}",
    response_model=DistribuicaoFuncaoOut,
    summary="Distribuição nacional de investimento per capita em uma função SICONFI",
)
async def distribuicao_funcao(
    funcao_cod: str,
    session: AsyncSession = Depends(get_session),
) -> DistribuicaoFuncaoOut:
    if not await repo.funcao_existe(session, funcao_cod):
        raise NaoEncontradoError(f"função SICONFI '{funcao_cod}'")

    stats = await repo.distribuicao_funcao(session, funcao_cod)
    if stats is None:
        raise NaoEncontradoError(f"distribuição para função '{funcao_cod}'")

    def _f(v: object) -> float | None:
        return float(v) if v is not None else None  # type: ignore[arg-type]

    return DistribuicaoFuncaoOut(
        funcao_cod=funcao_cod,
        funcao_nome=stats["funcao_nome"],
        ano=stats["ano"],
        n_municipios=stats["n"],
        media_brl_hab=_f(stats["media"]),
        mediana_brl_hab=_f(stats["mediana"]),
        desvio_padrao=_f(stats["desvio"]),
        p10=_f(stats["p10"]),
        p25=_f(stats["p25"]),
        p75=_f(stats["p75"]),
        p90=_f(stats["p90"]),
        minimo=_f(stats["minimo"]),
        maximo=_f(stats["maximo"]),
    )


@router.get(
    "/municipio/{ibge}/orcamento",
    response_model=PerfilOrcamentarioOut,
    summary="Perfil orçamentário municipal: todas as funções SICONFI com percentil nacional",
)
async def perfil_orcamentario(
    ibge: str,
    session: AsyncSession = Depends(get_session),
) -> PerfilOrcamentarioOut:
    terr = await repo.obter_territorio(session, ibge)
    if terr is None:
        raise NaoEncontradoError(f"território '{ibge}'")

    rows = await repo.perfil_orcamentario(session, terr["id"])
    if not rows:
        raise NaoEncontradoError(f"dados orçamentários para município '{ibge}'")

    ano: int | None = rows[0].get("ano") if rows else None

    def _f(v: object) -> float | None:
        return float(v) if v is not None else None  # type: ignore[arg-type]

    funcoes = [
        FuncaoPerfilItem(
            funcao_cod=r["funcao_cod"],
            funcao_nome=r["funcao_nome"],
            valor_liquidado=_f(r["valor_liquidado"]),
            valor_por_hab=_f(r["valor_por_hab"]),
            percentil=_f(r["percentil"]),
        )
        for r in rows
    ]

    return PerfilOrcamentarioOut(
        codigo_ibge=terr["codigo_ibge"],
        nome=terr["nome"],
        uf=terr["uf"],
        populacao=terr["populacao"],
        ano=ano,
        funcoes=funcoes,
        nota=_NOTA_PERFIL,
    )
