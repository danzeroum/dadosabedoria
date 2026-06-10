"""Repository do OndeFoi — lê ``execucao_funcao`` + ``territorio`` (SQLAlchemy Core).

Retorna os modelos Pydantic prontos para a rota. Nenhum dado pessoal — ``execucao_funcao`` é
agregado público (ADR-0028/0029). Cache em Redis via ``cache_leitura`` (chave ``v1:ondefoi``).
"""

from __future__ import annotations

from datetime import date

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.cache import cache_leitura
from app.core.erros import NaoEncontradoError
from app.core.tables import execucao_funcao as t_ef
from app.core.tables import territorio as t_terr
from app.produtos.modelos import (
    FonteOut,
    FuncaoOut,
    MetaOndeFoi,
    OndeFoiLista,
    OndeFoiOut,
    OndeFoiResumo,
)
from app.produtos.onde_foi import FuncaoBruta, banda, calcular

# Meta estática (fonte/metodologia não mudam entre exercícios).
_FONTE_SICONFI = FonteOut(
    sigla="SICONFI",
    nome="Sistema de Informações Contábeis e Fiscais — DCA (Anexo I-E)",
    orgao="Tesouro Nacional / STN",
    dominio="Finanças públicas municipais",
    ate="anual (por exercício)",
    atraso="~75 dias após o fechamento do exercício",
)

_METODOLOGIA = (
    "Execução orçamentária (empenho/liquidação) por função, no exercício — NÃO serviço entregue."
)


def _meta(periodo: date | None) -> MetaOndeFoi:
    return MetaOndeFoi(
        metodologia=_METODOLOGIA,
        versao_metodologia="v1",
        periodo=periodo.isoformat() if periodo else "",
        periodo_rotulo=f"exercício {periodo.year}" if periodo else "sem dados disponíveis",
        atraso_dias=75,
        licenca="Dados públicos (SICONFI) · Licença aberta · Atribuição: DadoSabedoria.",
        fontes=[_FONTE_SICONFI],
    )


def _to_int(v: object) -> int:
    if v is None:
        return 0
    return int(round(float(v)))  # type: ignore[arg-type]


class RepositorioOndeFoi:
    @cache_leitura("v1:ondefoi:detalhe")
    async def obter(self, session: AsyncSession, *, codigo_ibge: str) -> OndeFoiOut:
        """Execução por função do município — 404 se não há dado na ``execucao_funcao``."""
        # 1. territorio
        terr = (
            (
                await session.execute(
                    select(t_terr).where(
                        t_terr.c.codigo_ibge == codigo_ibge,
                        t_terr.c.nivel == "municipio",
                    )
                )
            )
            .mappings()
            .first()
        )
        if terr is None:
            raise NaoEncontradoError(f"território '{codigo_ibge}'")

        # 2. período mais recente disponível
        periodo = (
            await session.execute(
                select(func.max(t_ef.c.periodo)).where(t_ef.c.territorio_id == terr["id"])
            )
        ).scalar_one_or_none()
        if periodo is None:
            raise NaoEncontradoError(f"OndeFoi para município '{codigo_ibge}'")

        # 3. funções do período mais recente
        linhas = (
            (
                await session.execute(
                    select(
                        t_ef.c.funcao_cod,
                        t_ef.c.funcao_nome,
                        t_ef.c.empenhado,
                        t_ef.c.liquidado,
                    )
                    .where(
                        t_ef.c.territorio_id == terr["id"],
                        t_ef.c.periodo == periodo,
                    )
                    .order_by(t_ef.c.funcao_cod)
                )
            )
            .mappings()
            .all()
        )

        funcoes_brutas: list[FuncaoBruta] = []
        empenhado_total = 0
        for row in linhas:
            if row["empenhado"] is None:
                continue
            emp = _to_int(row["empenhado"])
            empenhado_total += emp
            liq: int | str
            if row["liquidado"] is not None:
                liq = _to_int(row["liquidado"])
            else:
                liq = "sem_cobertura"
            funcoes_brutas.append(FuncaoBruta(row["funcao_nome"], emp, liq))  # type: ignore[arg-type]

        if not funcoes_brutas:
            raise NaoEncontradoError(f"OndeFoi para município '{codigo_ibge}'")

        r = calcular(codigo_ibge, terr["nome"], terr["uf"] or "", empenhado_total, funcoes_brutas)
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
            meta=_meta(periodo),
        )

    @cache_leitura("v1:ondefoi:lista")
    async def listar(self, session: AsyncSession) -> OndeFoiLista:
        """Todos os municípios com dado em ``execucao_funcao``, ordenados por nome."""
        # Subquery: período mais recente por território
        sub = (
            select(t_ef.c.territorio_id, func.max(t_ef.c.periodo).label("max_periodo"))
            .group_by(t_ef.c.territorio_id)
            .subquery()
        )
        # Agregado por município: base do pct (só funções com liquidado)
        stmt = (
            select(
                t_terr.c.codigo_ibge,
                t_terr.c.nome,
                t_terr.c.uf,
                sub.c.max_periodo.label("periodo"),
                func.sum(case((t_ef.c.liquidado.is_not(None), t_ef.c.empenhado), else_=0)).label(
                    "empenhado_base"
                ),
                func.sum(t_ef.c.liquidado).label("liquidado"),
            )
            .select_from(
                t_ef.join(
                    sub,
                    (t_ef.c.territorio_id == sub.c.territorio_id)
                    & (t_ef.c.periodo == sub.c.max_periodo),
                ).join(t_terr, t_terr.c.id == t_ef.c.territorio_id)
            )
            .group_by(t_terr.c.codigo_ibge, t_terr.c.nome, t_terr.c.uf, sub.c.max_periodo)
            .order_by(t_terr.c.nome)
        )
        linhas = (await session.execute(stmt)).mappings().all()

        max_periodo = max((r["periodo"] for r in linhas), default=None)
        resumos: list[OndeFoiResumo] = []
        for row in linhas:
            emp_base = _to_int(row["empenhado_base"])
            liq = _to_int(row["liquidado"])
            pct_val = round(liq / emp_base * 100) if emp_base else 0
            resumos.append(
                OndeFoiResumo(
                    codigo_ibge=row["codigo_ibge"],
                    nome=row["nome"],
                    uf=row["uf"] or "",
                    pct=pct_val,
                    banda=banda(pct_val),
                )
            )

        return OndeFoiLista(dados=resumos, meta=_meta(max_periodo))
