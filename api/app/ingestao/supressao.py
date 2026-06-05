"""Regra ÚNICA de supressão por k-anonimato (invariante 1).

Esta é a *única* definição da regra em todo o código (DRY, §10). É pura, determinística e sem
I/O — portanto trivialmente testável (TDD). O único ponto de chamada em produção é
``app.ingestao.ouro.GravadorOuro.escrever_ouro`` (garantido por teste).

Semântica resolvida (documentada em ADR-0004, pontos silenciosos na doc decididos *fail-closed*):

- limiar efetivo = ``max(n_minimo, LIMIAR_SENSIVEL_MIN)`` quando ``origem_sensivel`` — um piso
  para indicadores de origem sensível mesmo que mal-semeados com ``n_minimo`` baixo.
- ``limiar <= 0``  → supressão DESLIGADA (ex.: saldo CAGED, que não é contagem de pessoas:
  ``n_minimo=0`` e ``n_amostra=None`` é o caso normal e válido).
- ``limiar > 0`` e ``n_amostra is None`` → **suprime** (fail-closed: não dá para provar k-anon).
- ``n_amostra < limiar`` → suprime.  (Fronteira ``<``: ``n_amostra == limiar`` é mantido.)
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal
from typing import Protocol

#: Piso de k-anonimato para indicadores derivados de microdado sensível (saúde, violência).
LIMIAR_SENSIVEL_MIN = 5

MOTIVO_PADRAO = "n < limiar de privacidade"
MOTIVO_SEM_AMOSTRA = "n_amostra ausente; impossível verificar limiar de privacidade"


@dataclass(frozen=True)
class MetaIndicadorSupressao:
    """O mínimo que a regra precisa saber sobre o indicador da célula."""

    n_minimo: int
    origem_sensivel: bool


@dataclass(frozen=True)
class ResultadoSupressao:
    valor: Decimal | None  # None quando suprimido
    suprimido: bool
    motivo_supressao: str | None
    n_amostra: int | None  # ecoado para gravação em ``valor``


class EstrategiaSupressao(Protocol):
    """Strategy: permite trocar a política (ex.: ruído diferencial) via Factory, sem mexer nos
    chamadores."""

    def aplicar(
        self,
        *,
        valor: Decimal | None,
        n_amostra: int | None,
        meta: MetaIndicadorSupressao,
    ) -> ResultadoSupressao: ...


class SupressaoKAnonimato:
    """A regra de k-anonimato. Suprime a célula ANTES da gravação (invariante 1)."""

    def limiar_efetivo(self, meta: MetaIndicadorSupressao) -> int:
        if meta.origem_sensivel:
            return max(meta.n_minimo, LIMIAR_SENSIVEL_MIN)
        return meta.n_minimo

    def aplicar(
        self,
        *,
        valor: Decimal | None,
        n_amostra: int | None,
        meta: MetaIndicadorSupressao,
    ) -> ResultadoSupressao:
        limiar = self.limiar_efetivo(meta)

        if limiar <= 0:
            # Supressão desligada: nenhuma contagem pode ser < 0.
            return ResultadoSupressao(valor, False, None, n_amostra)

        if n_amostra is None:
            return ResultadoSupressao(None, True, MOTIVO_SEM_AMOSTRA, n_amostra)

        if n_amostra < limiar:
            return ResultadoSupressao(None, True, MOTIVO_PADRAO, n_amostra)

        return ResultadoSupressao(valor, False, None, n_amostra)
