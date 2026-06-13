"""Fixture SINAN/Dengue — casos confirmados por município/ano (amostra CSV fiel-à-forma).

Colunas: ID_MUNICIP, NU_ANO, CLASSI_FIN (separador ",")
CLASSI_FIN: 1=Dengue clássica, 2=Dengue c/ sinais de alarme, 3=Dengue grave, 5=Descartado

Municípios de teste:
- São Paulo (355030, IBGE 6 díg.): 8 confirmados + 2 descartados → 8 casos na prata
- Campinas (350950, IBGE 6 díg.): 3 confirmados → 3 casos (abaixo do n_minimo=5, suprimido)
- Rio (330455, IBGE 6 díg.): 10 confirmados → 10 casos
- 1 linha sem município: descartada na prata
"""

from __future__ import annotations

from app.ingestao.adaptadores.base import Janela

_LINHAS = [
    # SP (355030): 8 confirmados (CLASSI_FIN 1, 2, 3) + 2 descartados (5)
    "355030,2023,1",
    "355030,2023,2",
    "355030,2023,3",
    "355030,2023,1",
    "355030,2023,2",
    "355030,2023,3",
    "355030,2023,1",
    "355030,2023,2",
    "355030,2023,5",  # descartado → excluído na prata
    "355030,2023,5",  # descartado → excluído na prata
    # Campinas (350950): 3 confirmados → abaixo do n_minimo=5 → suprimido no ouro
    "350950,2023,1",
    "350950,2023,1",
    "350950,2023,2",
    # Rio (330455): 10 confirmados
    "330455,2023,1",
    "330455,2023,2",
    "330455,2023,3",
    "330455,2023,1",
    "330455,2023,2",
    "330455,2023,3",
    "330455,2023,1",
    "330455,2023,2",
    "330455,2023,3",
    "330455,2023,1",
    # Linha sem município: descartada na prata
    ",2023,1",
]

_CSV = "ID_MUNICIP,NU_ANO,CLASSI_FIN\n" + "\n".join(_LINHAS)
AMOSTRA: bytes = _CSV.encode("utf-8")


class FetcherFake:
    """Fetcher injetável para testes (sem rede)."""

    def __init__(self, bruto: bytes) -> None:
        self._bruto = bruto

    def baixar(self, janela: Janela) -> tuple[bytes, str]:
        return self._bruto, "fixture://sinan"
