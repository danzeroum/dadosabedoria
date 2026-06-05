"""Rota da IA ancorada. Montada no monólito (api) por ora; o serviço `ai` é o ponto de extração."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.ia.modelos import PerguntaIA, RespostaIA
from app.ia.servico import ServicoIA

router = APIRouter(prefix="/v1/ia", tags=["ia"])


@router.post("/perguntar", response_model=RespostaIA)
async def perguntar(
    pergunta: PerguntaIA, session: AsyncSession = Depends(get_session)
) -> RespostaIA:
    """Responde SÓ com o que recupera do repositório, com citação; sem dado, abstém-se."""
    return await ServicoIA(session).perguntar(pergunta)
