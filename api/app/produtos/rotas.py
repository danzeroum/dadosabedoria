"""Rotas dos produtos nomeados. OndeFoi (TRANSP-06): execução orçamentária por função (grau-demo).
Pulso Produtivo (TRAB-01): saldo de emprego formal por município (dado real via ``/v1/valores``)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.erros import NaoEncontradoError
from app.produtos.dados_onde_foi import DEMO_MUNICIPIOS, META_DEMO
from app.produtos.facade import PulsoProdutivoFacade
from app.produtos.modelos import FuncaoOut, MetaOndeFoi, OndeFoiOut, PulsoProdutivoOut
from app.produtos.onde_foi import calcular

router = APIRouter(prefix="/v1", tags=["produtos"])


@router.get("/onde-foi/{codigo_ibge}", response_model=OndeFoiOut)
async def onde_foi(codigo_ibge: str) -> OndeFoiOut:
    """Do que a prefeitura empenhou por função, quanto liquidou? (Liquidado÷Empenhado — ADR-0029).

    GRAU-DEMO até o go-live ler a fato `execucao_funcao` (esteira viva do #0). ``meta.metodologia``
    enquadra: é execução **orçamentária** (empenhar≠liquidar≠serviço), NÃO serviço entregue.
    """
    reg = next((d for d in DEMO_MUNICIPIOS if d[0] == codigo_ibge), None)
    if reg is None:
        raise NaoEncontradoError(f"OndeFoi para município '{codigo_ibge}'")
    cod, nome, uf, total, funcoes = reg
    r = calcular(cod, nome, uf, total, funcoes)
    return OndeFoiOut(
        codigo_ibge=r.codigo_ibge,
        nome=r.nome,
        uf=r.uf,
        empenhado_total=r.empenhado_total,
        empenhado_base=r.empenhado_base,
        empenhado_fora_base=r.empenhado_fora_base,
        liquidado=r.liquidado,
        pct=r.pct,
        banda=r.banda,
        funcoes=[
            FuncaoOut(
                funcao=f.funcao,
                empenhado=f.empenhado,
                liquidado=f.liquidado,
                exe_estado=f.exe_estado,
                pct=f.pct,
            )
            for f in r.funcoes
        ],
        meta=MetaOndeFoi(**META_DEMO),
    )


@router.get("/pulso-produtivo/{codigo_ibge}", response_model=PulsoProdutivoOut)
async def pulso_produtivo(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> PulsoProdutivoOut:
    """Como está o pulso do emprego formal no município? Saldo CAGED (admissões − desligamentos).

    Dado **real** do acervo (mesmo Repository de ``/v1/valores``). ``nota``/``meta`` enquadram:
    emprego **formal**, fluxo volátil/sazonal — saldo negativo merece a pergunta, não é veredito.
    """
    return await PulsoProdutivoFacade(session).pulso_produtivo(codigo_ibge=codigo_ibge)
