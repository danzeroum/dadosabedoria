"""Fixture do PNCP (amostra JSON de contratos) — **FIEL-À-FORMA** (validada no #0, 2026-06-08).

Forma confirmada contra a API real (``pncp.gov.br/api/consulta/v1/contratos``), exercício 2024:
- ``data`` (lista) + ``totalRegistros`` / ``totalPaginas`` / ``numeroPagina`` / ``paginasRestantes``
- Item tem 41 campos; relevantes: ``valorGlobal`` (**float**), ``unidadeOrgao`` (Struct 6 campos)
- ``unidadeOrgao``: ``codigoIbge`` (str, IBGE 7 díg.), ``municipioNome``, ``ufSigla``, ``ufNome``,
  ``codigoUnidade`` (código da unidade orçamentária), ``nomeUnidade``
- ``valorGlobal`` é **float** na maioria dos itens; ocasionalmente **str** em dados heterogêneos
  (tratado com ``infer_schema_length=None`` no ``parse()``).
"""

from __future__ import annotations

import json

from app.ingestao.adaptadores.base import Janela


def _unidade(ibge: str, nome: str, uf_sigla: str = "SP", uf_nome: str = "São Paulo") -> dict:
    return {
        "ufNome": uf_nome,
        "codigoUnidade": "999999",
        "nomeUnidade": f"PREFEITURA MUNICIPAL DE {nome.upper()}",
        "ufSigla": uf_sigla,
        "municipioNome": nome,
        "codigoIbge": ibge,
    }


def _item(valor_global: float | str | None, unidade: dict) -> dict:
    return {
        "anoContrato": 2024,
        "tipoContrato": {"id": 1, "nome": "Contrato"},
        "dataAssinatura": "2024-01-15",
        "valorInicial": valor_global,
        "valorGlobal": valor_global,
        "valorAcumulado": valor_global,
        "objetoContrato": "Prestação de serviços",
        "unidadeOrgao": unidade,
    }


_ITENS = [
    _item(1000000.00, _unidade("3550308", "São Paulo")),
    _item(500000.00, _unidade("3550308", "São Paulo")),
    _item(250000.00, _unidade("3509502", "Campinas")),
    _item(None, _unidade("3509502", "Campinas")),  # sem valor → filtrado na prata
    _item(
        "5335.13-31", _unidade("3509502", "Campinas")
    ),  # str heterogênea real → cast strict=False
]
AMOSTRA = json.dumps(
    {
        "data": _ITENS,
        "totalRegistros": 5,
        "totalPaginas": 1,
        "numeroPagina": 1,
        "paginasRestantes": 0,
    }
).encode("utf-8")


class FetcherFake:
    """Fetcher injetável que devolve a amostra (sem rede)."""

    def __init__(self, bruto: bytes) -> None:
        self._bruto = bruto

    def baixar(self, janela: Janela) -> tuple[bytes, str]:
        return self._bruto, "fixture://pncp"
