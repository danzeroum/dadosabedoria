"""Testes unitários do produto Caçador de Arboviroses (SAUDE-02)."""

from __future__ import annotations

from app.produtos.cacador_arboviroses import (
    _LIMIAR_CRITICO,
    _LIMIAR_ELEVADO,
    _LIMIAR_MODERADO,
    calcular,
    classificar_nivel,
)

# ----------------------------------------------------------------- classificar_nivel


def test_classificar_nivel_none_retorna_sem_dado() -> None:
    assert classificar_nivel(None) == "sem_dado"


def test_classificar_nivel_critico() -> None:
    assert classificar_nivel(_LIMIAR_CRITICO) == "crítico"
    assert classificar_nivel(_LIMIAR_CRITICO + 100) == "crítico"
    assert classificar_nivel(1000.0) == "crítico"


def test_classificar_nivel_elevado() -> None:
    assert classificar_nivel(_LIMIAR_ELEVADO) == "elevado"
    assert classificar_nivel(_LIMIAR_CRITICO - 0.01) == "elevado"
    assert classificar_nivel(150.0) == "elevado"


def test_classificar_nivel_moderado() -> None:
    assert classificar_nivel(_LIMIAR_MODERADO) == "moderado"
    assert classificar_nivel(_LIMIAR_ELEVADO - 0.01) == "moderado"
    assert classificar_nivel(50.0) == "moderado"


def test_classificar_nivel_baixo() -> None:
    assert classificar_nivel(0.0) == "baixo"
    assert classificar_nivel(_LIMIAR_MODERADO - 0.01) == "baixo"
    assert classificar_nivel(10.0) == "baixo"


# ----------------------------------------------------------------- calcular


def test_calcular_com_populacao_e_casos() -> None:
    ca = calcular(
        "3550308",
        "São Paulo",
        "SP",
        11_451_245,
        ano=2023,
        casos_confirmados=8000,
    )
    assert ca.codigo_ibge == "3550308"
    assert ca.nome == "São Paulo"
    assert ca.uf == "SP"
    assert ca.populacao == 11_451_245
    assert ca.ano == 2023
    assert ca.casos_confirmados == 8000
    # incidência: 8000/11451245*100000 ≈ 69.87
    assert ca.incidencia_100k is not None
    assert abs(ca.incidencia_100k - 69.87) < 0.5
    assert ca.nivel == "elevado"


def test_calcular_sem_casos_retorna_sem_dado() -> None:
    ca = calcular(
        "3550308",
        "São Paulo",
        "SP",
        11_451_245,
        ano=2023,
        casos_confirmados=None,
    )
    assert ca.casos_confirmados is None
    assert ca.incidencia_100k is None
    assert ca.nivel == "sem_dado"


def test_calcular_sem_populacao_sem_incidencia() -> None:
    ca = calcular(
        "9999999",
        "Municipio Sem Pop",
        "XX",
        None,
        ano=2023,
        casos_confirmados=100,
    )
    assert ca.casos_confirmados == 100
    assert ca.incidencia_100k is None
    assert ca.nivel == "sem_dado"


def test_calcular_populacao_zero_sem_incidencia() -> None:
    ca = calcular(
        "9999999",
        "Municipio Zero",
        "XX",
        0,
        ano=2023,
        casos_confirmados=50,
    )
    assert ca.incidencia_100k is None
    assert ca.nivel == "sem_dado"


def test_calcular_nivel_critico() -> None:
    """300+ casos/100k → crítico."""
    # 3000 casos em 1_000_000 hab → 300/100k = crítico
    ca = calcular("1234567", "Município", "XX", 1_000_000, ano=2023, casos_confirmados=3000)
    assert ca.nivel == "crítico"
    assert ca.incidencia_100k is not None
    assert ca.incidencia_100k >= 300.0


def test_calcular_nivel_baixo() -> None:
    """< 20/100k → baixo."""
    # 100 casos em 1_000_000 hab → 10/100k = baixo
    ca = calcular("1234567", "Município", "XX", 1_000_000, ano=2023, casos_confirmados=100)
    assert ca.nivel == "baixo"


def test_calcular_incidencia_arredondada_dois_decimais() -> None:
    ca = calcular("3304557", "Rio de Janeiro", "RJ", 6_211_223, ano=2023, casos_confirmados=10)
    assert ca.incidencia_100k is not None
    # Deve ter no máximo 2 casas decimais
    partes = str(ca.incidencia_100k).split(".")
    assert len(partes) == 1 or len(partes[1]) <= 2


def test_calcular_sem_uf() -> None:
    ca = calcular("9999999", "Município", None, 100_000, ano=2023, casos_confirmados=10)
    assert ca.uf is None


def test_calcular_sem_ano() -> None:
    ca = calcular("3550308", "São Paulo", "SP", 11_451_245, ano=None, casos_confirmados=100)
    assert ca.ano is None
