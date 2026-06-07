"""Unidade do contrato do Pulso Produtivo (TRAB-01): nível + momento + janela. Puro, sem DB.

Os números espelham o seed (SP/Campinas) para que unidade e integração concordem.
"""

from __future__ import annotations

import pytest

from app.produtos.pulso_produtivo import (
    MesSaldo,
    calcular,
    classificar_pulso,
    classificar_tendencia,
)

# Mesmas batidas do seed (Onda 1).
SP = [MesSaldo("2026-02", 8200), MesSaldo("2026-03", -15400), MesSaldo("2026-04", -9100)]
CPS = [MesSaldo("2026-02", 1200), MesSaldo("2026-03", -800), MesSaldo("2026-04", -300)]


def test_pulso_pelo_sinal_da_batida() -> None:
    assert classificar_pulso(1) == "aquecido"
    assert classificar_pulso(-1) == "esfriando"
    assert classificar_pulso(0) == "estavel"  # limiar


def test_tendencia_compara_com_o_mes_anterior() -> None:
    assert classificar_tendencia(10, 5) == "melhorando"
    assert classificar_tendencia(5, 10) == "piorando"
    assert classificar_tendencia(7, 7) == "estavel"
    # o caso honesto: ainda negativo, mas MENOS negativo que antes = desacelerando (melhorando).
    assert classificar_tendencia(-9100, -15400) == "melhorando"


def test_calcular_sp_esfriando_mas_melhorando() -> None:
    p = calcular("3550308", "São Paulo", "SP", SP)
    assert p.periodo == "2026-04"
    assert p.saldo_mes == -9100  # batida atual
    assert p.saldo_acumulado == 8200 - 15400 - 9100  # -16300, contexto
    assert p.pulso == "esfriando"  # último mês negativo
    assert p.tendencia == "melhorando"  # -9100 > -15400 (desacelerou a perda)
    assert p.meses_positivos == 1
    assert p.meses_negativos == 2
    assert [m.saldo for m in p.meses] == [8200, -15400, -9100]  # janela inteira, sem esconder


def test_calcular_campinas_acumulado_positivo_nao_mascara_o_esfriamento() -> None:
    # A armadilha sazonal: acumulado +100 (puxado por janeiro), mas a batida atual esfria.
    p = calcular("3509502", "Campinas", "SP", CPS)
    assert p.saldo_acumulado == 100  # positivo no agregado
    assert p.pulso == "esfriando"  # ...mas a batida atual é negativa — a verdade aparece
    assert p.tendencia == "melhorando"
    assert (p.meses_positivos, p.meses_negativos) == (1, 2)


def test_um_unico_mes_sem_tendencia() -> None:
    p = calcular("3550308", "São Paulo", "SP", [MesSaldo("2026-04", 500)])
    assert p.saldo_mes == 500
    assert p.saldo_acumulado == 500
    assert p.pulso == "aquecido"
    assert p.tendencia is None  # sem mês anterior, não se inventa momento
    assert p.meses_negativos == 0


def test_mes_zero_e_neutro_na_contagem() -> None:
    p = calcular("1", "Brasil", None, [MesSaldo("2026-03", 0), MesSaldo("2026-04", 0)])
    assert p.pulso == "estavel"
    assert p.tendencia == "estavel"
    assert (p.meses_positivos, p.meses_negativos) == (0, 0)  # zero não é positivo nem negativo


def test_calcular_sem_meses_falha_fechado() -> None:
    with pytest.raises(ValueError, match="ao menos um mês"):
        calcular("3550308", "São Paulo", "SP", [])
