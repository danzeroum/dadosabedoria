"""Pipelines medallion (bronze→prata→ouro→``escrever_ouro``) das fontes da Onda 1.

O que worker e Dagster executam. Idempotente (escrever_ouro faz upsert). Toda carga passa pela
MESMA regra única de supressão e registra ``linhagem`` (URL de origem + hash do bruto). O tail de
carga é compartilhado entre as fontes; só a extração/transformação muda por adaptador.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import insert, text
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core import metricas
from app.core.observabilidade import get_logger
from app.core.tables import execucao_funcao as t_execucao_funcao
from app.core.tables import linhagem as t_linhagem
from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.caged import CODIGO_INDICADOR as CODIGO_CAGED
from app.ingestao.adaptadores.caged import AdaptadorCaged
from app.ingestao.adaptadores.datasus import CODIGO_INDICADOR as CODIGO_DATASUS
from app.ingestao.adaptadores.datasus import CONTRATO as CONTRATO_DATASUS
from app.ingestao.adaptadores.datasus import AdaptadorDatasus
from app.ingestao.adaptadores.estban import CODIGO_INDICADOR as CODIGO_ESTBAN
from app.ingestao.adaptadores.estban import AdaptadorEstban
from app.ingestao.adaptadores.inep import CODIGO_INDICADOR as CODIGO_INEP
from app.ingestao.adaptadores.inep import CONTRATO as CONTRATO_INEP
from app.ingestao.adaptadores.inep import AdaptadorInep
from app.ingestao.adaptadores.pncp import CODIGO_INDICADOR as CODIGO_PNCP
from app.ingestao.adaptadores.pncp import CONTRATO as CONTRATO_PNCP
from app.ingestao.adaptadores.pncp import AdaptadorPncp
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


def _dec(v: float | None) -> Decimal | None:
    return Decimal(str(round(float(v), 2))) if v is not None else None


async def executar_siconfi_funcoes(
    janela: Janela,
    conn: AsyncConnection,
    adaptador: AdaptadorSiconfi,
    store: ArmazenamentoBronze,
    *,
    responsavel: str = "ingestao",
) -> ResumoCarga:
    """Esteira SICONFI/DCA **Anexo I-E**: execução por função (Empenhado/Liquidado) → ouro dedicado.

    OndeFoi (TRANSP-06), re-ancorado em **Liquidado/Empenhado** (ADR-0029). É agregado **público sem
    PII** (ADR-0028) → grava na fato dedicada ``execucao_funcao`` (não a ``valor``; **sem**
    supressão k-anon, pois não há PII por baixo). A função é **dimensão** (coluna), não codificada.
    """
    bruto, url = adaptador.baixar_bruto(janela)
    hash_origem = gravar_bronze(store, f"siconfi/funcoes/{janela.ano}.json", bruto)
    df = adaptador.parse(bruto)
    CONTRATO_SICONFI.validar(df)  # borda bronze: mesma forma do DCA (campos confirmados no #0)
    agregado = adaptador.agregar_funcoes(adaptador.transformar_prata_funcoes(df))

    ind = await _carregar_indicador(conn, CODIGO_SICONFI)  # reaproveita o fonte_id do SICONFI
    mapa7 = await _mapa_municipios(conn)

    agora = datetime.now(UTC)
    linhas: list[dict[str, object]] = []
    ignorados = 0
    for row in agregado.iter_rows(named=True):
        territorio_id = mapa7.get(str(row["cod_ibge"]))
        if territorio_id is None:
            ignorados += 1
            continue
        linhas.append(
            {
                "territorio_id": territorio_id,
                "periodo": janela.periodo,
                "funcao_cod": row["funcao_cod"],
                "funcao_nome": row["funcao_nome"],
                "empenhado": _dec(row["empenhado"]),
                "liquidado": _dec(row["liquidado"]),
                "fonte_id": ind.fonte_id,
                "carregado_em": agora,
            }
        )

    if linhas:
        stmt = pg_insert(t_execucao_funcao).values(linhas)
        stmt = stmt.on_conflict_do_update(
            index_elements=["territorio_id", "periodo", "funcao_cod"],
            set_={
                "funcao_nome": stmt.excluded.funcao_nome,
                "empenhado": stmt.excluded.empenhado,
                "liquidado": stmt.excluded.liquidado,
                "fonte_id": stmt.excluded.fonte_id,
                "carregado_em": stmt.excluded.carregado_em,
            },
        )
        await conn.execute(stmt)

    await conn.execute(
        insert(t_linhagem).values(
            fonte_id=ind.fonte_id,
            indicador_id=None,  # fato por função é dedicada (não há indicador na `valor`)
            executado_em=agora,
            url_extracao=url,
            hash_origem=hash_origem,
            transformacoes=f"siconfi {janela.ano}: Anexo I-E -> execucao_funcao (emp/liq)",
            registros_carregados=len(linhas),
            responsavel=responsavel,
        )
    )
    metricas.frescor_dias.labels(fonte="siconfi_funcoes").set((date.today() - janela.periodo).days)
    _log.info(
        "ingestao_carregada",
        fonte="siconfi_funcoes",
        competencia=janela.competencia,
        municipios=len(linhas),
        ignorados=ignorados,
        registros=len(linhas),
    )
    return ResumoCarga(registros_carregados=len(linhas), suprimidos=0)


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


async def executar_pncp(
    janela: Janela,
    conn: AsyncConnection,
    adaptador: AdaptadorPncp,
    store: ArmazenamentoBronze,
    *,
    responsavel: str = "ingestao",
) -> ResumoCarga:
    """Esteira PNCP/contratos de um ano (anual). Requer ``conn`` numa transação aberta.

    Indicador DESCRITIVO (``compras.contratos.valor_total``), fora do IVM → sem ``refrescar_ivm``.
    **Vivo-pronto, NÃO validado:** a forma (lista ``data``, ``valorGlobal``, ``unidadeOrgao.
    codigoIbge``, paginação) **confirmar na 1ª busca real** do PNCP (#0) — ``CONTRATO_PNCP.validar``
    é a borda bronze.
    """
    bruto, url = adaptador.baixar_bruto(janela)
    hash_origem = gravar_bronze(store, f"pncp/{janela.ano}.json", bruto)
    df = adaptador.parse(bruto)
    CONTRATO_PNCP.validar(df)  # borda bronze: falha claro se o layout do PNCP mudar
    agregado = adaptador.agregar(adaptador.transformar_prata(df))

    ind = await _carregar_indicador(conn, CODIGO_PNCP)
    mapa7 = await _mapa_municipios(conn)  # PNCP usa unidadeOrgao.codigoIbge IBGE de 7 dígitos

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
                valor=Decimal(str(round(float(row["valor_contratos"]), 2))),
                n_amostra=None,  # soma de valores públicos → n_minimo=0, sem supressão
                confiabilidade=4,
                fonte_id=ind.fonte_id,
            )
        )
    return await _gravar_celulas(
        conn,
        ind,
        celulas,
        janela,
        fonte_codigo="pncp",
        transformacoes=f"pncp {janela.ano}: bronze->prata->ouro (valor de contratos públicos)",
        url=url,
        hash_origem=hash_origem,
        responsavel=responsavel,
        ignorados=ignorados,
    )


async def executar_datasus(
    janela: Janela,
    conn: AsyncConnection,
    adaptador: AdaptadorDatasus,
    store: ArmazenamentoBronze,
    *,
    responsavel: str = "ingestao",
) -> ResumoCarga:
    """Esteira DATASUS/SIH de uma competência (mensal). Requer ``conn`` numa transação aberta.

    **Origem SENSÍVEL (saúde, ADR-0024).** A contagem de AIH **é** o ``n_amostra`` → a regra única
    de k-anonimato no caminho ouro **suprime antes de gravar** a célula abaixo do piso (n_minimo=5):
    contagem pequena nunca vira número exposto. Subíndice do **IVM**. **Vivo-pronto, NÃO validado:**
    a forma (``MUNIC_RES``/``DIAG_PRINC``, DBC→tabular, nome do arquivo) **confirmar na 1ª busca
    real** do SIH (#0) — ``CONTRATO_DATASUS.validar`` é a borda bronze.
    """
    bruto, url = adaptador.baixar_bruto(janela)
    hash_origem = gravar_bronze(store, f"datasus/{janela.competencia}.csv", bruto)
    df = adaptador.parse(bruto)
    CONTRATO_DATASUS.validar(df)  # borda bronze: falha claro se o layout do SIH-RD mudar
    agregado = adaptador.agregar(adaptador.transformar_prata(df))

    ind = await _carregar_indicador(conn, CODIGO_DATASUS)
    mapa6 = {k[:6]: v for k, v in (await _mapa_municipios(conn)).items()}  # SIH usa IBGE 6 díg.

    celulas = []
    ignorados = 0
    for row in agregado.iter_rows(named=True):
        territorio_id = mapa6.get(str(row["cod_munres"]))
        if territorio_id is None:
            ignorados += 1
            continue
        contagem = int(row["internacoes"])
        celulas.append(
            CelulaOuro(
                indicador_id=ind.id,
                territorio_id=territorio_id,
                periodo=janela.periodo,
                atualizacao="mensal",
                valor=Decimal(contagem),
                n_amostra=contagem,  # a contagem É o n_amostra → k-anon protege contagens pequenas
                confiabilidade=4,
                fonte_id=ind.fonte_id,
            )
        )
    return await _gravar_celulas(
        conn,
        ind,
        celulas,
        janela,
        fonte_codigo="datasus_sih",
        transformacoes=(
            f"datasus {janela.competencia}: bronze->prata->ouro (internações resp. grupo J)"
        ),
        url=url,
        hash_origem=hash_origem,
        responsavel=responsavel,
        ignorados=ignorados,
    )
