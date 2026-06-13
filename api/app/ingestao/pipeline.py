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
from app.ingestao.adaptadores.ana import CODIGO_SECA as CODIGO_SECA_ANA
from app.ingestao.adaptadores.ana import CONTRATO as CONTRATO_ANA
from app.ingestao.adaptadores.ana import AdaptadorAna
from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.caged import CODIGO_INDICADOR as CODIGO_CAGED
from app.ingestao.adaptadores.caged import CODIGO_SALARIO as CODIGO_SALARIO_CAGED
from app.ingestao.adaptadores.caged import AdaptadorCaged
from app.ingestao.adaptadores.datasus import CODIGO_INDICADOR as CODIGO_DATASUS
from app.ingestao.adaptadores.datasus import CONTRATO as CONTRATO_DATASUS
from app.ingestao.adaptadores.datasus import AdaptadorDatasus
from app.ingestao.adaptadores.energia import CODIGO_DEC as CODIGO_DEC_ANEEL
from app.ingestao.adaptadores.energia import CODIGO_FEC as CODIGO_FEC_ANEEL
from app.ingestao.adaptadores.energia import CONTRATO as CONTRATO_ANEEL
from app.ingestao.adaptadores.energia import AdaptadorAneel
from app.ingestao.adaptadores.estban import CODIGO_INDICADOR as CODIGO_ESTBAN
from app.ingestao.adaptadores.estban import AdaptadorEstban
from app.ingestao.adaptadores.inep import CODIGO_INDICADOR as CODIGO_INEP
from app.ingestao.adaptadores.inep import CONTRATO as CONTRATO_INEP
from app.ingestao.adaptadores.inep import AdaptadorInep
from app.ingestao.adaptadores.pam import CODIGO_INDICADOR as CODIGO_PAM
from app.ingestao.adaptadores.pam import CONTRATO as CONTRATO_PAM
from app.ingestao.adaptadores.pam import AdaptadorPam
from app.ingestao.adaptadores.pncp import CODIGO_INDICADOR as CODIGO_PNCP
from app.ingestao.adaptadores.pncp import CONTRATO as CONTRATO_PNCP
from app.ingestao.adaptadores.pncp import AdaptadorPncp
from app.ingestao.adaptadores.saneamento import CODIGO_AGUA as CODIGO_AGUA_SNIS
from app.ingestao.adaptadores.saneamento import CODIGO_ESGOTO as CODIGO_ESGOTO_SNIS
from app.ingestao.adaptadores.saneamento import CONTRATO as CONTRATO_SNIS
from app.ingestao.adaptadores.saneamento import AdaptadorSnis
from app.ingestao.adaptadores.siconfi import CODIGO_INDICADOR as CODIGO_SICONFI
from app.ingestao.adaptadores.siconfi import CONTRATO as CONTRATO_SICONFI
from app.ingestao.adaptadores.siconfi import AdaptadorSiconfi
from app.ingestao.adaptadores.sisvan import CODIGO_INDICADOR as CODIGO_SISVAN
from app.ingestao.adaptadores.sisvan import CODIGO_INDICADOR_GESTANTE as CODIGO_SISVAN_GESTANTE
from app.ingestao.adaptadores.sisvan import CONTRATO as CONTRATO_SISVAN
from app.ingestao.adaptadores.sisvan import CONTRATO_GESTANTE as CONTRATO_SISVAN_GESTANTE
from app.ingestao.adaptadores.sisvan import AdaptadorSisvan, AdaptadorSisvanGestante
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
    """Esteira CAGED de uma competência. Requer ``conn`` numa transação aberta.

    Grava dois indicadores: saldo de emprego (CODIGO_CAGED) e salário médio de admissão
    (CODIGO_SALARIO_CAGED) — ambos derivados do mesmo bruto CAGEDMOV.
    """
    bruto, url = adaptador.baixar_bruto(janela)
    hash_origem = gravar_bronze(store, f"caged/{janela.competencia}.txt", bruto)
    # Agregação nacional em uma única passagem lazy (streaming) — ver ADR-0036
    saldos, salarios = adaptador.agregar_nacional(bruto)
    # Indexar salários por município para lookup O(1)
    sal_por_mun = {str(r["municipio"]): r["salario_medio"] for r in salarios.iter_rows(named=True)}

    ind_saldo = await _carregar_indicador(conn, CODIGO_CAGED)
    ind_sal = await _carregar_indicador(conn, CODIGO_SALARIO_CAGED)
    # CAGED usa IBGE de 6 dígitos (o de 7 sem o verificador).
    mapa6 = {k[:6]: v for k, v in (await _mapa_municipios(conn)).items()}

    celulas_saldo: list[CelulaOuro] = []
    celulas_sal: list[CelulaOuro] = []
    ignorados = 0
    for row in saldos.iter_rows(named=True):
        mun = str(row["municipio"])
        territorio_id = mapa6.get(mun)
        if territorio_id is None:
            ignorados += 1
            continue
        celulas_saldo.append(
            CelulaOuro(
                indicador_id=ind_saldo.id,
                territorio_id=territorio_id,
                periodo=janela.periodo,
                atualizacao="mensal",
                valor=Decimal(int(row["saldo"])),
                n_amostra=None,  # saldo → n_minimo=0, sem supressão
                confiabilidade=5,
                fonte_id=ind_saldo.fonte_id,
            )
        )
        sal_medio = sal_por_mun.get(mun)
        if sal_medio is not None:
            celulas_sal.append(
                CelulaOuro(
                    indicador_id=ind_sal.id,
                    territorio_id=territorio_id,
                    periodo=janela.periodo,
                    atualizacao="mensal",
                    valor=Decimal(str(round(float(sal_medio), 2))),
                    n_amostra=None,
                    confiabilidade=5,
                    fonte_id=ind_sal.fonte_id,
                )
            )

    resumo_saldo = await _gravar_celulas(
        conn,
        ind_saldo,
        celulas_saldo,
        janela,
        fonte_codigo="novo_caged",
        transformacoes=f"caged {janela.competencia}: bronze->prata->ouro (saldo por município)",
        url=url,
        hash_origem=hash_origem,
        responsavel=responsavel,
        ignorados=ignorados,
    )
    if celulas_sal:
        await _gravar_celulas(
            conn,
            ind_sal,
            celulas_sal,
            janela,
            fonte_codigo="novo_caged",
            transformacoes=(
                f"caged {janela.competencia}: bronze->prata->ouro (salário médio admissão)"
            ),
            url=url,
            hash_origem=hash_origem,
            responsavel=responsavel,
            ignorados=ignorados,
        )
    return resumo_saldo


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

    # asyncpg tem limite de 32.767 parâmetros por query; com 8 colunas → máx ~4000 linhas por lote.
    _BATCH = 3000
    for i in range(0, len(linhas), _BATCH):
        lote = linhas[i : i + _BATCH]
        stmt = pg_insert(t_execucao_funcao).values(lote)
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
    _log.info("datasus_parse: %d linhas, cols=%s", df.height, df.columns)
    CONTRATO_DATASUS.validar(df)  # borda bronze: falha claro se o layout do SIH-RD mudar

    prata = adaptador.transformar_prata(df)
    _log.info(
        "datasus_prata: %d linhas após filtro J%%, amostra=%s",
        prata.height,
        prata.head(3).to_dicts() if prata.height > 0 else "(vazio)",
    )

    agregado = adaptador.agregar(prata)
    _log.info("datasus_agregar: %d pares município×mês", agregado.height)

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
                periodo=row["mes_internacao"],  # data de internação (DT_INTER), não competência
                atualizacao="mensal",
                valor=Decimal(contagem),
                n_amostra=contagem,  # a contagem É o n_amostra → k-anon protege contagens pequenas
                confiabilidade=4,
                fonte_id=ind.fonte_id,
            )
        )

    _log.info(
        "datasus_mapa6: %d células ok, %d ignorados (sem mapa6 de %d pares)",
        len(celulas),
        ignorados,
        agregado.height,
    )

    # Guard anti-falha-silenciosa: 0 células com dado agregado indica bug no pipeline.
    # A linhagem só é gravada se houver dado real — não registrar execuções fantasma.
    if not celulas and agregado.height > 0:
        raise RuntimeError(
            f"datasus_sih {janela.competencia}: {agregado.height} pares município×mês agregados "
            f"mas 0 células geradas ({ignorados} sem mapa6) — provável divergência de código IBGE "
            f"ou bug no pipeline; abortando sem gravar linhagem."
        )
    if not celulas:
        raise RuntimeError(
            f"datasus_sih {janela.competencia}: 0 células geradas (parse={df.height} linhas, "
            f"prata={prata.height} linhas J%, agregado={agregado.height} pares) — "
            f"provável bug no pipeline; abortando sem gravar linhagem."
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


async def executar_aneel(
    janela: Janela,
    conn: AsyncConnection,
    adaptador: AdaptadorAneel,
    store: ArmazenamentoBronze,
    *,
    responsavel: str = "ingestao",
) -> ResumoCarga:
    """Esteira ANEEL DEC/FEC (anual) — qualidade do fornecimento elétrico por município.

    Grava dois indicadores: DEC (horas/consumidor/ano) e FEC (interrupções/consumidor/ano).
    Vivo-pronto: forma a confirmar na 1ª busca real (``dadosabertos.aneel.gov.br``).
    """
    bruto, url = adaptador.baixar_bruto(janela)
    hash_origem = gravar_bronze(store, f"aneel/{janela.ano}.csv", bruto)
    df = adaptador.parse(bruto)
    CONTRATO_ANEEL.validar(df)
    agregado = adaptador.agregar(adaptador.transformar_prata(df))

    ind_dec = await _carregar_indicador(conn, CODIGO_DEC_ANEEL)
    ind_fec = await _carregar_indicador(conn, CODIGO_FEC_ANEEL)
    mapa7 = await _mapa_municipios(conn)

    celulas_dec: list[CelulaOuro] = []
    celulas_fec: list[CelulaOuro] = []
    ignorados = 0
    for row in agregado.iter_rows(named=True):
        territorio_id = mapa7.get(str(row["cod_ibge"]))
        if territorio_id is None:
            ignorados += 1
            continue
        celulas_dec.append(
            CelulaOuro(
                indicador_id=ind_dec.id,
                territorio_id=territorio_id,
                periodo=janela.periodo,
                atualizacao="anual",
                valor=Decimal(str(round(float(row["dec"]), 4))),
                n_amostra=None,
                confiabilidade=4,
                fonte_id=ind_dec.fonte_id,
            )
        )
        if row["fec"] is not None:
            celulas_fec.append(
                CelulaOuro(
                    indicador_id=ind_fec.id,
                    territorio_id=territorio_id,
                    periodo=janela.periodo,
                    atualizacao="anual",
                    valor=Decimal(str(round(float(row["fec"]), 4))),
                    n_amostra=None,
                    confiabilidade=4,
                    fonte_id=ind_fec.fonte_id,
                )
            )

    resumo = await _gravar_celulas(
        conn,
        ind_dec,
        celulas_dec,
        janela,
        fonte_codigo="aneel",
        transformacoes=f"aneel {janela.ano}: bronze->prata->ouro (DEC)",
        url=url,
        hash_origem=hash_origem,
        responsavel=responsavel,
        ignorados=ignorados,
    )
    if celulas_fec:
        await _gravar_celulas(
            conn,
            ind_fec,
            celulas_fec,
            janela,
            fonte_codigo="aneel",
            transformacoes=f"aneel {janela.ano}: bronze->prata->ouro (FEC)",
            url=url,
            hash_origem=hash_origem,
            responsavel=responsavel,
            ignorados=0,
        )
    return resumo


async def executar_snis(
    janela: Janela,
    conn: AsyncConnection,
    adaptador: AdaptadorSnis,
    store: ArmazenamentoBronze,
    *,
    responsavel: str = "ingestao",
) -> ResumoCarga:
    """Esteira SNIS (anual) — água (IN023_AE) e esgoto (IN015_AE) por município.

    Grava dois indicadores: atendimento_pct e coleta_pct.
    Vivo-pronto: forma a confirmar na 1ª busca real (#0, host app4.mdr.gov.br).
    """
    bruto, url = adaptador.baixar_bruto(janela)
    hash_origem = gravar_bronze(store, f"snis/{janela.ano}.csv", bruto)
    df = adaptador.parse(bruto)
    CONTRATO_SNIS.validar(df)
    agregado = adaptador.agregar(adaptador.transformar_prata(df))

    ind_agua = await _carregar_indicador(conn, CODIGO_AGUA_SNIS)
    ind_esgoto = await _carregar_indicador(conn, CODIGO_ESGOTO_SNIS)
    mapa7 = await _mapa_municipios(conn)

    celulas_agua: list[CelulaOuro] = []
    celulas_esgoto: list[CelulaOuro] = []
    ignorados = 0
    for row in agregado.iter_rows(named=True):
        territorio_id = mapa7.get(str(row["cod_ibge"]))
        if territorio_id is None:
            ignorados += 1
            continue
        celulas_agua.append(
            CelulaOuro(
                indicador_id=ind_agua.id,
                territorio_id=territorio_id,
                periodo=janela.periodo,
                atualizacao="anual",
                valor=Decimal(str(round(float(row["agua_pct"]), 4))),
                n_amostra=None,
                confiabilidade=4,
                fonte_id=ind_agua.fonte_id,
            )
        )
        if row["esgoto_pct"] is not None:
            celulas_esgoto.append(
                CelulaOuro(
                    indicador_id=ind_esgoto.id,
                    territorio_id=territorio_id,
                    periodo=janela.periodo,
                    atualizacao="anual",
                    valor=Decimal(str(round(float(row["esgoto_pct"]), 4))),
                    n_amostra=None,
                    confiabilidade=4,
                    fonte_id=ind_esgoto.fonte_id,
                )
            )

    resumo = await _gravar_celulas(
        conn,
        ind_agua,
        celulas_agua,
        janela,
        fonte_codigo="snis",
        transformacoes=f"snis {janela.ano}: bronze->prata->ouro (atendimento água)",
        url=url,
        hash_origem=hash_origem,
        responsavel=responsavel,
        ignorados=ignorados,
    )
    if celulas_esgoto:
        await _gravar_celulas(
            conn,
            ind_esgoto,
            celulas_esgoto,
            janela,
            fonte_codigo="snis",
            transformacoes=f"snis {janela.ano}: bronze->prata->ouro (coleta esgoto)",
            url=url,
            hash_origem=hash_origem,
            responsavel=responsavel,
            ignorados=0,
        )
    return resumo


async def executar_ana(
    janela: Janela,
    conn: AsyncConnection,
    adaptador: AdaptadorAna,
    store: ArmazenamentoBronze,
    *,
    responsavel: str = "ingestao",
) -> ResumoCarga:
    """Esteira ANA Monitor de Secas (anual) — risco hídrico de seca por município.

    Grava um indicador: seca_indice (0–5, pior mês do ano).
    Vivo-pronto: forma a confirmar na 1ª busca real (#0, host monitordesecas.ana.gov.br).
    """
    bruto, url = adaptador.baixar_bruto(janela)
    hash_origem = gravar_bronze(store, f"ana/{janela.ano}.csv", bruto)
    df = adaptador.parse(bruto)
    CONTRATO_ANA.validar(df)
    agregado = adaptador.agregar(adaptador.transformar_prata(df))

    ind_seca = await _carregar_indicador(conn, CODIGO_SECA_ANA)
    mapa7 = await _mapa_municipios(conn)

    celulas: list[CelulaOuro] = []
    ignorados = 0
    for row in agregado.iter_rows(named=True):
        territorio_id = mapa7.get(str(row["cod_ibge"]))
        if territorio_id is None:
            ignorados += 1
            continue
        celulas.append(
            CelulaOuro(
                indicador_id=ind_seca.id,
                territorio_id=territorio_id,
                periodo=janela.periodo,
                atualizacao="anual",
                valor=Decimal(str(round(float(row["seca_indice"]), 4))),
                n_amostra=None,
                confiabilidade=3,
                fonte_id=ind_seca.fonte_id,
            )
        )

    return await _gravar_celulas(
        conn,
        ind_seca,
        celulas,
        janela,
        fonte_codigo="ana",
        transformacoes=f"ana {janela.ano}: bronze->prata->ouro (seca_indice)",
        url=url,
        hash_origem=hash_origem,
        responsavel=responsavel,
        ignorados=ignorados,
    )


async def executar_pam(
    janela: Janela,
    conn: AsyncConnection,
    adaptador: AdaptadorPam,
    store: ArmazenamentoBronze,
    *,
    responsavel: str = "ingestao",
) -> ResumoCarga:
    """Esteira IBGE PAM (anual) — valor da produção agrícola municipal por habitante.

    Grava um indicador: alimentacao.producao.valor_total (BRL, soma lavouras temp. + perm.).
    Vivo-pronto: forma a confirmar na 1ª busca real (#0, host servicodados.ibge.gov.br).
    """
    bruto, url = adaptador.baixar_bruto(janela)
    hash_origem = gravar_bronze(store, f"ibge_pam/{janela.ano}.json", bruto)
    df = adaptador.parse(bruto)
    CONTRATO_PAM.validar(df)
    agregado = adaptador.agregar(adaptador.transformar_prata(df))

    ind_pam = await _carregar_indicador(conn, CODIGO_PAM)
    mapa7 = await _mapa_municipios(conn)

    celulas: list[CelulaOuro] = []
    ignorados = 0
    for row in agregado.iter_rows(named=True):
        territorio_id = mapa7.get(str(row["cod_ibge"]))
        if territorio_id is None:
            ignorados += 1
            continue
        celulas.append(
            CelulaOuro(
                indicador_id=ind_pam.id,
                territorio_id=territorio_id,
                periodo=janela.periodo,
                atualizacao="anual",
                valor=Decimal(str(round(float(row["valor_brl"]), 0))),
                n_amostra=None,
                confiabilidade=3,
                fonte_id=ind_pam.fonte_id,
            )
        )

    return await _gravar_celulas(
        conn,
        ind_pam,
        celulas,
        janela,
        fonte_codigo="ibge_pam",
        transformacoes=f"ibge_pam {janela.ano}: bronze->prata->ouro (valor_brl)",
        url=url,
        hash_origem=hash_origem,
        responsavel=responsavel,
        ignorados=ignorados,
    )


async def executar_sisvan(
    janela: Janela,
    conn: AsyncConnection,
    adaptador: AdaptadorSisvan,
    store: ArmazenamentoBronze,
    *,
    responsavel: str = "ingestao",
) -> ResumoCarga:
    """Esteira SISVAN (anual) — % de crianças < 5 anos com baixo peso por município.

    Grava um indicador: alimentacao.nutricao.baixo_peso_pct (%).
    Vivo-pronto: forma a confirmar na 1ª busca real (#0, host s3.sa-east-1.amazonaws.com).
    """
    bruto, url = adaptador.baixar_bruto(janela)
    hash_origem = gravar_bronze(store, f"sisvan/{janela.ano}.csv", bruto)
    df = adaptador.parse(bruto)
    CONTRATO_SISVAN.validar(df)
    agregado = adaptador.agregar(adaptador.transformar_prata(df))

    ind_sisvan = await _carregar_indicador(conn, CODIGO_SISVAN)
    mapa7 = await _mapa_municipios(conn)

    celulas: list[CelulaOuro] = []
    ignorados = 0
    for row in agregado.iter_rows(named=True):
        territorio_id = mapa7.get(str(row["cod_ibge"]))
        if territorio_id is None:
            ignorados += 1
            continue
        celulas.append(
            CelulaOuro(
                indicador_id=ind_sisvan.id,
                territorio_id=territorio_id,
                periodo=janela.periodo,
                atualizacao="anual",
                valor=Decimal(str(round(float(row["baixo_peso_pct"]), 4))),
                n_amostra=int(row["n_total"]),
                confiabilidade=3,
                fonte_id=ind_sisvan.fonte_id,
            )
        )

    return await _gravar_celulas(
        conn,
        ind_sisvan,
        celulas,
        janela,
        fonte_codigo="sisvan",
        transformacoes=f"sisvan {janela.ano}: bronze->prata->ouro (baixo_peso_pct)",
        url=url,
        hash_origem=hash_origem,
        responsavel=responsavel,
        ignorados=ignorados,
    )


async def executar_sisvan_gestante(
    janela: Janela,
    conn: AsyncConnection,
    adaptador: AdaptadorSisvanGestante,
    store: ArmazenamentoBronze,
    *,
    responsavel: str = "ingestao",
) -> ResumoCarga:
    """Esteira SISVAN gestante (anual) — % de gestantes com baixo peso por município.

    Grava um indicador: saude.materno.gestante_baixo_peso_pct (%).
    Origem SENSÍVEL (dados de saúde materna). k-anonimato: n_minimo=5.
    Vivo-pronto: forma a confirmar na 1ª busca real (#0, host s3.sa-east-1.amazonaws.com).
    """
    bruto, url = adaptador.baixar_bruto(janela)
    hash_origem = gravar_bronze(store, f"sisvan_gestante/{janela.ano}.csv", bruto)
    df = adaptador.parse(bruto)
    CONTRATO_SISVAN_GESTANTE.validar(df)
    agregado = adaptador.agregar(adaptador.transformar_prata(df))

    ind_gestante = await _carregar_indicador(conn, CODIGO_SISVAN_GESTANTE)
    mapa7 = await _mapa_municipios(conn)

    celulas: list[CelulaOuro] = []
    ignorados = 0
    for row in agregado.iter_rows(named=True):
        territorio_id = mapa7.get(str(row["cod_ibge"]))
        if territorio_id is None:
            ignorados += 1
            continue
        celulas.append(
            CelulaOuro(
                indicador_id=ind_gestante.id,
                territorio_id=territorio_id,
                periodo=date(janela.ano, 1, 1),
                atualizacao="anual",
                valor=Decimal(str(round(float(row["gestante_baixo_peso_pct"]), 4))),
                n_amostra=int(row["n_total"]),
                confiabilidade=3,
                fonte_id=ind_gestante.fonte_id,
            )
        )

    return await _gravar_celulas(
        conn,
        ind_gestante,
        celulas,
        janela,
        fonte_codigo="sisvan_gestante",
        transformacoes=(
            f"sisvan_gestante {janela.ano}: bronze->prata->ouro (gestante_baixo_peso_pct)"
        ),
        url=url,
        hash_origem=hash_origem,
        responsavel=responsavel,
        ignorados=ignorados,
    )
