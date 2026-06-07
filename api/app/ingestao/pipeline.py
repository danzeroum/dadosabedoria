"""Pipelines medallion (bronze→prata→ouro→``escrever_ouro``) das fontes da Onda 1.

O que worker e Dagster executam. Idempotente (escrever_ouro faz upsert). Toda carga passa pela
MESMA regra única de supressão e registra ``linhagem`` (URL de origem + hash do bruto). O tail de
carga é compartilhado entre as fontes; só a extração/transformação muda por adaptador.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core import metricas
from app.core.observabilidade import get_logger
from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.caged import CODIGO_INDICADOR as CODIGO_CAGED
from app.ingestao.adaptadores.caged import AdaptadorCaged
from app.ingestao.adaptadores.estban import CODIGO_INDICADOR as CODIGO_ESTBAN
from app.ingestao.adaptadores.estban import AdaptadorEstban
from app.ingestao.adaptadores.inep import CODIGO_INDICADOR as CODIGO_INEP
from app.ingestao.adaptadores.inep import CONTRATO as CONTRATO_INEP
from app.ingestao.adaptadores.inep import AdaptadorInep
from app.ingestao.adaptadores.siconfi import CODIGO_INDICADOR as CODIGO_SICONFI
from app.ingestao.adaptadores.siconfi import CONTRATO as CONTRATO_SICONFI
from app.ingestao.adaptadores.siconfi import AdaptadorSiconfi
from app.ingestao.bronze import ArmazenamentoBronze, gravar_bronze
from app.ingestao.ouro import CelulaOuro, ContextoLinhagem, GravadorOuro, ResumoCarga
from app.ingestao.supressao import MetaIndicadorSupressao

_log = get_logger("ingestao")


@dataclass(frozen=True)
class _IndicadorRef:
    id: int
    fonte_id: int
    n_minimo: int
    origem_sensivel: bool


async def _carregar_indicador(conn: AsyncConnection, codigo: str) -> _IndicadorRef:
    row = (
        (
            await conn.execute(
                text(
                    "SELECT id, fonte_id, n_minimo, origem_sensivel "
                    "FROM indicador WHERE codigo = :c"
                ),
                {"c": codigo},
            )
        )
        .mappings()
        .first()
    )
    if row is None:
        raise RuntimeError(f"indicador '{codigo}' não cadastrado (rode o seed antes da ingestão).")
    return _IndicadorRef(row["id"], row["fonte_id"], row["n_minimo"], row["origem_sensivel"])


async def _mapa_municipios(conn: AsyncConnection) -> dict[str, int]:
    """{codigo_ibge (7 dígitos): territorio_id} para os municípios cadastrados."""
    res = await conn.execute(
        text("SELECT codigo_ibge, id FROM territorio WHERE nivel = 'municipio'")
    )
    return {str(r[0]): int(r[1]) for r in res}


async def _gravar_celulas(
    conn: AsyncConnection,
    ind: _IndicadorRef,
    celulas: list[CelulaOuro],
    janela: Janela,
    *,
    fonte_codigo: str,
    transformacoes: str,
    url: str,
    hash_origem: str,
    responsavel: str,
    ignorados: int,
) -> ResumoCarga:
    grav = GravadorOuro(conn)
    meta = {
        ind.id: MetaIndicadorSupressao(n_minimo=ind.n_minimo, origem_sensivel=ind.origem_sensivel)
    }
    resumo = await grav.escrever_ouro(
        celulas,
        meta,
        ContextoLinhagem(
            fonte_id=ind.fonte_id,
            indicador_id=ind.id,
            transformacoes=transformacoes,
            responsavel=responsavel,
            url_extracao=url,
            hash_origem=hash_origem,
        ),
    )
    metricas.frescor_dias.labels(fonte=fonte_codigo).set((date.today() - janela.periodo).days)
    _log.info(
        "ingestao_carregada",
        fonte=fonte_codigo,
        competencia=janela.competencia,
        municipios=len(celulas),
        ignorados=ignorados,
        registros=resumo.registros_carregados,
    )
    return resumo


async def executar_caged(
    janela: Janela,
    conn: AsyncConnection,
    adaptador: AdaptadorCaged,
    store: ArmazenamentoBronze,
    *,
    responsavel: str = "ingestao",
) -> ResumoCarga:
    """Esteira CAGED de uma competência. Requer ``conn`` numa transação aberta."""
    bruto, url = adaptador.baixar_bruto(janela)
    hash_origem = gravar_bronze(store, f"caged/{janela.competencia}.txt", bruto)
    saldos = adaptador.agregar_saldo(adaptador.transformar_prata(adaptador.parse(bruto)))

    ind = await _carregar_indicador(conn, CODIGO_CAGED)
    # CAGED usa IBGE de 6 dígitos (o de 7 sem o verificador).
    mapa6 = {k[:6]: v for k, v in (await _mapa_municipios(conn)).items()}

    celulas: list[CelulaOuro] = []
    ignorados = 0
    for row in saldos.iter_rows(named=True):
        territorio_id = mapa6.get(str(row["municipio"]))
        if territorio_id is None:
            ignorados += 1
            continue
        celulas.append(
            CelulaOuro(
                indicador_id=ind.id,
                territorio_id=territorio_id,
                periodo=janela.periodo,
                atualizacao="mensal",
                valor=Decimal(int(row["saldo"])),
                n_amostra=None,  # saldo → n_minimo=0, sem supressão
                confiabilidade=5,
                fonte_id=ind.fonte_id,
            )
        )
    return await _gravar_celulas(
        conn,
        ind,
        celulas,
        janela,
        fonte_codigo="novo_caged",
        transformacoes=f"caged {janela.competencia}: bronze->prata->ouro (saldo por município)",
        url=url,
        hash_origem=hash_origem,
        responsavel=responsavel,
        ignorados=ignorados,
    )


async def executar_estban(
    janela: Janela,
    conn: AsyncConnection,
    adaptador: AdaptadorEstban,
    store: ArmazenamentoBronze,
    *,
    responsavel: str = "ingestao",
) -> ResumoCarga:
    """Esteira BCB/ESTBAN de uma competência. Requer ``conn`` numa transação aberta."""
    bruto, url = adaptador.baixar_bruto(janela)
    hash_origem = gravar_bronze(store, f"estban/{janela.competencia}.csv", bruto)
    saldos = adaptador.agregar_credito(adaptador.transformar_prata(adaptador.parse(bruto)))

    ind = await _carregar_indicador(conn, CODIGO_ESTBAN)
    mapa7 = await _mapa_municipios(conn)  # ESTBAN usa CODMUN IBGE de 7 dígitos

    celulas = []
    ignorados = 0
    for row in saldos.iter_rows(named=True):
        territorio_id = mapa7.get(str(row["codmun"]))
        if territorio_id is None:
            ignorados += 1
            continue
        celulas.append(
            CelulaOuro(
                indicador_id=ind.id,
                territorio_id=territorio_id,
                periodo=janela.periodo,
                atualizacao="mensal",
                valor=Decimal(str(round(float(row["saldo"]), 2))),
                n_amostra=None,
                confiabilidade=4,
                fonte_id=ind.fonte_id,
            )
        )
    return await _gravar_celulas(
        conn,
        ind,
        celulas,
        janela,
        fonte_codigo="bcb_estban",
        transformacoes=f"estban {janela.competencia}: bronze->prata->ouro (crédito por município)",
        url=url,
        hash_origem=hash_origem,
        responsavel=responsavel,
        ignorados=ignorados,
    )


async def executar_siconfi(
    janela: Janela,
    conn: AsyncConnection,
    adaptador: AdaptadorSiconfi,
    store: ArmazenamentoBronze,
    *,
    responsavel: str = "ingestao",
) -> ResumoCarga:
    """Esteira SICONFI/DCA de um exercício (anual). Requer ``conn`` numa transação aberta.

    Indicador de PRODUTO (``OndeFoi``/TRANSP-06), não subíndice do IVM → sem ``refrescar_ivm``.
    ``janela.ano`` é o exercício da DCA; ``janela.periodo`` (1º jan) marca o ano.
    """
    bruto, url = adaptador.baixar_bruto(janela)
    hash_origem = gravar_bronze(store, f"siconfi/{janela.ano}.json", bruto)
    df = adaptador.parse(bruto)
    CONTRATO_SICONFI.validar(df)  # borda bronze: falha claro se o layout do SICONFI mudar
    agregado = adaptador.agregar(adaptador.transformar_prata(df))

    ind = await _carregar_indicador(conn, CODIGO_SICONFI)
    mapa7 = await _mapa_municipios(conn)  # SICONFI usa cod_ibge IBGE de 7 dígitos

    celulas = []
    ignorados = 0
    for row in agregado.iter_rows(named=True):
        territorio_id = mapa7.get(str(row["cod_ibge"]))
        if territorio_id is None:
            ignorados += 1
            continue
        celulas.append(
            CelulaOuro(
                indicador_id=ind.id,
                territorio_id=territorio_id,
                periodo=janela.periodo,
                atualizacao="anual",
                valor=Decimal(str(round(float(row["transferencias"]), 2))),
                n_amostra=None,
                confiabilidade=4,
                fonte_id=ind.fonte_id,
            )
        )
    return await _gravar_celulas(
        conn,
        ind,
        celulas,
        janela,
        fonte_codigo="siconfi",
        transformacoes=f"siconfi {janela.ano}: bronze->prata->ouro (transferências correntes DCA)",
        url=url,
        hash_origem=hash_origem,
        responsavel=responsavel,
        ignorados=ignorados,
    )


async def executar_inep(
    janela: Janela,
    conn: AsyncConnection,
    adaptador: AdaptadorInep,
    store: ArmazenamentoBronze,
    *,
    responsavel: str = "ingestao",
) -> ResumoCarga:
    """Esteira INEP/Censo Escolar de um ano (anual). Requer ``conn`` numa transação aberta.

    Indicador DESCRITIVO (``educacao.matriculas.fundamental``), fora do índice de vulnerabilidade →
    sem ``refrescar_ivm``. **Vivo-pronto, NÃO validado:** o contrato é fiel ao layout assumido; os
    nomes de coluna reais (CO_MUNICIPIO/QT_MAT_FUND) e o nome do CSV no ZIP **confirmar na 1ª busca
    real** do INEP (#0) — ``CONTRATO_INEP.validar`` falha claro se o layout divergir.
    """
    bruto, url = adaptador.baixar_bruto(janela)
    hash_origem = gravar_bronze(store, f"inep/{janela.ano}.csv", bruto)
    df = adaptador.parse(bruto)
    CONTRATO_INEP.validar(df)  # borda bronze: falha claro se o layout do Censo Escolar mudar
    agregado = adaptador.agregar(adaptador.transformar_prata(df))

    ind = await _carregar_indicador(conn, CODIGO_INEP)
    mapa7 = await _mapa_municipios(conn)  # INEP usa CO_MUNICIPIO IBGE de 7 dígitos

    celulas = []
    ignorados = 0
    for row in agregado.iter_rows(named=True):
        territorio_id = mapa7.get(str(row["cod_ibge"]))
        if territorio_id is None:
            ignorados += 1
            continue
        celulas.append(
            CelulaOuro(
                indicador_id=ind.id,
                territorio_id=territorio_id,
                periodo=janela.periodo,
                atualizacao="anual",
                valor=Decimal(int(row["matriculas"])),
                n_amostra=None,  # contagem agregada pública → n_minimo=0, sem supressão
                confiabilidade=4,
                fonte_id=ind.fonte_id,
            )
        )
    return await _gravar_celulas(
        conn,
        ind,
        celulas,
        janela,
        fonte_codigo="inep",
        transformacoes=f"inep {janela.ano}: bronze->prata->ouro (matrículas fundamental)",
        url=url,
        hash_origem=hash_origem,
        responsavel=responsavel,
        ignorados=ignorados,
    )
