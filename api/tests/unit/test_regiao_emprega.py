"""Testes unitários da Região Emprega (TRAB-04): classificação e cálculo puro."""

from __future__ import annotations

import pytest

from app.produtos.regiao_emprega import (
    MunicipioEmprego,
    NivelRegiao,
    RegiaoEmprega,
    calcular,
    classificar_nivel_regiao,
)

# ----------------------------------------------------------------- classificar_nivel_regiao


@pytest.mark.parametrize(
    "saldo_total, n_com_dado, esperado",
    [
        (0, 0, "sem_dado"),
        (100, 0, "sem_dado"),  # n_com_dado=0 → sem_dado mesmo com saldo
        (1, 1, "criando"),
        (9400, 2, "criando"),
        (0, 2, "estavel"),
        (-1, 1, "reduzindo"),
        (-9400, 2, "reduzindo"),
    ],
)
def test_classificar_nivel_regiao(saldo_total: int, n_com_dado: int, esperado: NivelRegiao) -> None:
    assert classificar_nivel_regiao(saldo_total, n_com_dado) == esperado


# ----------------------------------------------------------------- calcular


def _sp_municipios() -> list[tuple[str, str, int | None, int | None]]:
    """SP (2026-04, seed): SP=-9100, Campinas=-300."""
    return [
        ("3550308", "São Paulo", 11_451_245, -9100),
        ("3509502", "Campinas", 1_213_792, -300),
    ]


def test_calcular_saldo_total_e_contagens() -> None:
    reg = calcular(
        "35",
        "São Paulo",
        "SP",
        periodo="2026-04",
        municipios_raw=_sp_municipios(),
    )
    assert isinstance(reg, RegiaoEmprega)
    assert reg.saldo_total == -9400
    assert reg.municipios_criando == 0
    assert reg.municipios_estaveis == 0
    assert reg.municipios_reduzindo == 2
    assert reg.municipios_sem_dado == 0
    assert reg.municipios_total == 2
    assert reg.nivel == "reduzindo"
    assert reg.periodo == "2026-04"
    assert reg.uf == "SP"


def test_calcular_lista_municipios() -> None:
    reg = calcular("35", "São Paulo", "SP", periodo="2026-04", municipios_raw=_sp_municipios())
    assert len(reg.municipios) == 2
    sp = next(m for m in reg.municipios if m.codigo_ibge == "3550308")
    assert sp.saldo == -9100
    assert sp.nivel == "reduzindo"
    assert sp.per_1000 is not None
    assert abs(sp.per_1000 - (-9100 / 11_451_245 * 1000)) < 0.01


def test_calcular_per_1000_sem_populacao() -> None:
    """Município sem população: per_1000=None, nível derivado do saldo absoluto."""
    raw = [("3550308", "SP", None, -100)]
    reg = calcular("35", "São Paulo", "SP", periodo="2026-04", municipios_raw=raw)
    m = reg.municipios[0]
    assert m.per_1000 is None
    assert m.nivel == "reduzindo"


def test_calcular_municipio_sem_dado() -> None:
    raw = [
        ("3550308", "São Paulo", 11_451_245, -9100),
        ("3509502", "Campinas", 1_213_792, None),
    ]
    reg = calcular("35", "São Paulo", "SP", periodo="2026-04", municipios_raw=raw)
    assert reg.municipios_sem_dado == 1
    assert reg.municipios_total == 2
    campinas = next(m for m in reg.municipios if m.codigo_ibge == "3509502")
    assert campinas.saldo is None
    assert campinas.nivel == "sem_dado"


def test_calcular_todos_sem_dado() -> None:
    raw = [("3550308", "SP", 11_451_245, None)]
    reg = calcular("35", "São Paulo", "SP", periodo=None, municipios_raw=raw)
    assert reg.nivel == "sem_dado"
    assert reg.saldo_total == 0
    assert reg.municipios_sem_dado == 1


def test_calcular_mix_criando_reduzindo() -> None:
    raw = [
        ("AAA", "Cidade A", 100_000, 50),
        ("BBB", "Cidade B", 200_000, -10),
        ("CCC", "Cidade C", 50_000, 0),
    ]
    reg = calcular("35", "SP", "SP", periodo="2026-04", municipios_raw=raw)
    assert reg.municipios_criando == 1
    assert reg.municipios_estaveis == 1
    assert reg.municipios_reduzindo == 1
    assert reg.saldo_total == 40
    assert reg.nivel == "criando"


def test_calcular_municipio_estavel() -> None:
    raw = [("3550308", "SP", 11_451_245, 0)]
    reg = calcular("35", "São Paulo", "SP", periodo="2026-04", municipios_raw=raw)
    assert reg.municipios_estaveis == 1
    assert reg.nivel == "estavel"
    m = reg.municipios[0]
    assert m.nivel == "estavel"


def test_calcular_lista_vazia() -> None:
    reg = calcular("35", "São Paulo", "SP", periodo=None, municipios_raw=[])
    assert reg.nivel == "sem_dado"
    assert reg.municipios_total == 0
    assert reg.saldo_total == 0


def test_calcular_municipio_emprego_fields() -> None:
    raw = [("3550308", "São Paulo", 11_451_245, -9100)]
    reg = calcular("35", "São Paulo", "SP", periodo="2026-04", municipios_raw=raw)
    m = reg.municipios[0]
    assert isinstance(m, MunicipioEmprego)
    assert m.codigo_ibge == "3550308"
    assert m.nome == "São Paulo"
    assert m.populacao == 11_451_245
    assert m.saldo == -9100
