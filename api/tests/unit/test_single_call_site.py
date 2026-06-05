"""Garante que a regra de supressão tem UM único ponto de chamada e que ninguém escreve em
``valor`` por fora do caminho ouro (DRY / invariante 1). Faz "DRY em um lugar" ser verificável.
"""

from __future__ import annotations

from pathlib import Path

_APP = Path(__file__).resolve().parents[2] / "app"


def _arquivos_py() -> list[Path]:
    return list(_APP.rglob("*.py"))


def test_aplicar_so_em_ouro() -> None:
    ofensores = []
    for p in _arquivos_py():
        if p.name == "ouro.py":
            continue
        if ".aplicar(" in p.read_text(encoding="utf-8"):
            ofensores.append(str(p.relative_to(_APP)))
    assert not ofensores, f".aplicar( fora de ouro.py: {ofensores}"


def test_sem_insert_cru_em_valor() -> None:
    for p in _arquivos_py():
        texto = p.read_text(encoding="utf-8").lower()
        assert "insert into valor" not in texto, f"INSERT cru em valor em {p.name}"


def test_escrita_na_tabela_valor_so_em_ouro() -> None:
    """O alias ``t_valor`` (escrita na fato) só pode aparecer em ouro.py."""
    ofensores = []
    for p in _arquivos_py():
        if p.name == "ouro.py":
            continue
        if "t_valor" in p.read_text(encoding="utf-8"):
            ofensores.append(str(p.relative_to(_APP)))
    assert not ofensores, f"escrita na tabela valor fora de ouro.py: {ofensores}"
