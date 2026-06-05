"""Unidade dos guardrails da IA (sanitização + identificação de indicador) — puro."""

from __future__ import annotations

from app.ia.guardrails import identificar_indicador, sanitizar

CATALOGO = [
    ("trabalho.emprego.saldo_caged", "Saldo de empregos formais"),
    ("credito.operacoes.saldo_total", "Saldo de operações de crédito"),
]


def test_sanitizar_remove_controle_e_corta() -> None:
    s = sanitizar("a\x00b\x07c")
    assert "\x00" not in s and "\x07" not in s
    assert sanitizar("x" * 5000) == "x" * 1000


def test_identifica_por_nome() -> None:
    assert (
        identificar_indicador("qual o saldo de empregos formais em SP?", CATALOGO)
        == "trabalho.emprego.saldo_caged"
    )


def test_identifica_por_codigo() -> None:
    assert (
        identificar_indicador("me fale do trabalho.emprego.saldo_caged", CATALOGO)
        == "trabalho.emprego.saldo_caged"
    )


def test_sem_match_retorna_none() -> None:
    assert identificar_indicador("qual a cor do céu hoje?", CATALOGO) is None
