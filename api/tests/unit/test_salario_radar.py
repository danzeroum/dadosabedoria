"""Testes unitários do Salário Radar (TRAB-02): classificação e cálculo puro."""

from __future__ import annotations

import pytest

from app.ingestao.adaptadores.caged import AdaptadorCaged
from app.produtos.salario_radar import (
    _SALARIO_ALTO,
    _SALARIO_MEDIO,
    NivelSalario,
    SalarioRadar,
    calcular,
    classificar_nivel_salario,
)
from tests.fixtures.caged import AMOSTRA_UNIT, FetcherFake

# ----------------------------------------------------------------- classificar_nivel_salario


@pytest.mark.parametrize(
    "salario, esperado",
    [
        (None, "sem_dado"),
        (0.0, "baixo"),
        (1_518.0, "baixo"),
        (_SALARIO_MEDIO - 0.01, "baixo"),
        (_SALARIO_MEDIO, "medio"),
        (_SALARIO_MEDIO + 1.0, "medio"),
        (_SALARIO_ALTO - 0.01, "medio"),
        (_SALARIO_ALTO, "alto"),
        (_SALARIO_ALTO + 1.0, "alto"),
        (10_000.0, "alto"),
    ],
)
def test_classificar_nivel_salario(salario: float | None, esperado: NivelSalario) -> None:
    assert classificar_nivel_salario(salario) == esperado


# ----------------------------------------------------------------- calcular


def test_calcular_retorna_medio() -> None:
    s = calcular("3550308", "São Paulo", "SP", periodo="2026-04", salario_medio=2450.0)
    assert isinstance(s, SalarioRadar)
    assert s.nivel == "medio"
    assert s.salario_medio == 2450.0
    assert s.periodo == "2026-04"


def test_calcular_retorna_alto() -> None:
    s = calcular("3509502", "Campinas", "SP", periodo="2026-04", salario_medio=5200.0)
    assert s.nivel == "alto"
    assert s.salario_medio == 5200.0


def test_calcular_retorna_baixo() -> None:
    s = calcular("3509502", "Campinas", "SP", periodo="2026-03", salario_medio=1700.0)
    assert s.nivel == "baixo"


def test_calcular_sem_dado() -> None:
    s = calcular("3509502", "Campinas", "SP", periodo=None, salario_medio=None)
    assert s.nivel == "sem_dado"
    assert s.salario_medio is None
    assert s.periodo is None


def test_calcular_arredonda_dois_decimais() -> None:
    s = calcular("3550308", "São Paulo", "SP", periodo="2026-04", salario_medio=2333.3333)
    assert s.salario_medio == 2333.33


def test_calcular_uf_none() -> None:
    s = calcular("3550308", "São Paulo", None, periodo="2026-04", salario_medio=2450.0)
    assert s.uf is None


# ----------------------------------------------------------------- adaptador CAGED: agregar_salario_medio  # noqa: E501


def test_agregar_salario_medio_apenas_admissoes() -> None:
    """Só admissões (saldo_mov==1) entram na média; desligamentos são ignorados."""
    adaptador = AdaptadorCaged(FetcherFake(AMOSTRA_UNIT))
    df_prata = adaptador.transformar_prata(adaptador.parse(AMOSTRA_UNIT))
    df_sal = adaptador.agregar_salario_medio(df_prata)
    # municipio 355030: admissões c/ salários 2000, 1800, 2200 → média = 2000
    row_355030 = df_sal.filter(df_sal["municipio"] == "355030").row(0, named=True)
    assert abs(row_355030["salario_medio"] - 2000.0) < 0.01


def test_agregar_salario_medio_municipio_so_admissao() -> None:
    """Município com apenas 1 admissão → média = essa admissão."""
    adaptador = AdaptadorCaged(FetcherFake(AMOSTRA_UNIT))
    df_prata = adaptador.transformar_prata(adaptador.parse(AMOSTRA_UNIT))
    df_sal = adaptador.agregar_salario_medio(df_prata)
    # municipio 350950: só 1 admissão com salário 1700
    row_350950 = df_sal.filter(df_sal["municipio"] == "350950").row(0, named=True)
    assert abs(row_350950["salario_medio"] - 1700.0) < 0.01


def test_agregar_salario_medio_sem_admissoes_ausente() -> None:
    """Município sem nenhuma admissão não aparece no resultado."""
    from tests.fixtures.caged import _csv  # noqa: PLC0415

    # Fixture com município 111111 tendo só desligamentos
    fixture = _csv([("202604", "111111", -1, "2000,00")])
    adaptador = AdaptadorCaged(FetcherFake(fixture))
    df_prata = adaptador.transformar_prata(adaptador.parse(fixture))
    df_sal = adaptador.agregar_salario_medio(df_prata)
    assert len(df_sal) == 0
