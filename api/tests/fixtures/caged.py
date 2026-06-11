"""Amostras do layout CAGEDMOV (`;`-delimitado) e um fetcher fake (sem rede)."""

from __future__ import annotations

from app.ingestao.adaptadores.base import Janela

_HEADER = "competênciamov;município;saldomovimentação;salário"

# Cabeçalho real de 28 colunas — CAGEDMOV 202604 (ADR-0036, forma fiel-à-fonte).
_HEADER_28 = (
    "competênciamov;região;uf;município;seção;subclasse;saldomovimentação;cbo2002ocupação;"
    "categoria;graudeinstrução;idade;horascontratuais;raçacor;sexo;tipoempregador;"
    "tipoestabelecimento;tipomovimentação;tipodedeficiência;indtrabintermitente;indtrabparcial;"
    "salário;tamestabjan;indicadoraprendiz;origemdainformação;competênciadec;"
    "indicadordeforadoprazo;unidadesaláriocódigo;valorsaláriofixo"
)


def _csv(linhas: list[tuple]) -> bytes:
    corpo = [_HEADER] + [";".join(str(c) for c in linha) for linha in linhas]
    return ("\n".join(corpo) + "\n").encode("utf-8")


def _csv28(linhas: list[tuple]) -> bytes:
    """Gera CSV de 28 colunas no layout fiel-à-fonte (sem BOM, utf-8, `;`)."""
    corpo = [_HEADER_28] + [";".join(str(c) for c in linha) for linha in linhas]
    return ("\n".join(corpo) + "\n").encode("utf-8")


# 28 colunas — 3 linhas: 1 admissão SP (355030), 1 desligamento SP, 1 admissão (351905).
# Forma confirmada: utf-8 sem BOM, separador `;`, municipio 6 dígitos, salário BR decimal.
# Esperado após prata+agregação: 355030 → saldo=0, 351905 → saldo=1.
AMOSTRA_FIEL = _csv28(
    [
        # competênciamov;região;uf;município;seção;subclasse;saldomovimentação;cbo2002ocupação;
        # categoria;graudeinstrução;idade;horascontratuais;raçacor;sexo;tipoempregador;
        # tipoestabelecimento;tipomovimentação;tipodedeficiência;indtrabintermitente;
        # indtrabparcial;salário;tamestabjan;indicadoraprendiz;origemdainformação;
        # competênciadec;indicadordeforadoprazo;unidadesaláriocódigo;valorsaláriofixo
        (
            "202604",
            3,
            35,
            "355030",
            "G",
            "471301",
            1,
            "521110",
            101,
            4,
            27,
            "44,00",
            4,
            1,
            0,
            1,
            97,
            0,
            0,
            0,
            "1654,62",
            9,
            0,
            1,
            "202604",
            0,
            5,
            "1654,62",
        ),
        (
            "202604",
            3,
            35,
            "355030",
            "C",
            "251200",
            -1,
            "214905",
            101,
            7,
            35,
            "40,00",
            2,
            1,
            0,
            1,
            11,
            0,
            0,
            0,
            "1500,00",
            4,
            0,
            1,
            "202604",
            0,
            5,
            "1500,00",
        ),
        (
            "202604",
            3,
            35,
            "351905",
            "A",
            "111302",
            1,
            "622020",
            105,
            4,
            24,
            "44,00",
            3,
            1,
            0,
            1,
            97,
            0,
            0,
            0,
            "7500,00",
            9,
            0,
            1,
            "202604",
            0,
            5,
            "7500,00",
        ),
    ]
)


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
