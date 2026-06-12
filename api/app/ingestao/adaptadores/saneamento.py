"""Adaptador SNIS (Sistema Nacional de Informações sobre Saneamento) — domínio ``saneamento``.

Bronze: lê o CSV ``;``-delimitado da Série Histórica do SNIS com indicadores IN023_AE
(% atendimento de água) e IN015_AE (% coleta de esgoto). Prata: normaliza cod_ibge (7 díg.),
converte decimal BR (vírgula) para float. Ouro: máximo de cobertura por município.

ASSUNÇÕES a confirmar na 1ª busca real (#0, host ``app4.mdr.gov.br``):
- Colunas: ``cod_municipio``, ``in023_ae``, ``in015_ae``.
- Encoding UTF-8, delimitador ``;``, decimal ``,``.
- Cobertura ~5.100 municípios/exercício.
"""

from __future__ import annotations

import io

import polars as pl

from app.ingestao.adaptadores.base import FetcherFonte, Janela
from app.ingestao.contratos import ContratoFonte

CODIGO_AGUA = "saneamento.agua.atendimento_pct"
CODIGO_ESGOTO = "saneamento.esgoto.coleta_pct"

COL_IBGE = "cod_municipio"
COL_AGUA = "in023_ae"
COL_ESGOTO = "in015_ae"

CONTRATO = ContratoFonte(
    fonte="snis",
    colunas_obrigatorias=frozenset({COL_IBGE, COL_AGUA}),
)


class AdaptadorSnis:
    """Padrão Adapter: isola o formato do SNIS. Fetcher injetado (testável sem rede)."""

    codigo = "snis"

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
    def _decimal_br(expr: pl.Expr) -> pl.Expr:
        """Converte decimal brasileiro (vírgula) para float."""
        return expr.cast(pl.Utf8).str.replace(",", ".").cast(pl.Float64, strict=False)

    def transformar_prata(self, df: pl.DataFrame) -> pl.DataFrame:
        esgoto_col = (
            self._decimal_br(pl.col(COL_ESGOTO))
            if COL_ESGOTO in df.columns
            else pl.lit(None).cast(pl.Float64)
        )
        return df.select(
            pl.col(COL_IBGE).cast(pl.Utf8).str.strip_chars().alias("cod_ibge"),
            self._decimal_br(pl.col(COL_AGUA)).alias("agua_pct"),
            esgoto_col.alias("esgoto_pct"),
        ).filter(
            pl.col("cod_ibge").is_not_null()
            & (pl.col("cod_ibge") != "")
            & pl.col("agua_pct").is_not_null()
        )

    def agregar(self, df_prata: pl.DataFrame) -> pl.DataFrame:
        """Máximo de cobertura por município (consolida múltiplos prestadores)."""
        return (
            df_prata.group_by("cod_ibge")
            .agg(
                pl.col("agua_pct").max().alias("agua_pct"),
                pl.col("esgoto_pct").max().alias("esgoto_pct"),
            )
            .sort("cod_ibge")
        )


class FetcherSnisHTTP:
    """Fetcher real: baixa o CSV da Série Histórica do SNIS.

    URL e parâmetros a confirmar na 1ª busca real (#0, host ``app4.mdr.gov.br``).
    """

    BASE = "http://app4.mdr.gov.br/serieHistorica/api/dadosMunicipal/obterDadosMunicipalCSV"

    def baixar(self, janela: Janela) -> tuple[bytes, str]:  # pragma: no cover - rede
        import urllib.request

        url = f"{self.BASE}?anoRef={janela.ano}&indicadoresAgrupados={COL_AGUA},{COL_ESGOTO}"
        with urllib.request.urlopen(url, timeout=120) as resp:  # noqa: S310  # nosec B310
            return resp.read(), url
