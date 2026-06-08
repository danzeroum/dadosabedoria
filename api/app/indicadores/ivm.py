"""IVM — Índice de Vulnerabilidade Municipal (vista de topo que agrega os domínios).

Leitura O(1) da view materializada ``ivm_municipio`` (ADR-0008). ``refrescar_ivm`` recomputa a MV
após a ingestão (REFRESH CONCURRENTLY, em AUTOCOMMIT) e invalida o cache.
"""

from __future__ import annotations

import json
from datetime import date

from sqlalchemy import RowMapping, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_leitura, invalidar
from app.core.config import get_settings
from app.core.db import connect_autocommit
from app.core.erros import NaoEncontradoError
from app.core.observabilidade import get_logger
from app.indicadores.modelos import (
    FonteSelo,
    IVMItem,
    MetaIVM,
    Paginacao,
    RespostaIVM,
    RespostaIVMSerie,
)

_log = get_logger("ivm")

CODIGO_IVM = "transp.ivm.municipal"
COMPONENTES = [
    "trabalho.emprego.saldo_caged",
    "credito.operacoes.saldo_total",
    "saude.resp.internacoes_j",
]
_CACHE_PREFIXO = "v1:ivm"

_SELECT_BASE = """
    SELECT t.codigo_ibge, t.nome, m.periodo, m.ivm, m.semaforo,
           m.v_emprego, m.v_financas, m.v_saude, m.v_saude_estado
    FROM ivm_municipio m JOIN territorio t ON t.id = m.territorio_id
"""


async def refrescar_ivm() -> None:
    """Recomputa a MV (após ingestão) e invalida o cache do IVM."""
    async with connect_autocommit(get_settings().database_url) as conn:
        await conn.execute(text("REFRESH MATERIALIZED VIEW CONCURRENTLY ivm_municipio"))
    await invalidar(_CACHE_PREFIXO)
    _log.info("ivm_refrescado")


_MESES = ("jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez")


def _rotulo(periodo: date) -> str:
    return f"{_MESES[periodo.month - 1]}/{periodo.year}"


def _fontes_ivm(rotulo: str) -> list[FonteSelo]:
    """As três fontes do índice composto (emprego, crédito, saúde) — para o selo de confiança."""
    return [
        FonteSelo(
            sigla="CAGED",
            nome="Novo CAGED (Cadastro Geral de Empregados e Desempregados)",
            orgao="MTE / PDET",
            dominio="Trabalho (emprego formal)",
            ate=rotulo,
            atraso="~40 dias após o mês",
        ),
        FonteSelo(
            sigla="ESTBAN",
            nome="Estatística Bancária Mensal por Município",
            orgao="Banco Central do Brasil (BCB)",
            dominio="Crédito / Finanças",
            ate=rotulo,
            atraso="~60 dias após o mês",
        ),
        FonteSelo(
            sigla="SIH/SUS",
            nome="Sistema de Informações Hospitalares (internações respiratórias)",
            orgao="DATASUS / Ministério da Saúde",
            dominio="Saúde",
            ate=rotulo,
            atraso="~90 dias (subíndice opcional)",
        ),
    ]


def _meta(periodo: date | None) -> MetaIVM:
    rotulo = _rotulo(periodo) if periodo else None
    return MetaIVM(
        indicador=CODIGO_IVM,
        nome="Índice de Vulnerabilidade Municipal (IVM)",
        metodologia=(
            "Subíndices de emprego (CAGED), finanças (crédito ESTBAN) e saúde (internações "
            "respiratórias SIH), min-max por período; média dos disponíveis (saúde opcional); "
            "maior = mais vulnerável. z-score = v2 (cobertura nacional, ADR-0025)."
        ),
        versao_metodologia="v1.1",
        componentes=COMPONENTES,
        semaforo={"verde": "< 33", "amarelo": "33–66", "vermelho": "> 66"},
        periodo=periodo.strftime("%Y-%m") if periodo else None,
        # Selo de confiança (reuso do primitivo compartilhado): fontes ricas + frescor típico.
        fontes=_fontes_ivm(rotulo) if rotulo else [],
        periodo_rotulo=rotulo,
        atraso_dias=60,  # lag típico do composto (base emprego+finanças); saúde detalhada por fonte
        licenca="Dados públicos (CAGED/MTE · ESTBAN/BCB · SIH/DATASUS) · Licença aberta · "
        "Atribuição: DadoSabedoria.",
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
        v_saude=float(r["v_saude"]) if r["v_saude"] is not None else None,
        v_saude_estado=r["v_saude_estado"],
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

    async def malha(self, session: AsyncSession, *, uf: str, periodo: date) -> dict:
        """GeoJSON FeatureCollection: geometria do município + IVM (null onde não há dado)."""
        sql = text(
            """
            SELECT json_build_object(
              'type', 'FeatureCollection',
              'features', coalesce(json_agg(f), '[]'::json)
            )
            FROM (
              SELECT json_build_object(
                'type', 'Feature',
                'geometry', ST_AsGeoJSON(ST_SimplifyPreserveTopology(t.geom, 0.005))::json,
                'properties', json_build_object(
                  'codigo_ibge', t.codigo_ibge, 'nome', t.nome,
                  'ivm', m.ivm, 'semaforo', m.semaforo,
                  'v_emprego', m.v_emprego, 'v_financas', m.v_financas,
                  'v_saude', m.v_saude, 'v_saude_estado', m.v_saude_estado)
              ) AS f
              FROM territorio t
              LEFT JOIN ivm_municipio m ON m.territorio_id = t.id AND m.periodo = :periodo
              WHERE t.nivel = 'municipio' AND t.uf = :uf AND t.geom IS NOT NULL
              ORDER BY t.codigo_ibge
            ) sub
            """
        )
        bruto = (await session.execute(sql, {"uf": uf, "periodo": periodo})).scalar_one()
        return json.loads(bruto) if isinstance(bruto, str) else bruto


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

    @cache_leitura("v1:mapa:ivm")
    async def malha(self, *, uf: str, periodo: date | None = None) -> dict:
        alvo = periodo or await self._repo.periodo_mais_recente(self._s)
        if alvo is None:  # pragma: no cover - MV sempre populada após o seed
            return {"type": "FeatureCollection", "features": []}
        return await self._repo.malha(self._s, uf=uf, periodo=alvo)
