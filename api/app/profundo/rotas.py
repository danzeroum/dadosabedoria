"""Rota do tier profundo (open-core pago): ``POST /v1/consultas-lote``, com chave de API.

Aditiva (§7) e sobre o MESMO acervo público (role_analitica, sem PII): reusa o Facade de leitura por
item. Uma consulta com erro (indicador inexistente, período inválido) vira ``erro`` naquele item —
não derruba o lote.
"""

from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.core.erros import NaoEncontradoError, ValidacaoError
from app.indicadores.facade import IndicadoresFacade
from app.profundo.api_key import requer_chave_profunda
from app.profundo.modelos import ConsultaLoteIn, RespostaLote, ResultadoLote

router = APIRouter(prefix="/v1", tags=["profundo"])


def _parse_mes(valor: str | None, campo: str) -> date | None:
    if valor is None:
        return None
    try:
        ano, mes = valor.split("-")
        return date(int(ano), int(mes), 1)
    except (ValueError, TypeError) as exc:
        raise ValidacaoError(f"'{campo}' deve estar no formato YYYY-MM") from exc


@router.post("/consultas-lote", response_model=RespostaLote)
async def consultas_lote(
    corpo: ConsultaLoteIn,
    _chave: str = Depends(requer_chave_profunda),
    session: AsyncSession = Depends(get_session),
) -> RespostaLote:
    """Tier PROFUNDO: várias consultas de valores num só request. Mesmo dado público; o que muda é
    a conveniência/escala (open-core). Requer chave de API válida (Bearer ou X-API-Key)."""
    facade = IndicadoresFacade(session)
    resultados: list[ResultadoLote] = []
    for item in corpo.consultas:
        try:
            r = await facade.listar_valores(
                indicador=item.indicador,
                territorio=item.territorio,
                de=_parse_mes(item.de, "de"),
                ate=_parse_mes(item.ate, "ate"),
                pagina=1,
                por_pagina=item.por_pagina,
            )
            resultados.append(
                ResultadoLote(
                    indicador=item.indicador,
                    territorio=item.territorio,
                    dados=r.dados,
                    meta=r.meta,
                    paginacao=r.paginacao,
                )
            )
        except (NaoEncontradoError, ValidacaoError) as exc:
            resultados.append(
                ResultadoLote(indicador=item.indicador, territorio=item.territorio, erro=str(exc))
            )
    return RespostaLote(resultados=resultados, total=len(resultados))
