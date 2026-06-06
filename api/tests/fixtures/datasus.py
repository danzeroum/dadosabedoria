"""Fixture do DATASUS/SIH-RD (amostra tabular de AIH) — testes sem rede."""

from __future__ import annotations

from app.ingestao.adaptadores.base import Janela

# Tabular como o SIH-RD após decodificação (uma linha por AIH). MUNIC_RES é o IBGE de 6 dígitos do
# DATASUS (355030 = São Paulo; 350950 = Campinas). A linha I10 (fora do grupo J) testa o filtro.
_CABECALHO = "MUNIC_RES,DIAG_PRINC"
_LINHAS = [
    "355030,J189",  # SP — pneumonia
    "355030,J45",  # SP — asma
    "355030,J22",  # SP — infecção respiratória aguda
    "355030,I10",  # SP — hipertensão (fora do grupo J → filtrado)
    "350950,J189",  # Campinas
    "350950,J45",  # Campinas
]
AMOSTRA = ("\n".join([_CABECALHO, *_LINHAS]) + "\n").encode("utf-8")


class FetcherFake:
    """Fetcher injetável que devolve a amostra (sem rede)."""

    def __init__(self, bruto: bytes) -> None:
        self._bruto = bruto

    def baixar(self, janela: Janela) -> tuple[bytes, str]:
        return self._bruto, "fixture://datasus_sih"
