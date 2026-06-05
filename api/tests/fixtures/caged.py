"""Amostras do layout CAGEDMOV (`;`-delimitado) e um fetcher fake (sem rede)."""

from __future__ import annotations

from app.ingestao.adaptadores.base import Janela

_HEADER = "competênciamov;município;saldomovimentação;salário"


def _csv(linhas: list[tuple]) -> bytes:
    corpo = [_HEADER] + [";".join(str(c) for c in linha) for linha in linhas]
    return ("\n".join(corpo) + "\n").encode("utf-8")


# Agregação esperada: 355030 → +2, 350950 → −1, 999999 → +1.
AMOSTRA_UNIT = _csv(
    [
        ("202607", "355030", 1, "2000,00"),
        ("202607", "355030", 1, "1800,00"),
        ("202607", "355030", 1, "2200,00"),
        ("202607", "355030", -1, "1500,00"),
        ("202607", "350950", 1, "1700,00"),
        ("202607", "350950", -1, "1600,00"),
        ("202607", "350950", -1, "1900,00"),
        ("202607", "999999", 1, "1000,00"),
    ]
)

# Pipeline: Rio (330455) → +3; 999999 não está no cadastro → ignorado.
AMOSTRA_RIO = _csv(
    [
        ("202607", "330455", 1, "2000,00"),
        ("202607", "330455", 1, "2100,00"),
        ("202607", "330455", 1, "2200,00"),
        ("202607", "330455", 1, "2300,00"),
        ("202607", "330455", -1, "1500,00"),
        ("202607", "999999", 1, "1000,00"),
    ]
)


class FetcherFake:
    """Fetcher injetável que devolve bytes de fixture (sem rede)."""

    def __init__(self, dados: bytes, url: str = "fixture://caged") -> None:
        self._dados = dados
        self._url = url

    def baixar(self, janela: Janela) -> tuple[bytes, str]:
        return self._dados, self._url
