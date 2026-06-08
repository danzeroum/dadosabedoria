"""IVM: view materializada + endpoints (mapa semafórico + drill-down), contra Postgres real.

Usa dois municípios isolados (BH, Rio) num período próprio para exercitar a normalização min-max,
sem tocar a série de SP que outros testes verificam.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.config import get_settings
from app.core.db import connect
from app.indicadores.ivm import refrescar_ivm
from app.ingestao.ouro import CelulaOuro, ContextoLinhagem, GravadorOuro
from app.ingestao.supressao import MetaIndicadorSupressao

pytestmark = pytest.mark.integration

_PERIODO = date(2026, 8, 1)
_BH = "3106200"  # Belo Horizonte (menos vulnerável no fixture)
_RIO = "3304557"  # Rio de Janeiro (mais vulnerável no fixture)


async def _id_indicador(conn: AsyncConnection, codigo: str) -> tuple[int, int]:
    row = (
        (
            await conn.execute(
                text("SELECT id, fonte_id FROM indicador WHERE codigo = :c"), {"c": codigo}
            )
        )
        .mappings()
        .first()
    )
    assert row is not None
    return int(row["id"]), int(row["fonte_id"])


async def _id_territorio(conn: AsyncConnection, codigo_ibge: str) -> int:
    return int(
        (
            await conn.execute(
                text("SELECT id FROM territorio WHERE codigo_ibge = :c"), {"c": codigo_ibge}
            )
        ).scalar_one()
    )


async def _semear_ivm(conn: AsyncConnection) -> None:
    await conn.execute(
        text(
            "INSERT INTO territorio (codigo_ibge, nome, nivel, uf, populacao) VALUES "
            "('3106200','Belo Horizonte','municipio','MG',2315560),"
            "('3304557','Rio de Janeiro','municipio','RJ',6747815),"
            "('3170206','Uberlândia','municipio','MG',699097),"
            "('3118601','Contagem','municipio','MG',668949) "
            "ON CONFLICT (codigo_ibge) DO NOTHING"
        )
    )
    caged_id, caged_fonte = await _id_indicador(conn, "trabalho.emprego.saldo_caged")
    cred_id, cred_fonte = await _id_indicador(conn, "credito.operacoes.saldo_total")
    sau_id, sau_fonte = await _id_indicador(conn, "saude.resp.internacoes_j")
    bh = await _id_territorio(conn, _BH)
    rio = await _id_territorio(conn, _RIO)
    udi = await _id_territorio(conn, "3170206")  # Uberlândia (MG) — par de BH (cidades parecidas)
    cont = await _id_territorio(conn, "3118601")  # Contagem (MG) — outro par MG

    meta = {
        caged_id: MetaIndicadorSupressao(0, origem_sensivel=False),
        cred_id: MetaIndicadorSupressao(0, origem_sensivel=False),
        sau_id: MetaIndicadorSupressao(5, origem_sensivel=True),
    }
    # BH: muito emprego + crédito + POUCAS internações (menos vulnerável nos 3 = IVM mínimo).
    # Rio: o oposto (mais vulnerável = IVM máx). UDI/Contagem (MG): valores INTERMEDIÁRIOS, para BH
    # ter pares na mesma UF sem deslocar os extremos. n_amostra >= 5 -> saúde não suprimida.
    celulas = [
        CelulaOuro(caged_id, bh, _PERIODO, "mensal", Decimal(10000), None, 5, caged_fonte),
        CelulaOuro(caged_id, rio, _PERIODO, "mensal", Decimal(-5000), None, 5, caged_fonte),
        CelulaOuro(caged_id, udi, _PERIODO, "mensal", Decimal(5000), None, 5, caged_fonte),
        CelulaOuro(caged_id, cont, _PERIODO, "mensal", Decimal(2000), None, 5, caged_fonte),
        CelulaOuro(cred_id, bh, _PERIODO, "mensal", Decimal("2e11"), None, 4, cred_fonte),
        CelulaOuro(cred_id, rio, _PERIODO, "mensal", Decimal("5e10"), None, 4, cred_fonte),
        CelulaOuro(cred_id, udi, _PERIODO, "mensal", Decimal("1.5e11"), None, 4, cred_fonte),
        CelulaOuro(cred_id, cont, _PERIODO, "mensal", Decimal("1e11"), None, 4, cred_fonte),
        CelulaOuro(sau_id, bh, _PERIODO, "mensal", Decimal(20), 20, 4, sau_fonte),
        CelulaOuro(sau_id, rio, _PERIODO, "mensal", Decimal(800), 800, 4, sau_fonte),
        CelulaOuro(sau_id, udi, _PERIODO, "mensal", Decimal(100), 100, 4, sau_fonte),
        CelulaOuro(sau_id, cont, _PERIODO, "mensal", Decimal(300), 300, 4, sau_fonte),
    ]
    await grav_escrever(conn, celulas, meta, caged_fonte)


async def grav_escrever(conn, celulas, meta, fonte_id) -> None:  # noqa: ANN001
    await GravadorOuro(conn).escrever_ouro(
        celulas, meta, ContextoLinhagem(fonte_id, None, "ivm test", "test")
    )


async def test_mapa_semaforo_por_periodo(client) -> None:
    async with connect(get_settings().database_url) as conn:
        await _semear_ivm(conn)
    await refrescar_ivm()

    r = await client.get("/v1/ivm", params={"periodo": "2026-08"})
    assert r.status_code == 200
    body = r.json()
    por_mun = {d["codigo_ibge"]: d for d in body["dados"]}
    assert por_mun[_BH]["ivm"] == 0.0
    assert por_mun[_BH]["semaforo"] == "verde"
    assert por_mun[_BH]["v_saude"] == 0.0  # BH: poucas internações → subíndice de saúde baixo
    assert por_mun[_RIO]["ivm"] == 100.0
    assert por_mun[_RIO]["semaforo"] == "vermelho"
    assert por_mun[_RIO]["v_saude"] == 100.0  # Rio: muitas internações → subíndice de saúde alto
    assert body["meta"]["versao_metodologia"] == "v1.1"
    assert "saude.resp.internacoes_j" in body["meta"]["componentes"]
    # selo de confiança reutilizado (primitivo compartilhado OndeFoi↔IVM): fontes ricas + frescor.
    meta = body["meta"]
    assert {f["sigla"] for f in meta["fontes"]} == {"CAGED", "ESTBAN", "SIH/SUS"}
    assert all({"nome", "orgao", "dominio", "ate", "atraso"} <= set(f) for f in meta["fontes"])
    assert meta["periodo_rotulo"] and meta["atraso_dias"] > 0
    assert "Licença aberta" in meta["licenca"]


async def test_periodo_padrao_e_o_mais_recente(client) -> None:
    async with connect(get_settings().database_url) as conn:
        await _semear_ivm(conn)
    await refrescar_ivm()

    r = await client.get("/v1/ivm")  # sem período → mais recente (2026-08)
    body = r.json()
    assert body["meta"]["periodo"] == "2026-08"
    assert len(body["dados"]) >= 2


async def test_serie_municipio_drilldown(client) -> None:
    # SP tem IVM semeado (2026-02..04) — drill-down sem depender deste teste escrever em SP.
    r = await client.get("/v1/ivm/3550308")
    assert r.status_code == 200
    body = r.json()
    assert body["dados"]
    assert all(d["codigo_ibge"] == "3550308" for d in body["dados"])


async def test_serie_municipio_sem_ivm_404(client) -> None:
    r = await client.get("/v1/ivm/0000000")
    assert r.status_code == 404
    assert r.json()["erro"] == "nao_encontrado"


async def test_v_saude_estado_distingue_supressao_de_cobertura(client) -> None:
    # Seed (ADR-0026, padrão *_estado): SP tem saúde não suprimida em 2026-04; Campinas tem célula
    # k-anon suprimida (n=3<5) no mesmo período; em 2026-02 nenhum tem saúde. v_saude_estado
    # distingue valor × suprimido × sem_cobertura — null-por-supressão ≠ null-por-cobertura.
    por04 = {
        d["codigo_ibge"]: d for d in (await client.get("/v1/ivm?periodo=2026-04")).json()["dados"]
    }
    assert por04["3550308"]["v_saude_estado"] == "valor"
    assert por04["3550308"]["v_saude"] is not None
    assert por04["3509502"]["v_saude_estado"] == "suprimido"  # cadeado legítimo (PII por baixo)
    assert por04["3509502"]["v_saude"] is None  # null-por-supressão

    por02 = {
        d["codigo_ibge"]: d for d in (await client.get("/v1/ivm?periodo=2026-02")).json()["dados"]
    }
    assert por02["3550308"]["v_saude_estado"] == "sem_cobertura"
    assert por02["3550308"]["v_saude"] is None  # null-por-cobertura


async def test_similares_mesma_uf_ivm_proximo(client) -> None:
    # Reusa o seed do mapa (2026-08): BH/UDI/Contagem em MG, Rio em RJ. "Parecida" = MESMA UF, IVM
    # mais próximo — similares de BH traz os MG (UDI/Contagem), nunca o Rio (RJ) nem o próprio.
    async with connect(get_settings().database_url) as conn:
        await _semear_ivm(conn)
    await refrescar_ivm()

    body = (await client.get(f"/v1/ivm/{_BH}/similares")).json()
    cods = [d["codigo_ibge"] for d in body["dados"]]
    assert _BH not in cods  # exclui o próprio município
    assert _RIO not in cods  # outra UF (RJ) não entra
    assert cods, "deveria haver ao menos uma cidade parecida na mesma UF"
    assert all(d["uf"] == "MG" for d in body["dados"])
    assert {"3170206", "3118601"} <= set(cods)  # os pares MG (Uberlândia, Contagem)
