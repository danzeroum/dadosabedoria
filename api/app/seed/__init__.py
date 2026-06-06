"""Seed inicial — governança/dimensões + fatos da Onda 1.

Regra do produto: os FATOS passam pelo MESMO caminho ouro da ingestão (``escrever_ouro``:
supressão + linhagem) — nada de INSERT cru em ``valor``. As dimensões (base_legal, fonte,
territorio, indicador) são upserts idempotentes — são metadados de governança, não fatos
sujeitos a k-anonimato.

Inclui de propósito uma célula sub-limiar de indicador de origem sensível (Campinas), para que a
supressão seja exercida ponta a ponta já no seed (ADR-0004).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import Table
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core import tables as t
from app.core.config import get_settings
from app.core.db import connect
from app.ingestao.ouro import CelulaOuro, ContextoLinhagem, GravadorOuro
from app.ingestao.supressao import MetaIndicadorSupressao

# --------------------------------------------------------------------------- dimensões

BASE_LEGAL: list[dict[str, str]] = [
    {
        "codigo": "obrigacao_legal",
        "artigo": "LGPD Art. 7, II",
        "hipotese": "Cumprimento de obrigação legal",
        "justificativa": (
            "Dados estatísticos públicos coletados por órgão governamental no exercício de "
            "política pública; reuso de dado já público e anonimizado."
        ),
    },
    {
        "codigo": "consentimento",
        "artigo": "LGPD Art. 7, I",
        "hipotese": "Consentimento do titular",
        "justificativa": (
            "Cidadão que opta por receber alertas fornece contato e localização para finalidade "
            "específica e informada."
        ),
    },
    {
        "codigo": "consentimento_sensivel",
        "artigo": "LGPD Art. 11, I",
        "hipotese": "Consentimento específico e destacado",
        "justificativa": (
            "Condição de saúde informada pelo cidadão (ex.: asmático) para personalizar alertas; "
            "dado sensível, consentimento explícito e em destaque."
        ),
    },
]

FONTES: list[dict[str, Any]] = [
    {
        "codigo": "ibge",
        "nome": "IBGE Agregados/Malhas",
        "orgao": "IBGE",
        "url_doc": "https://servicodados.ibge.gov.br/api/docs",
        "licenca": "LAI/Dados Abertos",
        "permite_uso_comercial": True,
        "permite_redistribuicao": True,
        "atualizacao": "irregular",
        "lag_tipico_dias": None,
        "base_legal": "obrigacao_legal",
    },
    {
        "codigo": "novo_caged",
        "nome": "Novo CAGED",
        "orgao": "MTE/PDET",
        "url_doc": "https://pdet.mte.gov.br",
        "licenca": "LAI/Dados Abertos",
        "permite_uso_comercial": True,
        "permite_redistribuicao": True,
        "atualizacao": "mensal",
        "lag_tipico_dias": 40,
        "base_legal": "obrigacao_legal",
    },
    {
        "codigo": "bcb_sgs",
        "nome": "BCB SGS",
        "orgao": "Banco Central do Brasil",
        "url_doc": "https://api.bcb.gov.br",
        "licenca": "LAI/Dados Abertos",
        "permite_uso_comercial": True,
        "permite_redistribuicao": True,
        "atualizacao": "mensal",
        "lag_tipico_dias": 30,
        "base_legal": "obrigacao_legal",
    },
    {
        "codigo": "bcb_estban",
        "nome": "BCB ESTBAN",
        "orgao": "Banco Central do Brasil",
        "url_doc": "https://api.bcb.gov.br",
        "licenca": "LAI/Dados Abertos",
        "permite_uso_comercial": True,
        "permite_redistribuicao": True,
        "atualizacao": "mensal",
        "lag_tipico_dias": 60,
        "base_legal": "obrigacao_legal",
    },
    {
        "codigo": "datasus_sih",
        "nome": "SIH/SUS",
        "orgao": "Ministério da Saúde/DATASUS",
        "url_doc": "https://datasus.saude.gov.br",
        "licenca": "LAI/Dados Abertos (anonimizado)",
        "permite_uso_comercial": True,
        "permite_redistribuicao": True,
        "atualizacao": "mensal",
        "lag_tipico_dias": 90,
        "base_legal": "obrigacao_legal",
    },
    {
        "codigo": "siconfi",
        "nome": "SICONFI/STN",
        "orgao": "Tesouro Nacional (STN)",
        "url_doc": "https://apidatalake.tesouro.gov.br/ords/siconfi/docs",
        "licenca": "LAI/Dados Abertos",
        "permite_uso_comercial": True,
        "permite_redistribuicao": True,
        "atualizacao": "anual",
        "lag_tipico_dias": 365,
        "base_legal": "obrigacao_legal",
    },
    {
        "codigo": "inep",
        "nome": "INEP — Censo Escolar",
        "orgao": "INEP/MEC",
        "url_doc": "https://www.gov.br/inep/pt-br/acesso-a-informacao/dados-abertos/microdados",
        "licenca": "LAI/Dados Abertos",
        "permite_uso_comercial": True,
        "permite_redistribuicao": True,
        "atualizacao": "anual",
        "lag_tipico_dias": 365,
        "base_legal": "obrigacao_legal",
    },
    {
        "codigo": "pncp",
        "nome": "PNCP — Contratações Públicas",
        "orgao": "PNCP (MGI)",
        "url_doc": "https://pncp.gov.br/api/consulta/swagger-ui/index.html",
        "licenca": "LAI/Dados Abertos",
        "permite_uso_comercial": True,
        "permite_redistribuicao": True,
        "atualizacao": "diaria",
        "lag_tipico_dias": 30,
        "base_legal": "obrigacao_legal",
    },
]

# (codigo_ibge, nome, nivel, uf, populacao, codigo_ibge_do_pai)
TERRITORIOS = [
    ("1", "Brasil", "pais", None, 203080756, None),
    ("3", "Região Sudeste", "regiao", None, None, "1"),
    ("35", "São Paulo", "uf", "SP", None, "3"),
    ("3550308", "São Paulo", "municipio", "SP", 11451245, "35"),
    ("3509502", "Campinas", "municipio", "SP", 1213792, "35"),
]

INDICADORES: list[dict[str, Any]] = [
    {
        "codigo": "trabalho.emprego.saldo_caged",
        "nome": "Saldo de empregos formais",
        "descricao": "Admissões menos desligamentos com carteira no mês.",
        "dominio": "trabalho",
        "subdominio": "emprego_formal",
        "unidade": "contagem",
        "polaridade": "maior_melhor",
        "atualizacao": "mensal",
        "nivel_minimo_agregacao": "municipio",
        "n_minimo": 0,
        "classificacao": "nao_pessoal",
        "origem_sensivel": False,
        "publico": True,
        "base_legal": "obrigacao_legal",
        "fonte": "novo_caged",
        "codigo_externo": "CNAE",
        "metodologia": "Soma de admissões menos desligamentos do Novo CAGED por município/mês.",
    },
    {
        "codigo": "credito.operacoes.saldo_total",
        "nome": "Saldo de operações de crédito",
        "descricao": "Saldo total de operações de crédito do SFN por município/mês (ESTBAN).",
        "dominio": "credito",
        "subdominio": "operacoes",
        "unidade": "reais",
        "polaridade": "neutra",
        "atualizacao": "mensal",
        "nivel_minimo_agregacao": "municipio",
        "n_minimo": 0,
        "classificacao": "nao_pessoal",
        "origem_sensivel": False,
        "publico": True,
        "base_legal": "obrigacao_legal",
        "fonte": "bcb_estban",
        "codigo_externo": None,
        "metodologia": "Soma dos saldos de operações de crédito do ESTBAN por município/mês.",
    },
    {
        "codigo": "saude.resp.internacoes_j",
        "nome": "Internações por doenças respiratórias",
        "descricao": "Internações no SUS com CID-10 do grupo J (respiratórias) por mês.",
        "dominio": "saude",
        "subdominio": "respiratorio",
        "unidade": "contagem",
        "polaridade": "menor_melhor",
        "atualizacao": "mensal",
        "nivel_minimo_agregacao": "municipio",
        "n_minimo": 5,
        "classificacao": "nao_pessoal",
        "origem_sensivel": True,
        "publico": True,
        "base_legal": "obrigacao_legal",
        "fonte": "datasus_sih",
        "codigo_externo": "CID-10:J00-J99",
        "metodologia": (
            "Contagem de AIH com diagnóstico principal no grupo J do SIH/SUS por município/mês."
        ),
    },
    {
        "codigo": "financas.transferencias.correntes",
        "nome": "Transferências correntes recebidas",
        "descricao": "Transferências correntes recebidas pelo município no exercício (DCA).",
        "dominio": "financas",
        "subdominio": "transferencias",
        "unidade": "reais",
        "polaridade": "neutra",
        "atualizacao": "anual",
        "nivel_minimo_agregacao": "municipio",
        "n_minimo": 0,
        "classificacao": "nao_pessoal",
        "origem_sensivel": False,
        "publico": True,
        "base_legal": "obrigacao_legal",
        "fonte": "siconfi",
        "codigo_externo": "DCA",
        "metodologia": (
            "Soma das Transferências Correntes da DCA (SICONFI/STN) por município/exercício."
        ),
    },
    {
        "codigo": "educacao.matriculas.fundamental",
        "nome": "Matrículas no ensino fundamental",
        "descricao": "Matrículas no ensino fundamental por município (Censo Escolar/INEP).",
        "dominio": "educacao",
        "subdominio": "matriculas",
        "unidade": "contagem",
        "polaridade": "neutra",
        "atualizacao": "anual",
        "nivel_minimo_agregacao": "municipio",
        "n_minimo": 0,
        "classificacao": "nao_pessoal",
        "origem_sensivel": False,
        "publico": True,
        "base_legal": "obrigacao_legal",
        "fonte": "inep",
        "codigo_externo": "QT_MAT_FUND",
        "metodologia": (
            "Soma das matrículas no ensino fundamental (QT_MAT_FUND) do Censo Escolar por "
            "município/ano."
        ),
    },
    {
        "codigo": "compras.contratos.valor_total",
        "nome": "Valor total de contratos públicos",
        "descricao": "Soma do valor dos contratos públicos do município no ano (PNCP).",
        "dominio": "compras",
        "subdominio": "contratos",
        "unidade": "reais",
        "polaridade": "neutra",
        "atualizacao": "anual",
        "nivel_minimo_agregacao": "municipio",
        "n_minimo": 0,
        "classificacao": "nao_pessoal",
        "origem_sensivel": False,
        "publico": True,
        "base_legal": "obrigacao_legal",
        "fonte": "pncp",
        "codigo_externo": "valorGlobal",
        "metodologia": (
            "Soma do valorGlobal dos contratos do PNCP por município/ano (unidadeOrgao.codigoIbge)."
        ),
    },
]


async def _upsert(conn: AsyncConnection, tabela: Table, conflito: list[str], valores: dict) -> int:
    ins = pg_insert(tabela).values(**valores)
    set_ = {k: getattr(ins.excluded, k) for k in valores if k not in conflito}
    stmt = ins.on_conflict_do_update(index_elements=conflito, set_=set_).returning(tabela.c.id)
    res = await conn.execute(stmt)
    return int(res.scalar_one())


async def executar_seed(conn: AsyncConnection) -> dict[str, int]:
    """Semeia dimensões (upsert) e fatos (via ``escrever_ouro``). Idempotente."""
    bl_ids = {r["codigo"]: await _upsert(conn, t.base_legal, ["codigo"], r) for r in BASE_LEGAL}

    fonte_ids: dict[str, int] = {}
    for f in FONTES:
        row = {k: v for k, v in f.items() if k != "base_legal"}
        row["base_legal_id"] = bl_ids[f["base_legal"]]
        fonte_ids[f["codigo"]] = await _upsert(conn, t.fonte, ["codigo"], row)

    terr_ids: dict[str, int] = {}
    for codigo_ibge, nome, nivel, uf, pop, pai in TERRITORIOS:
        row = {
            "codigo_ibge": codigo_ibge,
            "nome": nome,
            "nivel": nivel,
            "uf": uf,
            "populacao": pop,
            "pai_id": terr_ids[pai] if pai else None,
        }
        terr_ids[codigo_ibge] = await _upsert(conn, t.territorio, ["codigo_ibge"], row)

    ind_ids: dict[str, int] = {}
    meta: dict[int, MetaIndicadorSupressao] = {}
    for ind in INDICADORES:
        row = {k: v for k, v in ind.items() if k not in ("base_legal", "fonte")}
        row["base_legal_id"] = bl_ids[ind["base_legal"]]
        row["fonte_id"] = fonte_ids[ind["fonte"]]
        iid = await _upsert(conn, t.indicador, ["codigo"], row)
        ind_ids[ind["codigo"]] = iid
        meta[iid] = MetaIndicadorSupressao(
            n_minimo=int(ind["n_minimo"]), origem_sensivel=bool(ind["origem_sensivel"])
        )

    await _semear_fatos(conn, fonte_ids, terr_ids, ind_ids, meta)
    return {"indicadores": len(ind_ids), "territorios": len(terr_ids), "fontes": len(fonte_ids)}


async def _semear_fatos(
    conn: AsyncConnection,
    fonte_ids: dict[str, int],
    terr_ids: dict[str, int],
    ind_ids: dict[str, int],
    meta: dict[int, MetaIndicadorSupressao],
) -> None:
    grav = GravadorOuro(conn)  # usa SupressaoKAnonimato por padrão

    sp = terr_ids["3550308"]
    cps = terr_ids["3509502"]

    # EMPREGO (saldo CAGED): n_amostra None, n_minimo 0 → nunca suprimido.
    caged = ind_ids["trabalho.emprego.saldo_caged"]
    f_caged = fonte_ids["novo_caged"]
    caged_cels = [
        CelulaOuro(caged, sp, date(2026, 2, 1), "mensal", Decimal(8200), None, 5, f_caged),
        CelulaOuro(caged, sp, date(2026, 3, 1), "mensal", Decimal(-15400), None, 5, f_caged),
        CelulaOuro(caged, sp, date(2026, 4, 1), "mensal", Decimal(-9100), None, 5, f_caged),
        CelulaOuro(caged, cps, date(2026, 2, 1), "mensal", Decimal(1200), None, 5, f_caged),
        CelulaOuro(caged, cps, date(2026, 3, 1), "mensal", Decimal(-800), None, 5, f_caged),
        CelulaOuro(caged, cps, date(2026, 4, 1), "mensal", Decimal(-300), None, 5, f_caged),
    ]
    await grav.escrever_ouro(
        caged_cels,
        meta,
        ContextoLinhagem(f_caged, caged, "seed Onda 1: prata->ouro (saldo CAGED)", "seed"),
    )

    # CRÉDITO (ESTBAN): reais; n_minimo 0.
    cred = ind_ids["credito.operacoes.saldo_total"]
    f_estban = fonte_ids["bcb_estban"]
    cred_cels = [
        CelulaOuro(cred, sp, date(2026, 2, 1), "mensal", Decimal("1.00e11"), None, 4, f_estban),
        CelulaOuro(cred, sp, date(2026, 3, 1), "mensal", Decimal("1.01e11"), None, 4, f_estban),
        CelulaOuro(cred, sp, date(2026, 4, 1), "mensal", Decimal("0.99e11"), None, 4, f_estban),
    ]
    await grav.escrever_ouro(
        cred_cels,
        meta,
        ContextoLinhagem(f_estban, cred, "seed Onda 1: prata->ouro (crédito ESTBAN)", "seed"),
    )

    # SAÚDE (origem sensível): SP acima do limiar; Campinas n_amostra=3 < 5 → SUPRIMIDO.
    sau = ind_ids["saude.resp.internacoes_j"]
    f_sih = fonte_ids["datasus_sih"]
    sau_cels = [
        CelulaOuro(sau, sp, date(2026, 4, 1), "mensal", Decimal(310), 310, 4, f_sih),
        CelulaOuro(sau, sp, date(2026, 5, 1), "mensal", Decimal(420), 420, 4, f_sih),
        CelulaOuro(sau, sp, date(2026, 6, 1), "mensal", Decimal(660), 660, 4, f_sih),
        CelulaOuro(sau, cps, date(2026, 4, 1), "mensal", Decimal(3), 3, 3, f_sih),  # < limiar
    ]
    await grav.escrever_ouro(
        sau_cels,
        meta,
        ContextoLinhagem(f_sih, sau, "seed Onda 1: prata->ouro (internações resp.)", "seed"),
    )

    # FINANÇAS (SICONFI/DCA, anual): transferências correntes por município/exercício. n_minimo 0.
    fin = ind_ids["financas.transferencias.correntes"]
    f_siconfi = fonte_ids["siconfi"]
    fin_cels = [
        CelulaOuro(fin, sp, date(2024, 1, 1), "anual", Decimal("1.50e9"), None, 4, f_siconfi),
        CelulaOuro(fin, cps, date(2024, 1, 1), "anual", Decimal("2.50e8"), None, 4, f_siconfi),
    ]
    await grav.escrever_ouro(
        fin_cels,
        meta,
        ContextoLinhagem(
            f_siconfi, fin, "seed Onda 2A: prata->ouro (SICONFI transferências)", "seed"
        ),
    )

    # EDUCAÇÃO (INEP/Censo Escolar, anual): matrículas no fundamental por município/ano. n_minimo 0.
    edu = ind_ids["educacao.matriculas.fundamental"]
    f_inep = fonte_ids["inep"]
    edu_cels = [
        CelulaOuro(edu, sp, date(2024, 1, 1), "anual", Decimal(980000), None, 4, f_inep),
        CelulaOuro(edu, cps, date(2024, 1, 1), "anual", Decimal(150000), None, 4, f_inep),
    ]
    await grav.escrever_ouro(
        edu_cels,
        meta,
        ContextoLinhagem(f_inep, edu, "seed Onda 2A: prata->ouro (INEP matrículas)", "seed"),
    )

    # COMPRAS (PNCP/contratos, anual): valor de contratos públicos por município/ano. n_minimo 0.
    com = ind_ids["compras.contratos.valor_total"]
    f_pncp = fonte_ids["pncp"]
    com_cels = [
        CelulaOuro(com, sp, date(2024, 1, 1), "anual", Decimal("2.00e9"), None, 4, f_pncp),
        CelulaOuro(com, cps, date(2024, 1, 1), "anual", Decimal("3.00e8"), None, 4, f_pncp),
    ]
    await grav.escrever_ouro(
        com_cels,
        meta,
        ContextoLinhagem(f_pncp, com, "seed Onda 2A: prata->ouro (PNCP contratos)", "seed"),
    )


async def main() -> None:
    from app.indicadores.ivm import refrescar_ivm

    settings = get_settings()
    async with connect(settings.database_url) as conn:
        resumo = await executar_seed(conn)
    await refrescar_ivm()  # popula a MV do IVM após o seed (fora da transação)
    print(f"seed concluído: {resumo}")  # noqa: T201 (saída de CLI)
