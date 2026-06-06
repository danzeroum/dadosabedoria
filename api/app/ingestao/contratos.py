"""Contratos de dados por fonte — validação na **borda bronze** (qualidade comprovada, §13).

Falha **rápido e claro** se o layout da fonte pública mudar (coluna sumiu/renomeou, arquivo vazio)
antes que o dado ruim alcance prata/ouro. O contrato viaja com o adaptador e é checado no
``extrair()`` — sem rede, testável com fixture.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import polars as pl


class ContratoVioladoError(RuntimeError):
    """O dado bruto não satisfaz o contrato da fonte (provável mudança de layout na origem)."""


@dataclass(frozen=True)
class ContratoFonte:
    """Contrato declarativo do bruto de uma fonte tabular (DataFrame da camada bronze)."""

    fonte: str
    colunas_obrigatorias: frozenset[str] = field(default_factory=frozenset)
    #: ao menos UMA coluna deve conter este texto (ex.: o verbete de crédito do ESTBAN, dinâmico).
    coluna_contendo: str | None = None
    min_linhas: int = 1

    def validar(self, df: pl.DataFrame) -> None:
        colunas = set(df.columns)
        faltando = set(self.colunas_obrigatorias) - colunas
        if faltando:
            raise ContratoVioladoError(
                f"{self.fonte}: colunas obrigatórias ausentes no bruto {sorted(faltando)}; "
                f"presentes={sorted(colunas)}"
            )
        if self.coluna_contendo is not None and not any(self.coluna_contendo in c for c in colunas):
            raise ContratoVioladoError(
                f"{self.fonte}: nenhuma coluna contém '{self.coluna_contendo}' "
                f"(presentes={sorted(colunas)})"
            )
        if df.height < self.min_linhas:
            raise ContratoVioladoError(
                f"{self.fonte}: {df.height} linha(s) no bruto < mínimo esperado {self.min_linhas}"
            )
