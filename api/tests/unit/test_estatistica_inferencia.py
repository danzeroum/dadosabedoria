"""Testes unitários para funções estatísticas de analytics inferencial."""

from __future__ import annotations

import pytest

from app.inferencia.estatistica import (
    benjamini_hochberg,
    p_valor_bilateral,
    percentil_rank,
    z_score,
)

# ───────────────────── percentil_rank ─────────────────────


def test_percentil_rank_minimo() -> None:
    distrib = [10.0, 20.0, 30.0, 40.0]
    assert percentil_rank(10.0, distrib) == 0.0  # nenhum valor abaixo


def test_percentil_rank_maximo() -> None:
    distrib = [10.0, 20.0, 30.0, 40.0]
    assert percentil_rank(40.0, distrib) == 75.0  # 3 dos 4 abaixo


def test_percentil_rank_meio() -> None:
    distrib = [10.0, 20.0, 30.0]
    assert percentil_rank(20.0, distrib) == pytest.approx(33.3, abs=0.1)


def test_percentil_rank_lista_vazia() -> None:
    assert percentil_rank(5.0, []) == 0.0


def test_percentil_rank_acima_de_todos() -> None:
    distrib = [1.0, 2.0, 3.0]
    assert percentil_rank(100.0, distrib) == 100.0


# ───────────────────── z_score ─────────────────────


def test_z_score_neutro() -> None:
    assert z_score(10.0, 10.0, 5.0) == pytest.approx(0.0)


def test_z_score_acima() -> None:
    assert z_score(15.0, 10.0, 5.0) == pytest.approx(1.0)


def test_z_score_abaixo() -> None:
    assert z_score(5.0, 10.0, 5.0) == pytest.approx(-1.0)


def test_z_score_desvio_zero_retorna_none() -> None:
    assert z_score(10.0, 10.0, 0.0) is None


def test_z_score_desvio_negativo_retorna_none() -> None:
    assert z_score(10.0, 10.0, -1.0) is None


# ───────────────────── p_valor_bilateral ─────────────────────


def test_p_valor_bilateral_z_zero() -> None:
    # p ≈ 1.0 quando z = 0 (exatamente na média)
    assert p_valor_bilateral(0.0) == pytest.approx(1.0, abs=0.01)


def test_p_valor_bilateral_z_196() -> None:
    # p ≈ 0.05 quando z = 1.96 (limite convencional)
    assert p_valor_bilateral(1.96) == pytest.approx(0.05, abs=0.005)


def test_p_valor_bilateral_z_grande() -> None:
    # p muito pequeno para z grande
    assert p_valor_bilateral(5.0) < 0.0001


# ───────────────────── benjamini_hochberg ─────────────────────


def test_bh_lista_vazia() -> None:
    assert benjamini_hochberg([]) == []


def test_bh_rejeita_significativo() -> None:
    # p-valores: 0.001 (muito pequeno) deve ser rejeitado
    resultado = benjamini_hochberg([0.001, 0.5, 0.9])
    assert resultado[0] is True
    assert resultado[1] is False
    assert resultado[2] is False


def test_bh_nenhum_rejeitado() -> None:
    # todos p-valores grandes → nenhum rejeitado
    resultado = benjamini_hochberg([0.4, 0.6, 0.8], alfa=0.05)
    assert all(r is False for r in resultado)


def test_bh_todos_rejeitados() -> None:
    # p-valores muito pequenos → todos rejeitados
    p = [0.001, 0.002, 0.003]
    resultado = benjamini_hochberg(p, alfa=0.05)
    assert all(r is True for r in resultado)


def test_bh_comprimento_preservado() -> None:
    p = [0.01, 0.04, 0.10, 0.20]
    resultado = benjamini_hochberg(p, alfa=0.05)
    assert len(resultado) == 4


def test_bh_preserva_ordem_original() -> None:
    # O segundo elemento (0.001) deve ser rejeitado, não o primeiro (0.5)
    resultado = benjamini_hochberg([0.5, 0.001])
    assert resultado[0] is False
    assert resultado[1] is True


def test_bh_limiar_exato() -> None:
    # BH threshold para k=1 de n=2, alfa=0.05: p <= 1*0.05/2 = 0.025
    assert benjamini_hochberg([0.025, 0.5])[0] is True
    assert benjamini_hochberg([0.026, 0.5])[0] is False
