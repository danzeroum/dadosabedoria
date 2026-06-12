"""Adaptador ANA (Agência Nacional de Águas) — Monitor de Secas.

Bronze: lê o CSV mensal de classificação de seca por município, publicado no Monitor de Secas da
ANA (``monitordesecas.ana.gov.br``).

Indicador:
- ``classe_seca``: classificação de seca (Normal, D0, D1, D2, D3, D4); convertida para índice
  numérico ``seca_indice`` (0–5) para armazenamento na camada ouro.
  Normal=0, D0=1, D1=2, D2=3, D3=4, D4=5.

Prata: normaliza cod_ibge (7 díg.), mapeia classe → índice float.
Ouro: máximo de seca_indice por município no período (pior mês do ano).

ASSUNÇÕES a confirmar na 1ª busca real (#0, host ``monitordesecas.ana.gov.br``):
- Colunas: ``cod_ibge``, ``municipio``, ``uf``, ``ano``, ``mes``, ``classe_seca``.
- Encoding UTF-8, delimitador ``;``.
- Classes: Normal, D0, D1, D2, D3, D4 (metodologia USDM adaptada pela ANA).
- Cobertura: ~5.500 municípios / mês (cobertura nacional).
"""

from __future__ import annotations

import io

import polars as pl

from app.ingestao.adaptadores.base import FetcherFonte, Janela
from app.ingestao.contratos import ContratoFonte

CODIGO_SECA = "saneamento.agua.seca_indice"

COL_IBGE = "cod_ibge"
COL_CLASSE = "classe_seca"
COL_ANO = "ano"
COL_MES = "mes"

# Mapeamento classe → índice numérico (0–5)
_MAPA_CLASSE: dict[str, float] = {
    "Normal": 0.0,
    "D0": 1.0,
    "D1": 2.0,
    "D2": 3.0,
    "D3": 4.0,
    "D4": 5.0,
}

CONTRATO = ContratoFonte(
    fonte="ana",
    colunas_obrigatorias=frozenset({COL_IBGE, COL_CLASSE}),
)


class AdaptadorAna:
    """Padrão Adapter: isola o formato ANA Monitor de Secas. Fetcher injetado (testável)."""

    codigo = "ana"

    def __init__(self, fetcher: FetcherFonte) -> None:
        self._fetcher = fetcher

    def baixar_bruto(self, janela: Janela) -> tuple[bytes, str]:
        return self._fetcher.baixar(janela)

    def parse(self, bruto: bytes) -> pl.DataFrame:
        return pl.read_csv(
            io.BytesIO(bruto),
            separator=";",
            encoding="utf8-lossy",
            infer_schema_length=0,
            ignore_errors=True,
        )

    def extrair(self, janela: Janela) -> pl.DataFrame:
        bruto, _ = self.baixar_bruto(janela)
        df = self.parse(bruto)
        CONTRATO.validar(df)
        return df

    @staticmethod
    def _classe_para_indice(expr: pl.Expr) -> pl.Expr:
        """Converte classe textual (Normal/D0-D4) para índice numérico 0–5."""
        return (
            expr.cast(pl.Utf8)
            .str.strip_chars()
            .replace(_MAPA_CLASSE)
            .cast(pl.Float64, strict=False)
        )

    def transformar_prata(self, df: pl.DataFrame) -> pl.DataFrame:
        return df.select(
            pl.col(COL_IBGE).cast(pl.Utf8).str.strip_chars().alias("cod_ibge"),
            self._classe_para_indice(pl.col(COL_CLASSE)).alias("seca_indice"),
        ).filter(
            pl.col("cod_ibge").is_not_null()
            & (pl.col("cod_ibge") != "")
            & pl.col("seca_indice").is_not_null()
        )

    def agregar(self, df_prata: pl.DataFrame) -> pl.DataFrame:
        """Máximo de seca_indice por município (pior mês do período anual)."""
        return (
            df_prata.group_by("cod_ibge")
            .agg(pl.col("seca_indice").max().alias("seca_indice"))
            .sort("cod_ibge")
        )


class FetcherAnaHTTP:
    """Fetcher real: baixa o CSV do Monitor de Secas da ANA.

    URL e parâmetros a confirmar na 1ª busca real (``monitordesecas.ana.gov.br``).
    """

    BASE = "https://monitordesecas.ana.gov.br/mapa"

    def baixar(self, janela: Janela) -> tuple[bytes, str]:  # pragma: no cover - rede
        import urllib.request

        url = f"{self.BASE}?ano={janela.ano}&formato=csv"
        with urllib.request.urlopen(url, timeout=120) as resp:  # noqa: S310  # nosec B310
            return resp.read(), url
