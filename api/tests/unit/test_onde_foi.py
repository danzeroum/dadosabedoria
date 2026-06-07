"""Unidade do contrato do OndeFoi (ADR-0026): denominador base-única + banda + exe_estado. Puro."""

from __future__ import annotations

from app.produtos.onde_foi import ExecucaoMunicipio, banda, calcular
from tests.fixtures.onde_foi import DEMO


def _calc(cod: str) -> ExecucaoMunicipio:
    c, nome, uf, total, fbs = next(d for d in DEMO if d[0] == cod)
    return calcular(c, nome, uf, total, fbs)


def test_banda_limiares() -> None:
    assert banda(95) == "alta"
    assert banda(80) == "alta"  # limiar
    assert banda(79) == "parcial"
    assert banda(55) == "parcial"  # limiar
    assert banda(54) == "baixa"
    assert banda(0) == "baixa"
    assert banda(None) == "indef"


def test_denominador_base_unica_sp() -> None:
    # SP: todas as funções divulgadas → base = soma de todas; % sobre essa base.
    sp = _calc("3550308")
    assert sp.recebido_base == 54200
    assert sp.executado == 47800
    assert sp.pct == 88  # round(47800/54200*100)
    assert sp.recebido_fora_base == 78900 - 54200  # 24700: não detalhado por função, explícito
    assert sp.banda == "alta"


def test_sem_cobertura_fica_fora_da_base_e_explicita_rio() -> None:
    # Rio: Saneamento + Cultura sem cobertura → fora do numerador E do denominador.
    rio = _calc("3304557")
    assert rio.recebido_base == 26000  # só as 4 funções divulgadas (9800+8600+2400+5200)
    assert rio.executado == 19780  # 8120+7310+1490+2860
    assert rio.pct == 76  # round(19780/26000*100)
    # parcela fora = total − base (sem cobertura + não detalhado), NUNCA silenciosamente fora do %.
    assert rio.recebido_fora_base == 41200 - 26000  # 15200
    assert rio.banda == "parcial"
    sem = [f for f in rio.funcoes if f.exe_estado == "sem_cobertura"]
    assert {f.funcao for f in sem} == {"Saneamento", "Cultura"}
    assert all(f.exe is None and f.pct is None for f in sem)


def test_recebido_total_nunca_e_o_denominador() -> None:
    # A armadilha que o ADR-0026 trava: o % usa recebido_base, não o total exibido.
    rio = _calc("3304557")
    assert rio.pct == round(rio.executado / rio.recebido_base * 100)
    assert rio.recebido_base < rio.recebido_total  # base é subconjunto do total


def test_baixa_execucao_merece_a_pergunta() -> None:
    rn = _calc("3154606")  # Ribeirão das Neves — executor baixo
    assert rn.pct == 50  # round(730/1470*100)
    assert rn.banda == "baixa"


def test_onde_foi_sem_cadeado_de_privacidade() -> None:
    # ADR-0026 refino: orçamento por função é público sem PII → válido = {valor, sem_cobertura}.
    estados = {f.exe_estado for c, n, u, t, fbs in DEMO for f in calcular(c, n, u, t, fbs).funcoes}
    assert estados == {"valor", "sem_cobertura"}
    assert "suprimido" not in estados  # nenhum cadeado fingido em dado público
