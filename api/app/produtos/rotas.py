"""Rotas dos produtos nomeados: OndeFoi, Pulso Produtivo (TRAB-01), Giro Local (TRAB-03),
Salário Radar (TRAB-02)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.produtos.facade import GiroLocalFacade, PulsoProdutivoFacade, SalarioRadarFacade
from app.produtos.modelos import (
    GiroLocalOut,
    OndeFoiLista,
    OndeFoiOut,
    PulsoProdutivoOut,
    SalarioRadarOut,
)
from app.produtos.repositorio_onde_foi import RepositorioOndeFoi

router = APIRouter(prefix="/v1", tags=["produtos"])

_repo_onde_foi = RepositorioOndeFoi()


@router.get("/onde-foi", response_model=OndeFoiLista)
async def onde_foi_lista(session: AsyncSession = Depends(get_session)) -> OndeFoiLista:
    """Diretório dos municípios do OndeFoi — ordenado por nome (dupla-face §17, não ranking).

    Lista os municípios com dado real na fato ``execucao_funcao`` (SICONFI/Anexo I-E). Retorna
    lista vazia quando nenhum dado foi ingerido ainda.
    """
    return await _repo_onde_foi.listar(session)


@router.get("/onde-foi/{codigo_ibge}", response_model=OndeFoiOut)
async def onde_foi(codigo_ibge: str, session: AsyncSession = Depends(get_session)) -> OndeFoiOut:
    """Do que a prefeitura empenhou por função, quanto liquidou? (Liquidado÷Empenhado — ADR-0029).

    ``meta.metodologia`` enquadra: é execução **orçamentária** (empenhar≠liquidar≠serviço
    entregue). 404 quando não há dado para o município.
    """
    return await _repo_onde_foi.obter(session, codigo_ibge=codigo_ibge)


@router.get("/pulso-produtivo/{codigo_ibge}", response_model=PulsoProdutivoOut)
async def pulso_produtivo(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> PulsoProdutivoOut:
    """Como está o pulso do emprego formal no município? Saldo CAGED (admissões − desligamentos).

    Dado **real** do acervo (mesmo Repository de ``/v1/valores``). ``nota``/``meta`` enquadram:
    emprego **formal**, fluxo volátil/sazonal — saldo negativo merece a pergunta, não é veredito.
    """
    return await PulsoProdutivoFacade(session).pulso_produtivo(codigo_ibge=codigo_ibge)


@router.get("/giro-local/{codigo_ibge}", response_model=GiroLocalOut)
async def giro_local(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> GiroLocalOut:
    """Dinamismo econômico local per capita: criação de emprego formal + crédito bancário.

    Combina CAGED (saldo/1000 hab) e ESTBAN (crédito/hab) para comparação entre municípios de
    portes diferentes. 404 quando não há nenhum dado disponível para o município.
    """
    return await GiroLocalFacade(session).giro_local(codigo_ibge=codigo_ibge)


@router.get("/salario-radar/{codigo_ibge}", response_model=SalarioRadarOut)
async def salario_radar(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> SalarioRadarOut:
    """Nível salarial das novas contratações formais no município (Salário Radar — TRAB-02).

    Salário médio declarado nas admissões do Novo CAGED do último mês disponível. Revela o
    patamar salarial da demanda por trabalho formal local — não o salário médio da população.
    404 quando não há dado para o município.
    """
    return await SalarioRadarFacade(session).salario_radar(codigo_ibge=codigo_ibge)
