"""Unidade do adaptador CAGED (parse/prata/agregação) e da agenda — puros, sem rede/DB."""

from __future__ import annotations

from datetime import date
from pathlib import Path

from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.caged import CONTRATO, AdaptadorCaged
from app.ingestao.agenda import competencia_alvo
from tests.fixtures.caged import AMOSTRA_FIEL, AMOSTRA_UNIT, FetcherFake

_FIXTURE_REAL = Path(__file__).resolve().parent.parent / "fixtures" / "caged_amostra_real.csv"


def _adaptador() -> AdaptadorCaged:
    return AdaptadorCaged(FetcherFake(AMOSTRA_UNIT))


def test_parse_le_colunas() -> None:
    df = _adaptador().parse(AMOSTRA_UNIT)
    assert "município" in df.columns
    assert df.height == 8


def test_prata_normaliza_e_filtra() -> None:
    a = _adaptador()
    df = a.transformar_prata(a.parse(AMOSTRA_UNIT))
    assert set(df.columns) == {"competencia", "municipio", "saldo_mov", "salario_brl"}
    assert df.height == 8


def test_agregar_saldo() -> None:
    a = _adaptador()
    saldos = a.agregar_saldo(a.transformar_prata(a.parse(AMOSTRA_UNIT)))
    por_municipio = {r["municipio"]: r["saldo"] for r in saldos.iter_rows(named=True)}
    assert por_municipio == {"355030": 2, "350950": -1, "999999": 1}


def test_extrair_usa_fetcher() -> None:
    df = _adaptador().extrair(Janela(2026, 7))
    assert df.height == 8


def test_competencia_alvo() -> None:
    assert competencia_alvo(date(2026, 6, 15)) == "202604"
    assert competencia_alvo(date(2026, 1, 10)) == "202511"  # vira o ano
    assert competencia_alvo(date(2026, 3, 1), defasagem_meses=1) == "202602"


# ---------------------------------------------------------------------------
# Testes de forma fiel-à-fonte (ADR-0036)
# ---------------------------------------------------------------------------


def test_contrato_fiel_forma_28_colunas() -> None:
    """Parse de AMOSTRA_FIEL (28 colunas) deve passar na validação do contrato."""
    a = AdaptadorCaged(FetcherFake(AMOSTRA_FIEL))
    df = a.parse(AMOSTRA_FIEL)
    n_cols = df.shape[1]
    print(f"colunas={n_cols}")
    assert n_cols == 28, f"esperado 28 colunas, obtido {n_cols}"
    CONTRATO.validar(df)  # deve passar sem exceção


def test_municipio_6_digitos_na_fixture_real() -> None:
    """Todos os municípios na fixture real têm exactamente 6 dígitos após prata."""
    bruto = _FIXTURE_REAL.read_bytes()
    a = AdaptadorCaged(FetcherFake(bruto))
    df_prata = a.transformar_prata(a.parse(bruto))
    invalidos = [m for m in df_prata["municipio"].to_list() if m and len(str(m)) != 6]
    assert invalidos == [], f"municípios com len != 6: {invalidos[:10]}"


def test_saldo_semantica_adm_demissao() -> None:
    """Saldo por município: 355030 (+1 -1) = 0, 351905 (+1) = 1."""
    a = AdaptadorCaged(FetcherFake(AMOSTRA_FIEL))
    df_prata = a.transformar_prata(a.parse(AMOSTRA_FIEL))
    saldos = a.agregar_saldo(df_prata)
    por_mun = {r["municipio"]: r["saldo"] for r in saldos.iter_rows(named=True)}
    assert por_mun.get("355030") == 0, f"355030 esperado 0, obtido {por_mun.get('355030')}"
    assert por_mun.get("351905") == 1, f"351905 esperado 1, obtido {por_mun.get('351905')}"


def test_parse_fixture_real_shape() -> None:
    """Fixture real tem 2000 linhas e 28 colunas (sem cabeçalho)."""
    bruto = _FIXTURE_REAL.read_bytes()
    a = AdaptadorCaged(FetcherFake(bruto))
    df = a.parse(bruto)
    assert df.shape[0] == 2000, f"esperado 2000 linhas, obtido {df.shape[0]}"
    assert df.shape[1] == 28, f"esperado 28 colunas, obtido {df.shape[1]}"
