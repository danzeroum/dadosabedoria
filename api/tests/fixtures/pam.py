"""Fixture IBGE PAM SIDRA v3 (amostra JSON) — baseada no layout da API SIDRA v3 do IBGE.

Forma a confirmar na 1ª busca real (#0, host ``servicodados.ibge.gov.br``):
- JSON com lista de tabelas; cada tabela tem "resultados[].series[]"
- "localidade.id" = IBGE 7 díg., "serie.<ano>" = valor em Mil Reais como string
- "-" = sem dado para o município; dados de tabelas 1612 + 1613, variável 215
- SP (3550308): 1612=5000, 1613=1000 → total=6.000.000 BRL
- Campinas (3509502): 1612=8000, 1613=2000 → total=10.000.000 BRL
- Rio (3304557): 1612=200, sem 1613 → total=200.000 BRL
- Inválido (9999999): valor "-" → filtrado na prata
"""

from __future__ import annotations

import json

from app.ingestao.adaptadores.base import Janela

_DADOS: list[dict] = [
    {
        "_tabela": "1612",
        "ano": 2023,
        "id": "1612",
        "variavel": "Valor da produção",
        "unidade": "Mil Reais",
        "resultados": [
            {
                "classificacoes": [],
                "series": [
                    {
                        "localidade": {"id": "3550308", "nivel": {"id": "N6"}, "nome": "São Paulo"},
                        "serie": {"2023": "5000"},
                    },
                    {
                        "localidade": {
                            "id": "3509502",
                            "nivel": {"id": "N6"},
                            "nome": "Campinas",
                        },
                        "serie": {"2023": "8000"},
                    },
                    {
                        "localidade": {
                            "id": "3304557",
                            "nivel": {"id": "N6"},
                            "nome": "Rio de Janeiro",
                        },
                        "serie": {"2023": "200"},
                    },
                    {
                        "localidade": {
                            "id": "9999999",
                            "nivel": {"id": "N6"},
                            "nome": "Município Inválido",
                        },
                        "serie": {"2023": "-"},
                    },
                ],
            }
        ],
    },
    {
        "_tabela": "1613",
        "ano": 2023,
        "id": "1613",
        "variavel": "Valor da produção",
        "unidade": "Mil Reais",
        "resultados": [
            {
                "classificacoes": [],
                "series": [
                    {
                        "localidade": {"id": "3550308", "nivel": {"id": "N6"}, "nome": "São Paulo"},
                        "serie": {"2023": "1000"},
                    },
                    {
                        "localidade": {
                            "id": "3509502",
                            "nivel": {"id": "N6"},
                            "nome": "Campinas",
                        },
                        "serie": {"2023": "2000"},
                    },
                ],
            }
        ],
    },
]

AMOSTRA = json.dumps(_DADOS).encode("utf-8")


class FetcherFake:
    """Fetcher injetável para testes (sem rede)."""

    def __init__(self, bruto: bytes) -> None:
        self._bruto = bruto

    def baixar(self, janela: Janela) -> tuple[bytes, str]:
        return self._bruto, "fixture://ibge_pam"
