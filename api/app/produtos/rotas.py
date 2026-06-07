"""Rotas dos produtos nomeados (TRANSP-*). OndeFoi: execução orçamentária por função (``/v1``)."""

from __future__ import annotations

from fastapi import APIRouter

from app.core.erros import NaoEncontradoError
from app.produtos.dados_onde_foi import DEMO_MUNICIPIOS, META_DEMO
from app.produtos.modelos import FuncaoOut, MetaOndeFoi, OndeFoiOut
from app.produtos.onde_foi import calcular

router = APIRouter(prefix="/v1", tags=["produtos"])


@router.get("/onde-foi/{codigo_ibge}", response_model=OndeFoiOut)
async def onde_foi(codigo_ibge: str) -> OndeFoiOut:
    """A transferência da União virou serviço? Recebido × execução por função (ADR-0026).

    GRAU-DEMO até a esteira (SICONFI/DCA) + a 1ª validação real no #0 — serve a fixture fiel ao
    contrato. ``meta.metodologia`` enquadra: é execução **orçamentária**, NÃO serviço entregue.
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
        recebido_total=r.recebido_total,
        recebido_base=r.recebido_base,
        recebido_fora_base=r.recebido_fora_base,
        executado=r.executado,
        pct=r.pct,
        banda=r.banda,
        funcoes=[
            FuncaoOut(
                funcao=f.funcao,
                recebido=f.recebido,
                exe=f.exe,
                exe_estado=f.exe_estado,
                pct=f.pct,
            )
            for f in r.funcoes
        ],
        meta=MetaOndeFoi(**META_DEMO),
    )
