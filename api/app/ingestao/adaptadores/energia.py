"""Adaptador ANEEL (Agência Nacional de Energia Elétrica) — domínio ``energia``.

Bronze: lê o CSV dos Indicadores de Qualidade do Serviço de Distribuição (DEC/FEC)
por distribuidora/município, publicado nos dados abertos da ANEEL.

Indicadores:
- DEC (Duração Equivalente por Consumidor): horas de interrupção por consumidor/ano.
- FEC (Frequência Equivalente por Consumidor): número de interrupções por consumidor/ano.

Prata: normaliza cod_ibge (7 díg.), converte DEC/FEC para float. Ouro: média de DEC/FEC
por município (consolida múltiplas distribuidoras que atendem o mesmo município).

ASSUNÇÕES a confirmar na 1ª busca real (host ``dadosabertos.aneel.gov.br``):
- Colunas: ``cod_ibge``, ``dec``, ``fec`` (nomes a confirmar no CSV real).
- Encoding UTF-8, delimitador ``;`` ou ``,``, decimal ponto ou vírgula.
- Cobertura: ~3.300–3.600 municípios com distribuidoras cadastradas na ANEEL.
"""

from __future__ import annotations

import io

import polars as pl

from app.ingestao.adaptadores.base import FetcherFonte, Janela
from app.ingestao.contratos import ContratoFonte

CODIGO_DEC = "energia.qualidade.dec"
CODIGO_FEC = "energia.qualidade.fec"

COL_IBGE = "cod_ibge"
COL_DEC = "dec"
COL_FEC = "fec"

CONTRATO = ContratoFonte(
    fonte="aneel",
    colunas_obrigatorias=frozenset({COL_IBGE, COL_DEC}),
)


class AdaptadorAneel:
    """Padrão Adapter: isola o formato ANEEL DEC/FEC. Fetcher injetado (testável sem rede)."""

    codigo = "aneel"

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
        """Converte decimal brasileiro (vírgula) ou internacional (ponto) para float."""
        return expr.cast(pl.Utf8).str.replace(",", ".").cast(pl.Float64, strict=False)

    def transformar_prata(self, df: pl.DataFrame) -> pl.DataFrame:
        fec_col = (
            self._decimal_br(pl.col(COL_FEC))
            if COL_FEC in df.columns
            else pl.lit(None).cast(pl.Float64)
        )
        return df.select(
            pl.col(COL_IBGE).cast(pl.Utf8).str.strip_chars().alias("cod_ibge"),
            self._decimal_br(pl.col(COL_DEC)).alias("dec"),
            fec_col.alias("fec"),
        ).filter(
            pl.col("cod_ibge").is_not_null()
            & (pl.col("cod_ibge") != "")
            & pl.col("dec").is_not_null()
        )

    def agregar(self, df_prata: pl.DataFrame) -> pl.DataFrame:
        """Média de DEC/FEC por município (consolida múltiplas distribuidoras)."""
        return (
            df_prata.group_by("cod_ibge")
            .agg(
                pl.col("dec").mean().alias("dec"),
                pl.col("fec").mean().alias("fec"),
            )
            .sort("cod_ibge")
        )


class FetcherAneelHTTP:
    """Fetcher real: baixa o CSV de DEC/FEC dos dados abertos da ANEEL.

    URL e parâmetros a confirmar na 1ª busca real (``dadosabertos.aneel.gov.br``).
    """

    BASE = "https://dadosabertos.aneel.gov.br/dataset/indicadores-qualidade-distribuicao-dec-fec"

    def baixar(self, janela: Janela) -> tuple[bytes, str]:  # pragma: no cover - rede
        import urllib.request

        url = f"{self.BASE}/resource/dec-fec-{janela.ano}.csv"
        with urllib.request.urlopen(url, timeout=120) as resp:  # noqa: S310  # nosec B310
            return resp.read(), url
