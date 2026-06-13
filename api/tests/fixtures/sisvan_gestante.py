"""Fixture SISVAN gestante — estado nutricional de gestantes, domínio saude."""

from __future__ import annotations

from app.ingestao.adaptadores.base import Janela

_LINHAS = [
    # Campinas (3509502): 3 baixo peso em 20 gestantes = 15% → moderado
    *["3509502;GESTANTE;2"] * 17,
    "3509502;GESTANTE;1",
    "3509502;GESTANTE;1",
    "3509502;GESTANTE;1",
    # SP (3550308): 1 em 30 = 3.3% → baixo  (below k-anon n_minimo=5 for suppression check)
    *["3550308;GESTANTE;2"] * 29,
    "3550308;GESTANTE;1",
    # Rio (3304557): 10 em 40 = 25% → elevado
    *["3304557;GESTANTE;2"] * 30,
    *["3304557;GESTANTE;1"] * 10,
    # Campinas valid record with outro publico (filtered out)
    "3509502;CRIANCA;1",
    # Invalid: empty IBGE
    ";GESTANTE;1",
    # Invalid: estado out of range
    "3509502;GESTANTE;0",
    "3509502;GESTANTE;5",
]
_CSV = "CO_MUNICIPIO_IBGE;CO_PUBLICO_ALVO;CO_ESTADO_NUTRI_GESTANTE\n" + "\n".join(_LINHAS)
AMOSTRA_GESTANTE: bytes = _CSV.encode("utf-8")


class FetcherFake:
    def __init__(self, bruto: bytes) -> None:
        self._bruto = bruto

    def baixar(self, janela: Janela) -> tuple[bytes, str]:
        return self._bruto, "fixture://sisvan_gestante"
