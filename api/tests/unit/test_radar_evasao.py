"""Unidade do Radar de Evasão Escolar (EDU-02). Puro, sem rede/DB."""

from __future__ import annotations

import pytest

from app.produtos.radar_evasao import RadarEvasao, calcular, classificar_nivel_evasao

# ---------- classificar_nivel_evasao ----------


def test_classificar_adequada() -> None:
    assert classificar_nivel_evasao(90.0) == "adequada"
    assert classificar_nivel_evasao(100.0) == "adequada"
    assert classificar_nivel_evasao(120.0) == "adequada"


def test_classificar_atencao() -> None:
    assert classificar_nivel_evasao(75.0) == "atencao"
    assert classificar_nivel_evasao(89.9) == "atencao"


def test_classificar_alerta() -> None:
    assert classificar_nivel_evasao(0.0) == "alerta"
    assert classificar_nivel_evasao(74.9) == "alerta"


def test_classificar_sem_dado() -> None:
    assert classificar_nivel_evasao(None) == "sem_dado"


# ---------- calcular ----------


def _radar(
    *,
    populacao: int | None = 100_000,
    matriculas: int | None = 12_000,
    periodo: str | None = "2023",
) -> RadarEvasao:
    return calcular(
        "3550308",
        "São Paulo",
        "SP",
        populacao,
        periodo=periodo,
        matriculas=matriculas,
    )


def test_calcular_taxa_cobertura_plena() -> None:
    # 14.000 matrículas / (100.000 × 0,14) = 100 % → adequada
    o = _radar(populacao=100_000, matriculas=14_000)
    assert o.taxa_cobertura == pytest.approx(100.0)
    assert o.nivel == "adequada"


def test_calcular_taxa_cobertura_parcial() -> None:
    # 11.200 / 14.000 = 80 % → atencao
    o = _radar(populacao=100_000, matriculas=11_200)
    assert o.taxa_cobertura == pytest.approx(80.0)
    assert o.nivel == "atencao"


def test_calcular_taxa_cobertura_baixa() -> None:
    # 7.000 / 14.000 = 50 % → alerta
    o = _radar(populacao=100_000, matriculas=7_000)
    assert o.taxa_cobertura == pytest.approx(50.0)
    assert o.nivel == "alerta"


def test_calcular_acima_de_100_pct_e_adequada() -> None:
    # Município polo — mais matrículas que o estimado localmente
    o = _radar(populacao=100_000, matriculas=16_000)
    assert o.taxa_cobertura is not None
    assert o.taxa_cobertura > 100.0
    assert o.nivel == "adequada"


def test_calcular_matriculas_por_mil() -> None:
    o = _radar(populacao=100_000, matriculas=12_000)
    # 12.000 / 100.000 × 1.000 = 120,0
    assert o.matriculas_por_mil == pytest.approx(120.0)


def test_calcular_populacao_escolar_estimada() -> None:
    o = _radar(populacao=100_000)
    assert o.populacao_escolar_estimada == 14_000  # round(100_000 × 0,14)


def test_calcular_sem_matriculas() -> None:
    o = _radar(matriculas=None)
    assert o.matriculas is None
    assert o.matriculas_por_mil is None
    assert o.taxa_cobertura is None
    assert o.nivel == "sem_dado"


def test_calcular_sem_populacao() -> None:
    o = _radar(populacao=None)
    assert o.populacao_escolar_estimada is None
    assert o.taxa_cobertura is None
    assert o.nivel == "sem_dado"


def test_calcular_sem_periodo() -> None:
    o = _radar(periodo=None)
    assert o.periodo is None
    # taxa é computada independentemente do período
    assert o.taxa_cobertura is not None


def test_calcular_populacao_zero_sem_taxa() -> None:
    o = _radar(populacao=0)
    assert o.taxa_cobertura is None
    assert o.nivel == "sem_dado"


def test_calcular_preserva_campos_territorio() -> None:
    o = calcular("3550308", "São Paulo", "SP", 12_300_000, periodo="2023", matriculas=None)
    assert o.codigo_ibge == "3550308"
    assert o.nome == "São Paulo"
    assert o.uf == "SP"
    assert o.populacao == 12_300_000
