"""Rotas do serviço de consentimento — ciclo LGPD: consentir → acessar → revogar → eliminar."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.consentimento import repositorio
from app.consentimento.auth import cidadao_atual, definir_cookie, emitir_token, limpar_cookie
from app.consentimento.cripto import hash_contato
from app.consentimento.db import get_consent_session
from app.consentimento.modelos import (
    AlertaIn,
    AlertaOut,
    LoginIn,
    NotificacaoOut,
    RespostaLogin,
)
from app.core.erros import NaoEncontradoError

router = APIRouter(prefix="/v1", tags=["consentimento"])


@router.post("/auth/login", response_model=RespostaLogin)
async def login(dados: LoginIn, resposta: Response) -> RespostaLogin:
    """Login simples (v1): emite JWT curto em cookie HttpOnly. OIDC real é plugue futuro."""
    sub = hash_contato(dados.email)
    definir_cookie(resposta, emitir_token(sub))
    return RespostaLogin(autenticado=True, sub=sub)


@router.post("/auth/logout")
async def logout(resposta: Response) -> dict:
    limpar_cookie(resposta)
    return {"ok": True}


@router.post("/alertas", response_model=AlertaOut, status_code=status.HTTP_201_CREATED)
async def criar_alerta(
    dados: AlertaIn,
    sub: str = Depends(cidadao_atual),
    session: AsyncSession = Depends(get_consent_session),
) -> AlertaOut:
    aid = await repositorio.assinar(
        session,
        contato_hash=sub,
        territorio_codigo=dados.territorio,
        finalidade=dados.finalidade,
        condicao_sensivel=dados.condicao_sensivel,
    )
    return AlertaOut(
        id=aid,
        territorio=dados.territorio,
        finalidade=dados.finalidade,
        consentido_em=datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
        condicao_sensivel=bool(dados.condicao_sensivel),
    )


@router.get("/alertas", response_model=list[AlertaOut])
async def listar_alertas(
    sub: str = Depends(cidadao_atual),
    session: AsyncSession = Depends(get_consent_session),
) -> list[AlertaOut]:
    linhas = await repositorio.listar(session, sub)
    return [
        AlertaOut(
            id=r["id"],
            territorio=r["codigo_ibge"],
            finalidade=r["finalidade"],
            consentido_em=r["consentido_em"].strftime("%Y-%m-%dT%H:%M:%SZ"),
            condicao_sensivel=r["tem_condicao"],
        )
        for r in linhas
    ]


@router.delete("/alertas/{alerta_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revogar_alerta(
    alerta_id: int,
    sub: str = Depends(cidadao_atual),
    session: AsyncSession = Depends(get_consent_session),
) -> None:
    if not await repositorio.revogar(session, sub, alerta_id):
        raise NaoEncontradoError(f"alerta {alerta_id}")


@router.get("/notificacoes", response_model=list[NotificacaoOut])
async def listar_notificacoes(
    sub: str = Depends(cidadao_atual),
    session: AsyncSession = Depends(get_consent_session),
) -> list[NotificacaoOut]:
    """Alertas consumidos para o cidadão (entrega pull; o contato bruto nunca é guardado)."""
    linhas = await repositorio.listar_notificacoes(session, sub)
    return [
        NotificacaoOut(
            id=r["id"],
            territorio=r["codigo_ibge"],
            periodo=r["periodo"].strftime("%Y-%m"),
            ivm=float(r["ivm"]),
            semaforo=r["semaforo"],
            fonte=r["fonte"],
            metodologia=r["metodologia"],
            criada_em=r["criada_em"].strftime("%Y-%m-%dT%H:%M:%SZ"),
            lida=r["lida"],
        )
        for r in linhas
    ]


@router.delete("/eu", status_code=status.HTTP_204_NO_CONTENT)
async def eliminar_meus_dados(
    sub: str = Depends(cidadao_atual),
    session: AsyncSession = Depends(get_consent_session),
) -> None:
    """Direito de eliminação (LGPD Art. 18)."""
    await repositorio.eliminar(session, sub)
