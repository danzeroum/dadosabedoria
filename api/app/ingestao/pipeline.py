"""Pipeline medallion do CAGED: bronze → prata → ouro → ``escrever_ouro``.

É o que o worker e o Dagster (Degrau 1) executam. Idempotente (escrever_ouro faz upsert). A carga
em ``valor`` passa pela MESMA regra única de supressão da fundação, e registra ``linhagem`` com a
URL de origem e o hash do bruto (proveniência, invariante 5).
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
from app.ingestao.adaptadores.caged import CODIGO_INDICADOR, AdaptadorCaged
from app.ingestao.bronze import ArmazenamentoBronze, gravar_bronze
from app.ingestao.ouro import CelulaOuro, ContextoLinhagem, GravadorOuro, ResumoCarga
from app.ingestao.supressao import MetaIndicadorSupressao

_log = get_logger("ingestao.caged")


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


async def _mapa_territorios_municipio(conn: AsyncConnection) -> dict[str, int]:
    # CAGED usa o código IBGE de 6 dígitos (o de 7 sem o dígito verificador).
    res = await conn.execute(
        text("SELECT codigo_ibge, id FROM territorio WHERE nivel = 'municipio'")
    )
    return {str(r[0])[:6]: int(r[1]) for r in res}


async def executar_caged(
    janela: Janela,
    conn: AsyncConnection,
    adaptador: AdaptadorCaged,
    store: ArmazenamentoBronze,
    *,
    responsavel: str = "ingestao",
) -> ResumoCarga:
    """Executa a esteira para uma competência (mês). Requer ``conn`` numa transação aberta."""
    bruto, url = adaptador.baixar_bruto(janela)
    chave = f"caged/{janela.competencia}.txt"
    hash_origem = gravar_bronze(store, chave, bruto)  # BRONZE

    df = adaptador.parse(bruto)
    df_prata = adaptador.transformar_prata(df)  # PRATA
    saldos = adaptador.agregar_saldo(df_prata)  # OURO (agregação)

    ind = await _carregar_indicador(conn, CODIGO_INDICADOR)
    mapa = await _mapa_territorios_municipio(conn)

    celulas: list[CelulaOuro] = []
    ignorados = 0
    for row in saldos.iter_rows(named=True):
        territorio_id = mapa.get(str(row["municipio"]))
        if territorio_id is None:
            ignorados += 1  # município fora do cadastro de territórios
            continue
        celulas.append(
            CelulaOuro(
                indicador_id=ind.id,
                territorio_id=territorio_id,
                periodo=janela.periodo,
                atualizacao="mensal",
                valor=Decimal(int(row["saldo"])),
                n_amostra=None,  # saldo (não é contagem de pessoas) → n_minimo=0, sem supressão
                confiabilidade=5,
                fonte_id=ind.fonte_id,
            )
        )

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
            transformacoes=f"caged {janela.competencia}: bronze->prata->ouro (saldo por município)",
            responsavel=responsavel,
            url_extracao=url,
            hash_origem=hash_origem,
        ),
    )
    metricas.frescor_dias.labels(fonte="novo_caged").set((date.today() - janela.periodo).days)
    _log.info(
        "caged_carregado",
        competencia=janela.competencia,
        municipios=len(celulas),
        ignorados=ignorados,
        registros=resumo.registros_carregados,
    )
    return resumo
