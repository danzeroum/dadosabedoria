"""Fixture SISVAN — estado nutricional infantil (amostra CSV fiel-à-forma).

Colunas: CO_MUNICIPIO_IBGE, NU_IDADE_ANO, CO_ESTADO_NUTRI_CRIANCA (separador ";")
Códigos de estado: 1=magreza acentuada, 2=magreza, 3=eutrofia, 4=risco sobrepeso,
                   5=sobrepeso, 6=obesidade
Municípios de teste:
- Sorriso (5107925, MT): 4/10 crianças com baixo peso → 40% → crítico
- Campinas (3509502, SP): 1/20 crianças com baixo peso → 5% → elevado
- São Paulo (3550308, SP): 1/50 crianças com baixo peso → 2% → moderado
- Rio (3304557, RJ): 0/5 crianças com baixo peso → 0% → baixo
- Linha inválida (idade ≥ 5): descartada na prata
- Linha sem município: descartada na prata
"""

from __future__ import annotations

from app.ingestao.adaptadores.base import Janela

_LINHAS = [
    # Sorriso: 4 baixo peso em 10 crianças (40%) → crítico
    "5107925;0;1",
    "5107925;1;2",
    "5107925;2;1",
    "5107925;3;2",
    "5107925;0;3",
    "5107925;1;3",
    "5107925;2;3",
    "5107925;3;3",
    "5107925;4;3",
    "5107925;4;3",
    # Campinas: 1 baixo peso em 20 crianças (5%) → elevado
    *["3509502;2;3"] * 19,
    "3509502;1;1",
    # SP: 1 baixo peso em 50 crianças (2%) → moderado
    *["3550308;3;3"] * 49,
    "3550308;0;2",
    # Rio: 0 em 5 → baixo
    *["3304557;1;3"] * 5,
    # Inválida: idade ≥ 5 (deve ser descartada na prata)
    "3550308;6;1",
    "3550308;7;2",
    # Inválida: sem código IBGE
    ";2;1",
    "  ;0;2",
    # Inválida: estado fora do intervalo
    "5107925;2;0",
    "5107925;3;7",
]

_CSV = "CO_MUNICIPIO_IBGE;NU_IDADE_ANO;CO_ESTADO_NUTRI_CRIANCA\n" + "\n".join(_LINHAS)
AMOSTRA: bytes = _CSV.encode("utf-8")


class FetcherFake:
    """Fetcher injetável para testes (sem rede)."""

    def __init__(self, bruto: bytes) -> None:
        self._bruto = bruto

    def baixar(self, janela: Janela) -> tuple[bytes, str]:
        return self._bruto, "fixture://sisvan"
