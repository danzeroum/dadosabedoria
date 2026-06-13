"""Testes unitários do produto Sentinela Materna (SAUDE-03)."""

from __future__ import annotations

from app.produtos.sentinela_materna import (
    NOTA_HONESTA,
    SentinelaMaterna,
    calcular,
    classificar_nivel,
)

# ------------------------------------------------------------------ classificar_nivel


def test_classificar_nivel_critico() -> None:
    assert classificar_nivel(30.0) == "crítico"
    assert classificar_nivel(45.0) == "crítico"
    assert classificar_nivel(100.0) == "crítico"


def test_classificar_nivel_elevado() -> None:
    assert classificar_nivel(20.0) == "elevado"
    assert classificar_nivel(25.5) == "elevado"
    assert classificar_nivel(29.99) == "elevado"


def test_classificar_nivel_moderado() -> None:
    assert classificar_nivel(10.0) == "moderado"
    assert classificar_nivel(15.0) == "moderado"
    assert classificar_nivel(19.99) == "moderado"


def test_classificar_nivel_baixo() -> None:
    assert classificar_nivel(0.0) == "baixo"
    assert classificar_nivel(5.0) == "baixo"
    assert classificar_nivel(9.99) == "baixo"


def test_classificar_nivel_sem_dado() -> None:
    assert classificar_nivel(None) == "sem_dado"


# ------------------------------------------------------------------ calcular


def test_calcular_com_dados() -> None:
    sm = calcular(
        "3509502",
        "Campinas",
        "SP",
        1213792,
        ano=2023,
        n_gestantes=20,
        gestante_baixo_peso_pct=15.0,
    )
    assert isinstance(sm, SentinelaMaterna)
    assert sm.codigo_ibge == "3509502"
    assert sm.nome == "Campinas"
    assert sm.uf == "SP"
    assert sm.populacao == 1213792
    assert sm.ano == 2023
    assert sm.n_gestantes == 20
    assert sm.gestante_baixo_peso_pct == 15.0
    assert sm.nivel == "moderado"


def test_calcular_sem_dados() -> None:
    sm = calcular(
        "9999999",
        "Município Fictício",
        None,
        None,
        ano=None,
        n_gestantes=None,
        gestante_baixo_peso_pct=None,
    )
    assert sm.nivel == "sem_dado"
    assert sm.gestante_baixo_peso_pct is None
    assert sm.n_gestantes is None


def test_calcular_critico() -> None:
    sm = calcular(
        "3304557",
        "Rio de Janeiro",
        "RJ",
        None,
        ano=2023,
        n_gestantes=40,
        gestante_baixo_peso_pct=35.0,
    )
    assert sm.nivel == "crítico"


def test_calcular_arredonda_pct() -> None:
    """calcular() deve arredondar para 2 casas decimais."""
    sm = calcular(
        "3550308",
        "São Paulo",
        "SP",
        None,
        ano=2023,
        n_gestantes=30,
        gestante_baixo_peso_pct=3.333333,
    )
    assert sm.gestante_baixo_peso_pct == 3.33


# ------------------------------------------------------------------ NOTA_HONESTA


def test_nota_honesta_presente() -> None:
    assert len(NOTA_HONESTA) > 0
    assert "SISVAN" in NOTA_HONESTA
    assert "gestantes" in NOTA_HONESTA.lower()
    # Dupla-face §17: não identifica gestantes individualmente
    assert "não identifica" in NOTA_HONESTA.lower()
