"""Rotas dos produtos nomeados. OndeFoi (TRANSP-06): execução orçamentária por função (dado vivo).
Pulso Produtivo (TRAB-01): saldo de emprego formal por município (dado real via ``/v1/valores``)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.produtos.facade import PulsoProdutivoFacade
from app.produtos.modelos import (
    OndeFoiLista,
    OndeFoiOut,
    PulsoProdutivoOut,
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
