"""Fixture SNIS (amostra CSV) — baseada na documentação pública do SNIS/MDR.

Forma a confirmar na 1ª busca real (#0, host ``app4.mdr.gov.br``):
- delimitador ``;``, encoding UTF-8
- ``cod_municipio`` = IBGE 7 díg., ``in023_ae`` = % atendimento água,
  ``in015_ae`` = % coleta esgoto; valores com vírgula decimal (formato BR).
- Cobertura: ~5.100 municípios/exercício (nem todos têm prestador declarante).
"""

from __future__ import annotations

from app.ingestao.adaptadores.base import Janela

_CAB = "cod_municipio;municipio;sigla_uf;ano;prestador;in023_ae;in015_ae"
_LINHAS = [
    "3550308;São Paulo;SP;2022;SABESP;99,82;87,52",
    "3304557;Rio de Janeiro;RJ;2022;CEDAE;92,14;58,03",
    "5300108;Brasília;DF;2022;CAESB;98,45;90,23",
    "1501402;Belém;PA;2022;COSANPA;72,89;22,14",
    "2304400;Fortaleza;CE;2022;CAGECE;94,67;42,38",
    "3509502;Campinas;SP;2022;SANASA;97,10;82,80",
    "9999999;Município Inválido;ZZ;2022;FICTICIO;80,00;",  # esgoto ausente → esgoto_pct null
]
AMOSTRA = ("\n".join([_CAB, *_LINHAS]) + "\n").encode("utf-8")


class FetcherFake:
    """Fetcher injetável para testes (sem rede)."""

    def __init__(self, bruto: bytes) -> None:
        self._bruto = bruto

    def baixar(self, janela: Janela) -> tuple[bytes, str]:
        return self._bruto, "fixture://snis"
