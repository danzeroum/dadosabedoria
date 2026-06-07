"""Fixtures do SICONFI — **FIÉIS-À-FORMA** do DCA real (validados no #0, 2026-06-07; ADR-0028).

Capturados da API real (``apidatalake.tesouro.gov.br/ords/siconfi/tt/dca``), São Paulo 2024.
Forma confirmada vs. o mock antigo (fiel-ao-contrato): ``cod_ibge`` é **int**, ``valor`` é
**numérico**, e há a dimensão **``coluna``** (Receitas Brutas Realizadas vs. deduções; Despesas
Empenhadas vs. Liquidadas) + ``cod_conta``. Amostras trimadas (poucas linhas), **valores reais**.

- ``AMOSTRA``         — Anexo I-C (receitas): conta "Transferências Correntes" → ``financas``.
  Inclui as armadilhas que o #0 revelou: deduções (mesma conta, outra ``coluna``), a transferência
  **intra**-orçamentária (``RI7.7...`` — fora do alvo) e um off-target — para o filtro provar-se.
- ``AMOSTRA_FUNCOES`` — Anexo I-E (despesas por função): a **forma-verdade** do OndeFoi (TRANSP-06).
  A função vive no texto ``conta`` ("10 - Saúde"); ``cod_conta`` é constante ("TotalDespesas").
"""

from __future__ import annotations

import json
from typing import Any

from app.ingestao.adaptadores.base import Janela

_INSTITUICAO = "Prefeitura Municipal de São Paulo - SP"


def _linha(
    *,
    cod_ibge: int,
    cod_conta: str,
    conta: str,
    coluna: str,
    valor: float,
    anexo: str,
    exercicio: int = 2024,
    uf: str = "SP",
) -> dict[str, Any]:
    """Uma linha na forma real do DCA (todas as chaves que a API devolve)."""
    return {
        "exercicio": exercicio,
        "instituicao": _INSTITUICAO,
        "cod_ibge": cod_ibge,
        "uf": uf,
        "anexo": anexo,
        "rotulo": "Padrão",
        "coluna": coluna,
        "cod_conta": cod_conta,
        "conta": conta,
        "valor": valor,
        "populacao": 12200180,
    }


_IC = "DCA-Anexo I-C"
_TC = "1.7.0.0.00.0.0 - Transferências Correntes"  # orçamentária (alvo do indicador financas)

# Anexo I-C — receitas. Só a Transf. Corrente ORÇAMENTÁRIA realizada (bruta) entra no indicador.
_ITENS_IC: list[dict[str, Any]] = [
    # SP: alvo (RO1.7... + Receitas Brutas Realizadas) — entra.
    _linha(
        cod_ibge=3550308,
        cod_conta="RO1.7.0.0.00.0.0",
        conta=_TC,
        coluna="Receitas Brutas Realizadas",
        valor=1_000_000.00,
        anexo=_IC,
    ),
    # SP: MESMA conta, outra coluna (dedução) — NÃO somar (revelado no #0: 3 colunas por conta).
    _linha(
        cod_ibge=3550308,
        cod_conta="RO1.7.0.0.00.0.0",
        conta=_TC,
        coluna="Deduções - FUNDEB",
        valor=300_000.00,
        anexo=_IC,
    ),
    # SP: Transferência Corrente INTRA-orçamentária (RI7.7...) — texto idêntico, fora do alvo.
    _linha(
        cod_ibge=3550308,
        cod_conta="RI7.7.0.0.00.0.0",
        conta="7.7.0.0.00.0.0 - Transferências Correntes",
        coluna="Receitas Brutas Realizadas",
        valor=50_000.00,
        anexo=_IC,
    ),
    # Outro município (no cadastro do seed): alvo — entra.
    _linha(
        cod_ibge=3509502,
        cod_conta="RO1.7.0.0.00.0.0",
        conta=_TC,
        coluna="Receitas Brutas Realizadas",
        valor=250_000.00,
        anexo=_IC,
    ),
    # Off-target (impostos) — fora do alvo.
    _linha(
        cod_ibge=3550308,
        cod_conta="RO1.1.0.0.00.0.0",
        conta="1.1.0.0.00.0.0 - Impostos, Taxas e Contribuições de Melhoria",
        coluna="Receitas Brutas Realizadas",
        valor=9_999.00,
        anexo=_IC,
    ),
]
AMOSTRA = json.dumps({"items": _ITENS_IC}).encode("utf-8")

_IE = "DCA-Anexo I-E"


def _funcao(conta: str, empenhado: float, liquidado: float) -> list[dict[str, Any]]:
    return [
        _linha(
            cod_ibge=3550308,
            cod_conta="TotalDespesas",
            conta=conta,
            coluna="Despesas Empenhadas",
            valor=empenhado,
            anexo=_IE,
        ),
        _linha(
            cod_ibge=3550308,
            cod_conta="TotalDespesas",
            conta=conta,
            coluna="Despesas Liquidadas",
            valor=liquidado,
            anexo=_IE,
        ),
    ]


# Anexo I-E — despesas por função (SP 2024, valores reais). Função de 1º nível = "NN - Nome".
_ITENS_IE: list[dict[str, Any]] = [
    *_funcao("08 - Assistência Social", 2_476_946_124.21, 2_403_458_773.82),
    *_funcao("10 - Saúde", 22_752_837_820.49, 21_927_842_055.50),
    *_funcao("12 - Educação", 23_290_435_795.57, 22_334_221_416.70),
    *_funcao("17 - Saneamento", 2_868_478_794.47, 2_033_377_157.72),
    # Subfunção (NN.NNN) — NÃO é função de 1º nível; o detector de função deve ignorá-la.
    *_funcao("10.301 - Atenção Básica", 10_594_697_971.08, 10_346_536_695.56),
]
AMOSTRA_FUNCOES = json.dumps({"items": _ITENS_IE}).encode("utf-8")


class FetcherFake:
    """Fetcher injetável que devolve a amostra (sem rede)."""

    def __init__(self, bruto: bytes) -> None:
        self._bruto = bruto

    def baixar(self, janela: Janela) -> tuple[bytes, str]:
        return self._bruto, "fixture://siconfi"
