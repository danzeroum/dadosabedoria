"""Adaptador do INEP (Censo Escolar) — matrículas por município, domínio ``educacao``.

Bronze (parse): lê o CSV ``;``-delimitado dos microdados do Censo Escolar (nível escola) num
DataFrame Polars (tudo texto, ``utf8-lossy`` tolera o latin-1 da fonte — como CAGED/ESTBAN). Prata:
normaliza ``CO_MUNICIPIO`` (IBGE 7 díg.) e a contagem de matrículas. Ouro: soma por município.

Contrato de dados (ASSUNÇÕES a confirmar contra o arquivo real do INEP): o microdado de escolas traz
``CO_MUNICIPIO`` e ``QT_MAT_FUND`` (matrículas no ensino fundamental); o Censo Escolar é **anual**.
Fonte aberta, sem credencial. A carga em ``valor`` é feita pelo ``pipeline`` via ``escrever_ouro``.
"""

from __future__ import annotations

import io

import polars as pl

from app.ingestao.adaptadores.base import FetcherFonte, Janela
from app.ingestao.contratos import ContratoFonte

#: Indicador alimentado por este adaptador.
CODIGO_INDICADOR = "educacao.matriculas.fundamental"

COL_IBGE = "CO_MUNICIPIO"
COL_MATRICULAS = "QT_MAT_FUND"  # matrículas no ensino fundamental (nível escola)

#: Contrato do bruto INEP: o microdado precisa do município e da contagem de matrículas.
CONTRATO = ContratoFonte(
    fonte="inep",
    colunas_obrigatorias=frozenset({COL_IBGE, COL_MATRICULAS}),
)


class AdaptadorInep:
    """Padrão Adapter: isola o formato do Censo Escolar. Fetcher injetado (testável sem rede)."""

    codigo = "inep"

    def __init__(self, fetcher: FetcherFonte) -> None:
        self._fetcher = fetcher

    def baixar_bruto(self, janela: Janela) -> tuple[bytes, str]:
        return self._fetcher.baixar(janela)

    def parse(self, bruto: bytes) -> pl.DataFrame:
        # Tudo como texto no bronze (infer_schema_length=0); tipos vêm na prata. utf8-lossy tolera o
        # latin-1 dos microdados (só uso colunas numéricas, então acentos garbled não importam).
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
        CONTRATO.validar(df)  # borda bronze: falha claro se o layout do Censo Escolar mudar
        return df

    def transformar_prata(self, df: pl.DataFrame) -> pl.DataFrame:
        return df.select(
            pl.col(COL_IBGE).cast(pl.Utf8).str.strip_chars().alias("cod_ibge"),
            pl.col(COL_MATRICULAS).cast(pl.Int64, strict=False).alias("matriculas"),
        ).filter(
            pl.col("cod_ibge").is_not_null()
            & (pl.col("cod_ibge") != "")
            & pl.col("matriculas").is_not_null()
        )

    def agregar(self, df_prata: pl.DataFrame) -> pl.DataFrame:
        """Matrículas no fundamental por município (soma das escolas do município)."""
        return (
            df_prata.group_by("cod_ibge")
            .agg(pl.col("matriculas").sum().alias("matriculas"))
            .sort("cod_ibge")
        )


class FetcherInepHTTP:
    """Fetcher real: baixa o ZIP dos microdados do Censo Escolar do INEP e extrai o CSV de escolas.

    Não exercitado em teste (rede/zip); parse/transformação são cobertos por fixture.
    """

    BASE = "https://download.inep.gov.br/dados_abertos/microdados_censo_escolar"

    def baixar(self, janela: Janela) -> tuple[bytes, str]:  # pragma: no cover - rede/zip
        import urllib.request
        import zipfile

        # Censo Escolar é anual (an_censo = ano da janela). URL/nome do CSV a confirmar.
        url = f"{self.BASE}/microdados_censo_escolar_{janela.ano}.zip"
        with urllib.request.urlopen(url, timeout=120) as resp:  # noqa: S310  # nosec B310
            dados = resp.read()
        with zipfile.ZipFile(io.BytesIO(dados)) as z:
            nome = next(n for n in z.namelist() if n.lower().endswith(".csv"))
            return z.read(nome), url
