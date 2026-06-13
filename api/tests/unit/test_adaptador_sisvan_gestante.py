"""Testes unitários do AdaptadorSisvanGestante (SAUDE-03)."""

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
    assert "CO_MUNICIPIO_IBGE" in df.columns
    assert "CO_PUBLICO_ALVO" in df.columns
    assert "CO_ESTADO_NUTRI_GESTANTE" in df.columns
    assert df.height > 0


def test_parse_csv_invalido(adaptador: AdaptadorSisvanGestante) -> None:
    """Bytes corrompidos retornam DataFrame vazio com colunas corretas."""
    df = adaptador.parse(b"\x00\xff\xfe invalid bytes")
    assert "CO_MUNICIPIO_IBGE" in df.columns
    assert df.height == 0


# ------------------------------------------------------------------ transformar_prata


def test_transformar_prata_filtra_publico_gestante(adaptador: AdaptadorSisvanGestante) -> None:
    df = adaptador.parse(AMOSTRA_GESTANTE)
    prata = adaptador.transformar_prata(df)
    # Nenhuma linha de CRIANCA deve aparecer
    assert "cod_ibge" in prata.columns
    # Campinas: apenas as linhas de GESTANTE (20 válidas + 3 inválidas descartadas)
    campinas = prata.filter(pl.col("cod_ibge") == "3509502")
    assert campinas.height == 20  # 17 adequado + 3 baixo peso (a de CRIANCA é filtrada)


def test_transformar_prata_filtra_estado_invalido(adaptador: AdaptadorSisvanGestante) -> None:
    df = adaptador.parse(AMOSTRA_GESTANTE)
    prata = adaptador.transformar_prata(df)
    # Estados 0 e 5 (fora do range 1–4) devem ser descartados
    estados = prata["estado"].to_list()
    assert all(1 <= e <= 4 for e in estados)


def test_transformar_prata_filtra_ibge_vazio(adaptador: AdaptadorSisvanGestante) -> None:
    df = adaptador.parse(AMOSTRA_GESTANTE)
    prata = adaptador.transformar_prata(df)
    # Linha com IBGE vazio deve ser descartada
    ibges = prata["cod_ibge"].to_list()
    assert "" not in ibges
    assert None not in ibges


# ------------------------------------------------------------------ agregar


def test_agregar_pct_correto(adaptador: AdaptadorSisvanGestante) -> None:
    df = adaptador.parse(AMOSTRA_GESTANTE)
    prata = adaptador.transformar_prata(df)
    ouro = adaptador.agregar(prata)
    assert "gestante_baixo_peso_pct" in ouro.columns
    assert "n_total" in ouro.columns
    assert "n_baixo_peso" in ouro.columns


def test_fixture_campinas(adaptador: AdaptadorSisvanGestante) -> None:
    """Campinas: 3 baixo peso em 20 gestantes = 15% → moderado."""
    from app.produtos.sentinela_materna import classificar_nivel

    df = adaptador.parse(AMOSTRA_GESTANTE)
    prata = adaptador.transformar_prata(df)
    ouro = adaptador.agregar(prata)

    row = ouro.filter(pl.col("cod_ibge") == "3509502").to_dicts()[0]
    assert row["n_total"] == 20
    assert row["n_baixo_peso"] == 3
    assert abs(row["gestante_baixo_peso_pct"] - 15.0) < 0.01
    assert classificar_nivel(row["gestante_baixo_peso_pct"]) == "moderado"


def test_fixture_sp_baixo(adaptador: AdaptadorSisvanGestante) -> None:
    """SP: 1 em 30 = 3.33% → baixo."""
    from app.produtos.sentinela_materna import classificar_nivel

    df = adaptador.parse(AMOSTRA_GESTANTE)
    prata = adaptador.transformar_prata(df)
    ouro = adaptador.agregar(prata)

    row = ouro.filter(pl.col("cod_ibge") == "3550308").to_dicts()[0]
    assert row["n_total"] == 30
    assert row["n_baixo_peso"] == 1
    assert abs(row["gestante_baixo_peso_pct"] - 3.33) < 0.01
    assert classificar_nivel(row["gestante_baixo_peso_pct"]) == "baixo"
