"""Testes unitários do módulo de saneamento."""

from app.domains.saneamento import ModuloSaneamento
from app.ingestao.adaptadores.saneamento import (
    CODIGO_AGUA,
    CODIGO_ESGOTO,
    CONTRATO,
    AdaptadorSnis,
)
from tests.fixtures.saneamento import AMOSTRA, FetcherFake


def test_modulo_registra_dois_indicadores():
    m = ModuloSaneamento()
    inds = m.registrar_indicadores()
    codigos = {i["codigo"] for i in inds}
    assert CODIGO_AGUA in codigos
    assert CODIGO_ESGOTO in codigos


def test_modulo_registra_adaptador():
    m = ModuloSaneamento()
    assert len(m.registrar_adaptadores_fonte()) == 1


def test_adaptador_parse_fixture():
    adp = AdaptadorSnis(FetcherFake(AMOSTRA))
    df = adp.parse(AMOSTRA)
    assert "cod_municipio" in df.columns
    assert "in023_ae" in df.columns


def test_adaptador_contrato_ok():
    adp = AdaptadorSnis(FetcherFake(AMOSTRA))
    df = adp.parse(AMOSTRA)
    CONTRATO.validar(df)  # não deve lançar


def test_adaptador_transformar_prata():
    adp = AdaptadorSnis(FetcherFake(AMOSTRA))
    df = adp.parse(AMOSTRA)
    prata = adp.transformar_prata(df)
    assert "cod_ibge" in prata.columns
    assert "agua_pct" in prata.columns
    assert "esgoto_pct" in prata.columns
    # Município inválido (9999999) deve ser mantido — filtro é na prata mas IBGE inválido
    # fica para o pipeline ignorar via mapa de municípios
    assert prata["agua_pct"].is_not_null().all()


def test_adaptador_agregar():
    adp = AdaptadorSnis(FetcherFake(AMOSTRA))
    df = adp.parse(AMOSTRA)
    agregado = adp.agregar(adp.transformar_prata(df))
    assert "cod_ibge" in agregado.columns
    # 6 municípios válidos (São Paulo, Rio, Brasília, Belém, Fortaleza, Campinas, 9999999)
    # 9999999 tem agua_pct não-nulo → está incluído, mas com esgoto null
    assert len(agregado) == 7


def test_decimal_br_converte():
    adp = AdaptadorSnis(FetcherFake(AMOSTRA))
    df = adp.parse(AMOSTRA)
    prata = adp.transformar_prata(df)
    sp = prata.filter(prata["cod_ibge"] == "3550308")
    assert abs(sp["agua_pct"][0] - 99.82) < 0.01
