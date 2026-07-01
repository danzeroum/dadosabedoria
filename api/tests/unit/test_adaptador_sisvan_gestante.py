"""Testes unitários do AdaptadorSisvanGestante (SAUDE-03) — forma API JSON."""

from __future__ import annotations

import polars as pl
import pytest

from app.ingestao.adaptadores.sisvan import AdaptadorSisvanGestante
from tests.fixtures.sisvan_gestante import AMOSTRA_GESTANTE, FetcherFake


@pytest.fixture()
def adaptador() -> AdaptadorSisvanGestante:
    return AdaptadorSisvanGestante(FetcherFake(AMOSTRA_GESTANTE))


# ------------------------------------------------------------------ parse


def test_parse_colunas_corretas(adaptador: AdaptadorSisvanGestante) -> None:
    df = adaptador.parse(AMOSTRA_GESTANTE)
    assert "codigo_municipio" in df.columns
    assert "codigo_estado_nutricional_imc_gestante" in df.columns
    assert df.height > 0


def test_parse_json_invalido(adaptador: AdaptadorSisvanGestante) -> None:
    """Bytes corrompidos retornam DataFrame vazio com colunas corretas."""
    df = adaptador.parse(b"\x00\xff\xfe invalid bytes")
    assert "codigo_municipio" in df.columns
    assert df.height == 0


# ------------------------------------------------------------------ transformar_prata


def test_transformar_prata_filtra_publico_gestante(adaptador: AdaptadorSisvanGestante) -> None:
    df = adaptador.parse(AMOSTRA_GESTANTE)
    prata = adaptador.transformar_prata(df)
    assert "cod_ibge" in prata.columns
    # Campinas: 20 gestantes válidas (o registro não-gestante de classificação nula é filtrado)
    campinas = prata.filter(pl.col("cod_ibge") == "350950")
    assert campinas.height == 20


def test_transformar_prata_marca_baixo_peso(adaptador: AdaptadorSisvanGestante) -> None:
    df = adaptador.parse(AMOSTRA_GESTANTE)
    prata = adaptador.transformar_prata(df)
    # baixo_peso é 0/1
    assert set(prata["baixo_peso"].to_list()) <= {0, 1}


def test_transformar_prata_filtra_ibge_vazio(adaptador: AdaptadorSisvanGestante) -> None:
    df = adaptador.parse(AMOSTRA_GESTANTE)
    prata = adaptador.transformar_prata(df)
    ibges = prata["cod_ibge"].to_list()
    assert "" not in ibges
    assert None not in ibges


# ------------------------------------------------------------------ agregar


def test_agregar_pct_correto(adaptador: AdaptadorSisvanGestante) -> None:
    df = adaptador.parse(AMOSTRA_GESTANTE)
    ouro = adaptador.agregar(adaptador.transformar_prata(df))
    assert "gestante_baixo_peso_pct" in ouro.columns
    assert "n_total" in ouro.columns
    assert "n_baixo_peso" in ouro.columns


def test_fixture_campinas(adaptador: AdaptadorSisvanGestante) -> None:
    """Campinas: 3 baixo peso em 20 gestantes = 15% → moderado."""
    from app.produtos.sentinela_materna import classificar_nivel

    df = adaptador.parse(AMOSTRA_GESTANTE)
    ouro = adaptador.agregar(adaptador.transformar_prata(df))

    row = ouro.filter(pl.col("cod_ibge") == "350950").to_dicts()[0]
    assert row["n_total"] == 20
    assert row["n_baixo_peso"] == 3
    assert abs(row["gestante_baixo_peso_pct"] - 15.0) < 0.01
    assert classificar_nivel(row["gestante_baixo_peso_pct"]) == "moderado"


def test_fixture_sp_baixo(adaptador: AdaptadorSisvanGestante) -> None:
    """SP: 1 em 30 = 3.33% → baixo."""
    from app.produtos.sentinela_materna import classificar_nivel

    df = adaptador.parse(AMOSTRA_GESTANTE)
    ouro = adaptador.agregar(adaptador.transformar_prata(df))

    row = ouro.filter(pl.col("cod_ibge") == "355030").to_dicts()[0]
    assert row["n_total"] == 30
    assert row["n_baixo_peso"] == 1
    assert abs(row["gestante_baixo_peso_pct"] - 3.33) < 0.01
    assert classificar_nivel(row["gestante_baixo_peso_pct"]) == "baixo"
