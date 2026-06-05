"""IVM — Índice de Vulnerabilidade Municipal (vista de topo que agrega os domínios).

Leitura O(1) da view materializada ``ivm_municipio`` (ADR-0008). ``refrescar_ivm`` recomputa a MV
após a ingestão (REFRESH CONCURRENTLY, em AUTOCOMMIT) e invalida o cache.
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import RowMapping, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_leitura, invalidar
from app.core.config import get_settings
from app.core.db import connect_autocommit
from app.core.erros import NaoEncontradoError
from app.core.observabilidade import get_logger
from app.indicadores.modelos import (
    IVMItem,
    MetaIVM,
    Paginacao,
    RespostaIVM,
    RespostaIVMSerie,
)

_log = get_logger("ivm")

CODIGO_IVM = "transp.ivm.municipal"
COMPONENTES = ["trabalho.emprego.saldo_caged", "credito.operacoes.saldo_total"]
_CACHE_PREFIXO = "v1:ivm"

_SELECT_BASE = """
    SELECT t.codigo_ibge, t.nome, m.periodo, m.ivm, m.semaforo, m.v_emprego, m.v_financas
    FROM ivm_municipio m JOIN territorio t ON t.id = m.territorio_id
"""


async def refrescar_ivm() -> None:
    """Recomputa a MV (após ingestão) e invalida o cache do IVM."""
    async with connect_autocommit(get_settings().database_url) as conn:
        await conn.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY ivm_municipio"))
    await invalidar(_CACHE_PREFIXO)
    _log.info("ivm_refrescado")


def _meta(periodo: date | None) -> MetaIVM:
    return MetaIVM(
        indicador=CODIGO_IVM,
        nome="Índice de Vulnerabilidade Municipal (IVM)",
        metodologia=(
            "Subíndices de emprego (saldo CAGED) e finanças (crédito ESTBAN), normalizados "
            "min-max por período e ponderados 50/50; maior = mais vulnerável."
        ),
        versao_metodologia="v1",
        componentes=COMPONENTES,
        semaforo={"verde": "< 33", "amarelo": "33–66", "vermelho": "> 66"},
        periodo=periodo.strftime("%Y-%m") if periodo else None,
    )


def _item(r: RowMapping) -> IVMItem:
    return IVMItem(
        codigo_ibge=r["codigo_ibge"],
        nome=r["nome"],
        periodo=r["periodo"].strftime("%Y-%m"),
        ivm=float(r["ivm"]),
        semaforo=r["semaforo"],
        v_emprego=float(r["v_emprego"]),
        v_financas=float(r["v_financas"]),
    )


class RepositorioIVM:
    async def periodo_mais_recente(self, session: AsyncSession) -> date | None:
        return (
            await session.execute(text("SELECT max(periodo) FROM ivm_municipio"))
        ).scalar_one_or_none()

    async def por_periodo(
        self, session: AsyncSession, *, periodo: date, pagina: int, por_pagina: int
    ) -> tuple[list[RowMapping], int]:
        stmt = text(
            _SELECT_BASE
            + " WHERE m.periodo = :periodo ORDER BY m.ivm DESC, t.codigo_ibge"
            + " LIMIT :limit OFFSET :offset"
        )
        params = {"periodo": periodo, "limit": por_pagina, "offset": (pagina - 1) * por_pagina}
        rows = (await session.execute(stmt, params)).mappings().all()
        total = (
            await session.execute(
                text("SELECT count(*) FROM ivm_municipio WHERE periodo = :periodo"),
                {"periodo": periodo},
            )
        ).scalar_one()
        return list(rows), int(total)

    async def serie(
        self, session: AsyncSession, *, codigo_ibge: str, de: date | None, ate: date | None
    ) -> list[RowMapping]:
        sql = _SELECT_BASE + " WHERE t.codigo_ibge = :codigo"
        params: dict[str, object] = {"codigo": codigo_ibge}
        if de:
            sql += " AND m.periodo >= :de"
            params["de"] = de
        if ate:
            sql += " AND m.periodo <= :ate"
            params["ate"] = ate
        sql += " ORDER BY m.periodo"
        return list((await session.execute(text(sql), params)).mappings().all())


class IVMFacade:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session
        self._repo = RepositorioIVM()

    @cache_leitura("v1:ivm:periodo")
    async def por_periodo(
        self, *, periodo: date | None = None, pagina: int = 1, por_pagina: int = 1000
    ) -> RespostaIVM:
        alvo = periodo or await self._repo.periodo_mais_recente(self._s)
        if alvo is None:  # pragma: no cover - MV sempre populada após o seed
            return RespostaIVM(
                dados=[],
                meta=_meta(None),
                paginacao=Paginacao(pagina=pagina, por_pagina=por_pagina, total=0),
            )
        rows, total = await self._repo.por_periodo(
            self._s, periodo=alvo, pagina=pagina, por_pagina=por_pagina
        )
        return RespostaIVM(
            dados=[_item(r) for r in rows],
            meta=_meta(alvo),
            paginacao=Paginacao(pagina=pagina, por_pagina=por_pagina, total=total),
        )

    @cache_leitura("v1:ivm:municipio")
    async def serie(
        self, *, codigo_ibge: str, de: date | None = None, ate: date | None = None
    ) -> RespostaIVMSerie:
        rows = await self._repo.serie(self._s, codigo_ibge=codigo_ibge, de=de, ate=ate)
        if not rows:
            raise NaoEncontradoError(f"IVM para território '{codigo_ibge}'")
        return RespostaIVMSerie(dados=[_item(r) for r in rows], meta=_meta(rows[-1]["periodo"]))
