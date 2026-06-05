"""Caminho de escrita da camada OURO — o ÚNICO ponto de chamada da regra de supressão.

Tanto o seed quanto a futura ingestão real chamam ``escrever_ouro``. Ele:

1. aplica a regra única de supressão (k-anonimato) a cada célula — ANTES de gravar (invariante 1);
2. grava a linha em ``valor`` (célula suprimida vira ``valor=NULL, suprimido=true``);
3. registra UMA linha de ``linhagem`` por lote (proveniência, invariante 5).

Idempotente: ``ON CONFLICT (indicador_id, territorio_id, periodo, versao) DO UPDATE`` — reexecutar
o seed/pipeline é seguro (§15).

ATENÇÃO (mantido por teste no quality gate): a escrita na fato (alias ``t_valor``) e a chamada
``.aplicar(`` só podem aparecer aqui. Não grave a fato por nenhum outro lugar — nem com SQL cru.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import insert
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core import metricas
from app.core.tables import linhagem as t_linhagem
from app.core.tables import valor as t_valor
from app.ingestao.supressao import (
    EstrategiaSupressao,
    MetaIndicadorSupressao,
    ResultadoSupressao,
    SupressaoKAnonimato,
)


@dataclass(frozen=True)
class CelulaOuro:
    """Uma célula indicador×território×período antes da supressão."""

    indicador_id: int
    territorio_id: int
    periodo: date
    atualizacao: str  # valor do enum periodicidade
    valor: Decimal | None
    n_amostra: int | None
    confiabilidade: int | None
    fonte_id: int
    versao: int = 1


@dataclass(frozen=True)
class ContextoLinhagem:
    """Proveniência do lote (uma linha de ``linhagem`` por carga)."""

    fonte_id: int
    indicador_id: int | None
    transformacoes: str
    responsavel: str
    url_extracao: str | None = None
    hash_origem: str | None = None


@dataclass(frozen=True)
class ResumoCarga:
    registros_carregados: int
    suprimidos: int


class GravadorOuro:
    """Escreve a camada ouro aplicando a regra única de supressão (Strategy injetada)."""

    def __init__(
        self, conn: AsyncConnection, estrategia: EstrategiaSupressao | None = None
    ) -> None:
        self._conn = conn
        self._supressao: EstrategiaSupressao = estrategia or SupressaoKAnonimato()

    async def escrever_ouro(
        self,
        celulas: list[CelulaOuro],
        meta_por_indicador: dict[int, MetaIndicadorSupressao],
        linhagem: ContextoLinhagem,
    ) -> ResumoCarga:
        suprimidos = 0
        for c in celulas:
            meta = meta_por_indicador[c.indicador_id]
            resultado = self._supressao.aplicar(  # <-- ÚNICO ponto de chamada da regra
                valor=c.valor, n_amostra=c.n_amostra, meta=meta
            )
            await self._inserir_valor(c, resultado)
            metricas.celulas_gravadas_total.labels(indicador=str(c.indicador_id)).inc()
            if resultado.suprimido:
                suprimidos += 1
                metricas.supressao_total.labels(indicador=str(c.indicador_id)).inc()

        await self._registrar_linhagem(linhagem, registros=len(celulas))
        return ResumoCarga(registros_carregados=len(celulas), suprimidos=suprimidos)

    async def _inserir_valor(self, c: CelulaOuro, r: ResultadoSupressao) -> None:
        stmt = pg_insert(t_valor).values(
            indicador_id=c.indicador_id,
            territorio_id=c.territorio_id,
            periodo=c.periodo,
            atualizacao=c.atualizacao,
            valor=r.valor,
            n_amostra=r.n_amostra,
            suprimido=r.suprimido,
            motivo_supressao=r.motivo_supressao,
            confiabilidade=c.confiabilidade,
            fonte_id=c.fonte_id,
            versao=c.versao,
            carregado_em=datetime.now(UTC),
        )
        stmt = stmt.on_conflict_do_update(
            index_elements=["indicador_id", "territorio_id", "periodo", "versao"],
            set_={
                "valor": stmt.excluded.valor,
                "n_amostra": stmt.excluded.n_amostra,
                "suprimido": stmt.excluded.suprimido,
                "motivo_supressao": stmt.excluded.motivo_supressao,
                "confiabilidade": stmt.excluded.confiabilidade,
                "atualizacao": stmt.excluded.atualizacao,
                "carregado_em": stmt.excluded.carregado_em,
            },
        )
        await self._conn.execute(stmt)

    async def _registrar_linhagem(self, ctx: ContextoLinhagem, registros: int) -> None:
        await self._conn.execute(
            insert(t_linhagem).values(
                fonte_id=ctx.fonte_id,
                indicador_id=ctx.indicador_id,
                executado_em=datetime.now(UTC),
                url_extracao=ctx.url_extracao,
                hash_origem=ctx.hash_origem,
                transformacoes=ctx.transformacoes,
                registros_carregados=registros,
                responsavel=ctx.responsavel,
            )
        )
