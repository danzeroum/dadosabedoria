"""Fixture SISVAN — estado nutricional infantil (amostra JSON fiel-à-forma).

Forma real (API de Dados Abertos do MS, ``/sisvan/estado-nutricional``):
- JSON ``{"estados_nutricionais": [...]}``; ``codigo_municipio`` = IBGE **6 dígitos**.
- ``crianca_imc_x_idade`` = texto ("Magreza acentuada"/"Magreza" = baixo peso; "Eutrofia" etc.).
- baixo peso = magreza / magreza acentuada.

Municípios de teste (código de 6 dígitos):
- Sorriso (510792): 4/10 crianças com baixo peso → 40% → crítico
- Campinas (350950): 1/20 crianças com baixo peso → 5% → elevado
- São Paulo (355030): 1/50 crianças com baixo peso → 2% → moderado
- Rio (330455): 0/5 crianças com baixo peso → 0% → baixo
- Registros inválidos: idade ≥ 5, sem município, classificação nula (não-criança) → descartados
"""

from __future__ import annotations

import json

from app.ingestao.adaptadores.base import Janela


def _reg(cod: object, idade: object, imc: object) -> dict:
    """Registro fiel-à-forma (subconjunto dos campos reais que o parser consome)."""
    return {
        "codigo_municipio": cod,
        "uf": "SP",
        "idade": idade,
        "fase_vida": "ENTRE 2 ANOS A 5 ANOS",
        "crianca_imc_x_idade": imc,
        "codigo_estado_nutricional_imc_gestante": None,
        "ano_mes_competencia": "201812",
    }


_REGISTROS: list[dict] = [
    # Sorriso: 4 baixo peso em 10 crianças (40%) → crítico
    _reg(510792, 0, "Magreza acentuada"),
    _reg(510792, 1, "Magreza"),
    _reg(510792, 2, "Magreza acentuada"),
    _reg(510792, 3, "Magreza"),
    *[_reg(510792, 2, "Eutrofia") for _ in range(6)],
    # Campinas: 1 baixo peso em 20 crianças (5%) → elevado
    *[_reg(350950, 2, "Eutrofia") for _ in range(19)],
    _reg(350950, 1, "Magreza acentuada"),
    # SP: 1 baixo peso em 50 crianças (2%) → moderado
    *[_reg(355030, 3, "Eutrofia") for _ in range(49)],
    _reg(355030, 0, "Magreza"),
    # Rio: 0 em 5 → baixo
    *[_reg(330455, 1, "Eutrofia") for _ in range(5)],
    # Inválido: idade ≥ 5 (descartado na prata)
    _reg(355030, 6, "Magreza acentuada"),
    _reg(355030, 7, "Magreza"),
    # Inválido: sem município
    _reg(None, 2, "Magreza"),
    _reg("", 0, "Magreza"),
    # Inválido: não-criança (classificação IMC-x-idade nula)
    _reg(510792, 30, None),
]

AMOSTRA: bytes = json.dumps({"estados_nutricionais": _REGISTROS}).encode("utf-8")


class FetcherFake:
    """Fetcher injetável para testes (sem rede)."""

    def __init__(self, bruto: bytes) -> None:
        self._bruto = bruto

    def baixar(self, janela: Janela) -> tuple[bytes, str]:
        return self._bruto, "fixture://sisvan"
