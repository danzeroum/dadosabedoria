"""Fixture ANEEL DEC/FEC (amostra CSV) — baseada no layout dos dados abertos da ANEEL.

Forma a confirmar na 1ª busca real (host ``dadosabertos.aneel.gov.br``):
- delimitador ``;``, encoding UTF-8
- ``cod_ibge`` = IBGE 7 díg., ``dec`` = horas/consumidor/ano, ``fec`` = interrupções/ano.
- Cobertura: ~3.300–3.600 municípios com distribuidoras cadastradas.
"""

from __future__ import annotations

from app.ingestao.adaptadores.base import Janela

_CAB = "cod_ibge;municipio;uf;distribuidora;ano;dec;fec"
_LINHAS = [
    "3550308;São Paulo;SP;ENEL SP;2023;3.52;4.21",       # confiavel
    "3304557;Rio de Janeiro;RJ;LIGHT;2023;9.80;8.15",    # regular
    "5300108;Brasília;DF;CEB;2023;7.10;5.90",            # confiavel
    "1501402;Belém;PA;CELPA;2023;25.40;18.60",           # frágil
    "2304400;Fortaleza;CE;ENEL CE;2023;11.20;9.40",      # regular
    "3509502;Campinas;SP;CPFL;2023;5.75;5.10",           # confiavel
    "9999999;Município Inválido;ZZ;FICTICIO;2023;8.00;",  # fec ausente
]
AMOSTRA = ("\n".join([_CAB, *_LINHAS]) + "\n").encode("utf-8")


class FetcherFake:
    """Fetcher injetável para testes (sem rede)."""

    def __init__(self, bruto: bytes) -> None:
        self._bruto = bruto

    def baixar(self, janela: Janela) -> tuple[bytes, str]:
        return self._bruto, "fixture://aneel"
