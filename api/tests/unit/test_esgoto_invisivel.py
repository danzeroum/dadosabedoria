"""Testes unitários para EsgotoInvisível (SANE-03) — lógica pura."""

from app.produtos.esgoto_invisivel import calcular, calcular_gap, classificar_nivel


def test_classificar_nivel_adequado() -> None:
    assert classificar_nivel(70.0) == "adequado"
    assert classificar_nivel(95.0) == "adequado"
    assert classificar_nivel(100.0) == "adequado"


def test_classificar_nivel_atencao() -> None:
    assert classificar_nivel(40.0) == "atencao"
    assert classificar_nivel(55.0) == "atencao"
    assert classificar_nivel(69.9) == "atencao"


def test_classificar_nivel_critico() -> None:
    assert classificar_nivel(0.0) == "critico"
    assert classificar_nivel(20.0) == "critico"
    assert classificar_nivel(39.9) == "critico"


def test_classificar_nivel_sem_dado() -> None:
    assert classificar_nivel(None) == "sem_dado"


def test_calcular_gap_normal() -> None:
    assert calcular_gap(85.0, 40.0) == 45.0


def test_calcular_gap_sem_diferenca() -> None:
    assert calcular_gap(70.0, 70.0) == 0.0


def test_calcular_gap_esgoto_maior_agua() -> None:
    # Gap não pode ser negativo
    assert calcular_gap(60.0, 80.0) == 0.0


def test_calcular_gap_sem_esgoto() -> None:
    assert calcular_gap(85.0, None) is None


def test_calcular_gap_sem_agua() -> None:
    # Sem água: gap = 0 (esgoto sem água é incomum)
    assert calcular_gap(None, 40.0) == 0.0


def test_calcular_produto_completo() -> None:
    ei = calcular("3550308", "São Paulo", "SP", periodo="2022", agua_pct=97.2, esgoto_pct=86.0)
    assert ei.codigo_ibge == "3550308"
    assert ei.nivel_gap == "adequado"
    assert ei.gap_pct == pytest.approx(11.2)


def test_calcular_paradoxo_hidrico() -> None:
    # Município tem água mas esgoto muito baixo — "esgoto invisível" típico
    ei = calcular("1234567", "Exemplo", "PA", periodo="2022", agua_pct=75.0, esgoto_pct=8.0)
    assert ei.nivel_gap == "critico"
    assert ei.gap_pct == pytest.approx(67.0)


def test_calcular_sem_esgoto() -> None:
    ei = calcular("1234567", "SemDado", "AM", periodo=None, agua_pct=None, esgoto_pct=None)
    assert ei.nivel_gap == "sem_dado"
    assert ei.gap_pct is None


import pytest  # noqa: E402
