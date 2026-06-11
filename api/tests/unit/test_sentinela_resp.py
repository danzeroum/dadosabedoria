"""Unidade do contrato da Sentinela Respiratória (SAUDE-01). Puro, sem DB.

Valores do seed (SP/Campinas): SP tem 3 meses reais (310, 420, 660); Campinas 1 mês suprimido.
"""

from __future__ import annotations

import pytest

from app.produtos.sentinela_resp import (
    MesInternacoes,
    calcular,
    classificar_nivel,
    classificar_tendencia,
)

POP_SP = 11_451_245
# Seed: abril=310, maio=420, junho=660
MESES_SP = [
    MesInternacoes("2026-04", 310, False),
    MesInternacoes("2026-05", 420, False),
    MesInternacoes("2026-06", 660, False),
]
# Seed: Campinas — 1 mês suprimido (n_amostra=3 < 5)
MESES_CPS = [MesInternacoes("2026-04", None, True)]


def test_nivel_elevado() -> None:
    assert classificar_nivel(12.0, False) == "elevado"


def test_nivel_moderado() -> None:
    assert classificar_nivel(5.0, False) == "moderado"


def test_nivel_baixo() -> None:
    assert classificar_nivel(1.0, False) == "baixo"


def test_nivel_suprimido_tem_prioridade() -> None:
    assert classificar_nivel(999.0, True) == "suprimido"  # suprimido sobrepõe o per capita


def test_nivel_sem_dado() -> None:
    assert classificar_nivel(None, False) == "sem_dado"


def test_tendencia_subindo() -> None:
    assert classificar_tendencia(660, 420) == "subindo"


def test_tendencia_caindo() -> None:
    assert classificar_tendencia(300, 420) == "caindo"


def test_tendencia_estavel() -> None:
    assert classificar_tendencia(400, 400) == "estavel"


def test_calcular_sp_moderado_subindo() -> None:
    s = calcular("3550308", "São Paulo", "SP", POP_SP, MESES_SP)
    assert s.periodo == "2026-06"
    assert s.internacoes == 660
    assert s.suprimido is False
    assert s.nivel == "moderado"  # 660/11_451_245 × 100k ≈ 5.8
    assert s.internacoes_por_100k is not None
    assert 5.5 < s.internacoes_por_100k < 6.0
    assert s.tendencia == "subindo"  # 660 > 420
    assert len(s.meses) == 3
    assert s.meses[0].internacoes == 310
    assert s.meses[2].internacoes == 660


def test_calcular_campinas_suprimido() -> None:
    s = calcular("3509502", "Campinas", "SP", 1_213_792, MESES_CPS)
    assert s.periodo == "2026-04"
    assert s.internacoes is None
    assert s.suprimido is True
    assert s.nivel == "suprimido"
    assert s.internacoes_por_100k is None  # suprimido → não calcula per capita
    assert s.tendencia is None  # sem dois meses reais
    assert s.meses[0].suprimido is True


def test_calcular_sem_populacao_nivel_sem_dado() -> None:
    meses = [MesInternacoes("2026-06", 200, False)]
    s = calcular("1", "Teste", None, None, meses)
    assert s.internacoes_por_100k is None  # sem populacao
    assert s.nivel == "sem_dado"  # per capita ausente → sem_dado


def test_calcular_um_mes_sem_tendencia() -> None:
    meses = [MesInternacoes("2026-06", 100, False)]
    s = calcular("1", "Teste", "SP", 100_000, meses)
    assert s.tendencia is None  # só 1 mês real → sem comparação


def test_calcular_vazio_falha_fechado() -> None:
    with pytest.raises(ValueError, match="ao menos um mês"):
        calcular("1", "Teste", None, None, [])


def test_calcular_misto_suprimido_e_real_tendencia_com_reais() -> None:
    meses = [
        MesInternacoes("2026-03", None, True),  # suprimido
        MesInternacoes("2026-04", 300, False),
        MesInternacoes("2026-05", 450, False),
    ]
    s = calcular("1", "Teste", "SP", 500_000, meses)
    assert s.internacoes == 450
    assert s.suprimido is False
    assert s.tendencia == "subindo"  # 450 > 300 (ignora o mês suprimido)
    assert len(s.meses) == 3
    assert s.meses[0].suprimido is True
