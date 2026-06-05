"""Contrato de adaptador de fonte + tipos compartilhados da ingestão."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    import polars as pl


@dataclass(frozen=True)
class Janela:
    """Janela de referência da extração (incremental — só o período, invariante 6)."""

    ano: int
    mes: int

    @property
    def competencia(self) -> str:
        return f"{self.ano:04d}{self.mes:02d}"

    @property
    def periodo(self) -> date:
        return date(self.ano, self.mes, 1)

    @classmethod
    def de_competencia(cls, comp: str) -> Janela:
        return cls(int(comp[:4]), int(comp[4:6]))


@runtime_checkable
class AdaptadorFonte(Protocol):
    """Isola o formato de uma fonte pública e expõe a extração para a camada bronze."""

    codigo: str

    def extrair(self, janela: Janela) -> pl.DataFrame: ...


class FetcherFonte(Protocol):
    """Busca o dado bruto (já descompactado) de uma janela. Injetável → testável sem rede."""

    def baixar(self, janela: Janela) -> tuple[bytes, str]:
        """Retorna ``(conteúdo_bruto, url_de_origem)``."""
        ...
