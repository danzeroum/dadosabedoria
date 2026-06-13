"""GET /v1/frescor — status de frescor (SLA de dados) por fonte de ingestão.

Consulta a tabela ``linhagem`` para data da última execução e a tabela ``fonte`` para
metadados de periodicidade e lag típico. Não expõe PII nem dado individual.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session

router = APIRouter(prefix="/v1", tags=["frescor"])


class FonteFrescorOut(BaseModel):
    fonte: str
    nome: str
    periodicidade: str
    lag_tipico_dias: int | None
    ultima_execucao: str | None  # ISO-8601 datetime ou None se nunca executou
    dias_desde_execucao: int | None
    status: str  # ok | atencao | atrasado | sem_dado


def _status(periodicidade: str, dias: int | None) -> str:
    if dias is None:
        return "sem_dado"
    # Limiares: mensal → ok≤45d, atenção≤90d; anual → ok≤400d, atenção≤700d
    limiar_ok, limiar_atencao = (45, 90) if periodicidade == "mensal" else (400, 700)
    if dias <= limiar_ok:
        return "ok"
    if dias <= limiar_atencao:
        return "atencao"
    return "atrasado"


_SQL = text("""
    SELECT
        f.codigo,
        f.nome,
        f.atualizacao::text                         AS periodicidade,
        f.lag_tipico_dias,
        MAX(l.executado_em)                         AS ultima_execucao,
        (NOW() - MAX(l.executado_em))               AS intervalo
    FROM fonte f
    LEFT JOIN linhagem l ON l.fonte_id = f.id
    GROUP BY f.id, f.codigo, f.nome, f.atualizacao, f.lag_tipico_dias
    ORDER BY f.codigo
""")


@router.get("/frescor", response_model=list[FonteFrescorOut])
async def listar_frescor(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> list[FonteFrescorOut]:
    """Lista o status de frescor de cada fonte de dados ingerida."""
    rows = (await session.execute(_SQL)).mappings().all()
    resultado: list[FonteFrescorOut] = []
    for r in rows:
        intervalo = r["intervalo"]
        dias = int(intervalo.days) if intervalo is not None else None
        resultado.append(
            FonteFrescorOut(
                fonte=r["codigo"],
                nome=r["nome"],
                periodicidade=r["periodicidade"],
                lag_tipico_dias=r["lag_tipico_dias"],
                ultima_execucao=(
                    r["ultima_execucao"].isoformat() if r["ultima_execucao"] else None
                ),
                dias_desde_execucao=dias,
                status=_status(r["periodicidade"], dias),
            )
        )
    return resultado
