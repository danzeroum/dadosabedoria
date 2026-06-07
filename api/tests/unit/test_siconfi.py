"""Unidade do adaptador SICONFI (parse/prata/agregação + contrato) — puro, sem rede/DB.

Os testes exercitam a **forma real** do DCA (validada no #0, ADR-0028): ``cod_ibge`` int, ``valor``
numérico, dimensão ``coluna`` (realizada vs. deduções) e conta prefixada por código (orçamentária
vs. intra). O ``test_forma_real_funcoes`` tranca o vocabulário de função promovido **da fonte**.
"""

from __future__ import annotations

import json

import polars as pl
import pytest

from app.ingestao.adaptadores.base import Janela
from app.ingestao.adaptadores.siconfi import (
    CONTRATO,
    FUNCOES_SICONFI,
    AdaptadorSiconfi,
    e_funcao,
    parse_funcao,
)
from app.ingestao.contratos import ContratoVioladoError
from tests.fixtures.siconfi import AMOSTRA, AMOSTRA_FUNCOES, FetcherFake


def _ad() -> AdaptadorSiconfi:
    return AdaptadorSiconfi(FetcherFake(AMOSTRA))


def test_parse_le_items() -> None:
    df = _ad().parse(AMOSTRA)
    assert {"cod_ibge", "valor", "conta", "coluna", "cod_conta"} <= set(df.columns)
    assert df["cod_ibge"].dtype == pl.Int64  # forma real: cod_ibge é inteiro (não string)
    assert df.height == 5


def test_prata_filtra_conta_alvo_e_coluna() -> None:
    a = _ad()
    df = a.transformar_prata(a.parse(AMOSTRA))
    assert set(df.columns) == {"cod_ibge", "valor"}
    # Sobram só as 2 Transf. Correntes ORÇAMENTÁRIAS realizadas; caem a dedução (outra coluna),
    # a intra-orçamentária (RI7.7...) e o off-target (impostos).
    assert df.height == 2


def test_agregar_nao_dobra_com_deducoes() -> None:
    a = _ad()
    ag = a.agregar(a.transformar_prata(a.parse(AMOSTRA)))
    por = {r["cod_ibge"]: r["transferencias"] for r in ag.iter_rows(named=True)}
    # SP = só a realizada (1.000.000), sem somar a dedução (300.000) nem a intra (50.000).
    assert por == {"3550308": 1_000_000.0, "3509502": 250_000.0}


def test_extrair_valida_contrato() -> None:
    assert _ad().extrair(Janela(2024, 1)).height == 5


def test_contrato_reprova_layout_mudado() -> None:
    df = pl.DataFrame({"cod_ibge": [3550308], "valor": [1.0]})  # faltam conta/coluna/cod_conta
    with pytest.raises(ContratoVioladoError):
        CONTRATO.validar(df)


def test_forma_real_funcoes() -> None:
    """Forma-verdade do Anexo I-E (#0): vocabulário de função DA FONTE, sem campo de sigilo."""
    itens = json.loads(AMOSTRA_FUNCOES)["items"]

    # (b) detecção de função de 1º nível: pega "10 - Saúde", ignora a subfunção "10.301 - ...".
    assert e_funcao("10 - Saúde") is True
    assert e_funcao("10.301 - Atenção Básica") is False
    assert parse_funcao("12 - Educação") == ("12", "Educação")
    assert parse_funcao("Total Geral da Despesa por Função") is None

    # Todo membro detectado no dado real está no vocabulário promovido da fonte, com o MESMO nome.
    detectadas = {parse_funcao(i["conta"]) for i in itens if e_funcao(i["conta"])}
    assert detectadas  # a fixture tem funções
    for codigo, nome in detectadas:
        assert FUNCOES_SICONFI.get(codigo) == nome

    # (c) ausente vs. retida: nenhuma linha tem marca de sigilo; valores numéricos (não nulos) →
    # conjunto válido = {valor, sem_cobertura}; função ausente é linha que NÃO existe (não um flag).
    for i in itens:
        assert not any("sigil" in k or "supr" in k for k in i)
        assert isinstance(i["valor"], (int, float))
