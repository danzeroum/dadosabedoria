"""Testes unitários do AdaptadorAna (Monitor de Secas) — sem rede, sem DB."""

from __future__ import annotations

import pytest

from app.ingestao.adaptadores.ana import AdaptadorAna
from app.ingestao.adaptadores.base import Janela
from tests.fixtures.ana import AMOSTRA, FetcherFake


@pytest.fixture()
def adaptador() -> AdaptadorAna:
    return AdaptadorAna(FetcherFake(AMOSTRA))


@pytest.fixture()
def janela() -> Janela:
    return Janela.de_competencia("202301")


def test_parse_retorna_dataframe_com_cabecalho(adaptador: AdaptadorAna, janela: Janela) -> None:
    bruto, _ = adaptador.baixar_bruto(janela)
    df = adaptador.parse(bruto)
    assert "cod_ibge" in df.columns
    assert "classe_seca" in df.columns
    assert len(df) == 9  # 8 linhas de dados + 1 inválido


def test_transformar_prata_filtra_invalidos(adaptador: AdaptadorAna, janela: Janela) -> None:
    bruto, _ = adaptador.baixar_bruto(janela)
    df = adaptador.parse(bruto)
    prata = adaptador.transformar_prata(df)
    # inválido (classe vazia) e Normal (convertido para 0.0) são mantidos; só a linha vazia some
    assert "9999999" not in prata["cod_ibge"].to_list()
    assert "seca_indice" in prata.columns


def test_transformar_prata_converte_classes(adaptador: AdaptadorAna, janela: Janela) -> None:
    bruto, _ = adaptador.baixar_bruto(janela)
    df = adaptador.parse(bruto)
    prata = adaptador.transformar_prata(df)
    # D3 → 4.0
    ce_rows = prata.filter(prata["cod_ibge"] == "2304400")
    assert len(ce_rows) == 1
    assert ce_rows["seca_indice"][0] == pytest.approx(4.0)


def test_agregar_calcula_maximo_por_municipio(adaptador: AdaptadorAna, janela: Janela) -> None:
    bruto, _ = adaptador.baixar_bruto(janela)
    df = adaptador.parse(bruto)
    prata = adaptador.transformar_prata(df)
    ouro = adaptador.agregar(prata)
    # SP tem dois meses: Normal(0) e D1(2) → máximo = 2.0
    sp = ouro.filter(ouro["cod_ibge"] == "3550308")
    assert sp["seca_indice"][0] == pytest.approx(2.0)
    # RJ tem D0(1) e Normal(0) → máximo = 1.0
    rj = ouro.filter(ouro["cod_ibge"] == "3304557")
    assert rj["seca_indice"][0] == pytest.approx(1.0)


def test_extrair_valida_contrato(adaptador: AdaptadorAna, janela: Janela) -> None:
    df = adaptador.extrair(janela)
    assert "cod_ibge" in df.columns
    assert "classe_seca" in df.columns
