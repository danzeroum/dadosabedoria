"""Testes unitários de água_viva.py — lógica pura, sem banco."""

from app.produtos.agua_viva import calcular, classificar_nivel


def test_nivel_adequado():
    assert classificar_nivel(95.0) == "adequado"
    assert classificar_nivel(90.0) == "adequado"


def test_nivel_atencao():
    assert classificar_nivel(80.0) == "atencao"
    assert classificar_nivel(70.0) == "atencao"


def test_nivel_alerta():
    assert classificar_nivel(65.0) == "alerta"
    assert classificar_nivel(0.0) == "alerta"


def test_nivel_sem_dado():
    assert classificar_nivel(None) == "sem_dado"


def test_calcular_completo():
    av = calcular("3550308", "São Paulo", "SP", periodo="2022", agua_pct=99.8, esgoto_pct=87.5)
    assert av.nivel_agua == "adequado"
    assert av.nivel_esgoto == "atencao"
    assert av.agua_pct == 99.8
    assert av.esgoto_pct == 87.5


def test_calcular_sem_esgoto():
    av = calcular("1501402", "Belém", "PA", periodo="2022", agua_pct=72.9, esgoto_pct=None)
    assert av.nivel_agua == "atencao"
    assert av.nivel_esgoto == "sem_dado"
    assert av.esgoto_pct is None


def test_calcular_alerta():
    av = calcular("1501402", "Belém", "PA", periodo="2022", agua_pct=65.0, esgoto_pct=20.0)
    assert av.nivel_agua == "alerta"
    assert av.nivel_esgoto == "alerta"
