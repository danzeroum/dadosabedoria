"""Rota do tier profundo (open-core pago): ``POST /v1/consultas-lote``, com chave de API.

Aditiva (§7) e sobre o MESMO acervo público (role_analitica, sem PII): reusa o Facade de leitura por
item. Uma consulta com erro (indicador inexistente, período inválido) vira ``erro`` naquele item —
não derruba o lote. Rate-limiting: fixed-window 1.000 req/h por chave (configurável via env).
"""

from __future__ import annotations

import asyncio
from datetime import date

from fastapi import APIRouter, Depends, Response

from app.core.config import get_settings
from app.core.db import get_sessionmaker
from app.core.erros import NaoEncontradoError, ValidacaoError
from app.indicadores.facade import IndicadoresFacade
from app.profundo.api_key import requer_chave_profunda
from app.profundo.modelos import (
    ConsultaItem,
    ConsultaLoteIn,
    RespostaLote,
    RespostaQuota,
    ResultadoLote,
)
from app.profundo.rate_limit import consultar_quota, verificar_rate_limit

router = APIRouter(prefix="/v1", tags=["profundo"])


@router.get("/quota", response_model=RespostaQuota)
async def quota(
    cliente: str = Depends(requer_chave_profunda),
) -> RespostaQuota:
    """Tier PROFUNDO: retorna o uso atual da cota na janela em curso **sem** incrementar o contador.

    Requer chave de API válida (Bearer ou X-API-Key). Não conta como requisição para o rate-limit.
    """
    q = await consultar_quota(cliente)
    return RespostaQuota(limite=q.limite, usado=q.usado, restante=q.restante, reset=q.reset)


def _parse_mes(valor: str | None, campo: str) -> date | None:
    if valor is None:
        return None
    try:
        ano, mes = valor.split("-")
        return date(int(ano), int(mes), 1)
    except (ValueError, TypeError) as exc:
        raise ValidacaoError(f"'{campo}' deve estar no formato YYYY-MM") from exc


async def _executar_item(
    item: ConsultaItem,
    semaforo: asyncio.Semaphore,
) -> ResultadoLote:
    """Executa uma consulta individual do lote, protegida por semáforo de concorrência."""
    async with semaforo:
        async with get_sessionmaker()() as session:
            try:
                facade = IndicadoresFacade(session)
                r = await facade.listar_valores(
                    indicador=item.indicador,
                    territorio=item.territorio,
                    de=_parse_mes(item.de, "de"),
                    ate=_parse_mes(item.ate, "ate"),
                    pagina=1,
                    por_pagina=item.por_pagina,
                )
                return ResultadoLote(
                    indicador=item.indicador,
                    territorio=item.territorio,
                    dados=r.dados,
                    meta=r.meta,
                    paginacao=r.paginacao,
                )
            except (NaoEncontradoError, ValidacaoError) as exc:
                return ResultadoLote(
                    indicador=item.indicador, territorio=item.territorio, erro=str(exc)
                )


@router.post("/consultas-lote", response_model=RespostaLote)
async def consultas_lote(
    response: Response,
    corpo: ConsultaLoteIn,
    cliente: str = Depends(requer_chave_profunda),
) -> RespostaLote:
    """Tier PROFUNDO: várias consultas de valores num só request. Mesmo dado público; o que muda é
    a conveniência/escala (open-core). Requer chave de API válida (Bearer ou X-API-Key).

    Rate-limiting: fixed-window 1.000 req/h por chave (``RATE_LIMIT_PROFUNDO``). Cabeçalhos de
    resposta: ``X-RateLimit-Limit``, ``X-RateLimit-Remaining``, ``X-RateLimit-Reset``.
    Concorrência interna: ``CONCORRENCIA_LOTE`` (padrão 5, igual ao pool_size do banco).
    """
    rl = await verificar_rate_limit(cliente)
    response.headers["X-RateLimit-Limit"] = str(rl.limite)
    response.headers["X-RateLimit-Remaining"] = str(rl.restante)
    response.headers["X-RateLimit-Reset"] = str(rl.reset)

    concorrencia = get_settings().concorrencia_lote
    semaforo = asyncio.Semaphore(concorrencia)

    resultados: list[ResultadoLote] = await asyncio.gather(
        *[_executar_item(item, semaforo) for item in corpo.consultas]
    )
    return RespostaLote(resultados=list(resultados), total=len(resultados))
