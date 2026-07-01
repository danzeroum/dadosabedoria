"""Fixture SISVAN gestante — estado nutricional de gestantes (amostra JSON fiel-à-forma).

Forma real (API de Dados Abertos do MS): ``codigo_estado_nutricional_imc_gestante`` = texto
("Baixo peso" = baixo peso; "Adequado ou eutrófico"/"Sobrepeso"/"Obesidade"). Só gestantes têm
essa classificação preenchida — é o filtro de público. ``codigo_municipio`` = IBGE 6 dígitos.

Municípios de teste (6 dígitos):
- Campinas (350950): 3 baixo peso em 20 gestantes = 15% → moderado
- São Paulo (355030): 1 em 30 = 3.3% → baixo
- Rio (330455): 10 em 40 = 25% → elevado
- Registros inválidos: sem município, não-gestante (classificação nula) → descartados
"""

from __future__ import annotations

import json

from app.ingestao.adaptadores.base import Janela


def _reg(cod: object, gestante_imc: object) -> dict:
    return {
        "codigo_municipio": cod,
        "uf": "SP",
        "idade": 28,
        "fase_vida": "ADULTO",
        "crianca_imc_x_idade": None,
        "codigo_estado_nutricional_imc_gestante": gestante_imc,
        "ano_mes_competencia": "201812",
    }


_REGISTROS: list[dict] = [
    # Campinas: 3 baixo peso em 20 gestantes (15%) → moderado
    *[_reg(350950, "Adequado ou eutrófico") for _ in range(17)],
    *[_reg(350950, "Baixo peso") for _ in range(3)],
    # SP: 1 em 30 (3.3%) → baixo
    *[_reg(355030, "Adequado ou eutrófico") for _ in range(29)],
    _reg(355030, "Baixo peso"),
    # Rio: 10 em 40 (25%) → elevado
    *[_reg(330455, "Adequado ou eutrófico") for _ in range(30)],
    *[_reg(330455, "Baixo peso") for _ in range(10)],
    # Inválido: sem município
    _reg(None, "Baixo peso"),
    # Inválido: não-gestante (classificação gestacional nula)
    _reg(350950, None),
]

AMOSTRA_GESTANTE: bytes = json.dumps({"estados_nutricionais": _REGISTROS}).encode("utf-8")


class FetcherFake:
    def __init__(self, bruto: bytes) -> None:
        self._bruto = bruto

    def baixar(self, janela: Janela) -> tuple[bytes, str]:
        return self._bruto, "fixture://sisvan_gestante"
