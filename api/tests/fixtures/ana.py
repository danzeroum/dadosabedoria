"""Fixture ANA Monitor de Secas (amostra CSV) — baseada na metodologia USDM adaptada pela ANA.

Forma a confirmar na 1ª busca real (#0, host ``monitordesecas.ana.gov.br``):
- delimitador ``;``, encoding UTF-8
- ``cod_ibge`` = IBGE 7 díg., ``classe_seca`` = Normal/D0/D1/D2/D3/D4
- Cobertura: ~5.500 municípios/mês (maior concentração no Semiárido e Centro-Oeste).
"""

from __future__ import annotations

from app.ingestao.adaptadores.base import Janela

_CAB = "cod_ibge;municipio;uf;ano;mes;classe_seca"
_LINHAS = [
    # SP — dois meses, pior = D1 → seca_indice=2 → atencao
    "3550308;São Paulo;SP;2023;01;Normal",
    "3550308;São Paulo;SP;2023;07;D1",
    # RJ — dois meses, pior = D0 → seca_indice=1 → atencao
    "3304557;Rio de Janeiro;RJ;2023;01;D0",
    "3304557;Rio de Janeiro;RJ;2023;07;Normal",
    # DF — D2 → seca_indice=3 → critico
    "5300108;Brasília;DF;2023;06;D2",
    # PA — Normal → seca_indice=0 → normal
    "1501402;Belém;PA;2023;06;Normal",
    # CE — D3 → seca_indice=4 → critico
    "2304400;Fortaleza;CE;2023;06;D3",
    # SP/Campinas — D0 → seca_indice=1 → atencao
    "3509502;Campinas;SP;2023;06;D0",
    # inválido: classe ausente → filtrado na prata
    "9999999;Município Inválido;ZZ;2023;06;",
]
AMOSTRA = ("\n".join([_CAB, *_LINHAS]) + "\n").encode("utf-8")


class FetcherFake:
    """Fetcher injetável para testes (sem rede)."""

    def __init__(self, bruto: bytes) -> None:
        self._bruto = bruto

    def baixar(self, janela: Janela) -> tuple[bytes, str]:
        return self._bruto, "fixture://ana"
