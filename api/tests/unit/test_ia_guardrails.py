"""Unidade dos guardrails da IA (sanitização + identificação de indicador + ancoragem) — puro."""

from __future__ import annotations

from app.ia.guardrails import (
    identificar_indicador,
    numeros,
    sanitizar,
    validar_numeros_ancorados,
)

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


def test_identifica_por_termo_do_codigo_com_flexao() -> None:
    # "emprego" (singular, fora do nome "Saldo de empregos formais") casa pelo léxico do CÓDIGO
    # (trabalho.emprego.saldo_caged) + prefixo — antes a IA abstinha de uma pergunta com dado.
    assert (
        identificar_indicador("como está o emprego em São Paulo?", CATALOGO)
        == "trabalho.emprego.saldo_caged"
    )


def test_identifica_credito_por_termo_curto() -> None:
    assert (
        identificar_indicador("qual o crédito disponível na cidade?", CATALOGO)
        == "credito.operacoes.saldo_total"
    )


def test_palavra_generica_do_codigo_nao_casa_sozinha() -> None:
    # "total" existe só no código (credito...saldo_total), não no nome → score 1 < limiar:
    # não basta uma palavra genérica para fixar o indicador (evita falso-positivo).
    assert identificar_indicador("qual o total de impostos?", CATALOGO) is None


def test_numeros_normaliza_separadores() -> None:
    # ``8.200`` e ``8200`` contam como o mesmo número; só conta >= 2 dígitos.
    assert numeros("foi 8.200 em 2026-02 (conf 4/5)") == {"8200", "2026", "02"}


def test_validar_ancoragem_aprova_quando_subconjunto() -> None:
    permitidos = numeros("DADOS: 2026-02: 8200")
    assert validar_numeros_ancorados("O valor foi 8.200 em 2026-02.", permitidos) is True
    assert validar_numeros_ancorados("Sem números relevantes aqui.", permitidos) is True


def test_validar_ancoragem_reprova_numero_inventado() -> None:
    permitidos = numeros("DADOS: 2026-02: 8200")
    assert validar_numeros_ancorados("Na verdade o valor foi 9999.", permitidos) is False
