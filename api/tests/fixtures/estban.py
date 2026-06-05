"""Amostra do CSV ESTBAN municipal (`;`-delimitado)."""

from __future__ import annotations

_HEADER = "CODMUN;NOME_INSTITUICAO;VERBETE_160_OPERACOES_CREDITO"


def _csv(linhas: list[tuple]) -> bytes:
    corpo = [_HEADER] + [";".join(str(c) for c in linha) for linha in linhas]
    return ("\n".join(corpo) + "\n").encode("utf-8")


# Rio (3304557): crédito = (1.000.000,00 + 500.000,50) R$ mil → ×1000 = 1.500.000.500,00 reais.
# 9999999 não está no cadastro → ignorado.
AMOSTRA_ESTBAN = _csv(
    [
        ("3304557", "BANCO A", "1000000,00"),
        ("3304557", "BANCO B", "500000,50"),
        ("9999999", "BANCO C", "123,00"),
    ]
)
