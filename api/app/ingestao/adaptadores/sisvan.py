"""Adaptador SISVAN — estado nutricional de crianças < 5 anos e gestantes, domínio saúde.

Bronze: CSV individual de acompanhamento nutricional publicado pelo Ministério da Saúde.
URL pública: https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SISVAN/

Indicadores:
- ``baixo_peso_pct``: % de crianças < 5 anos com magreza ou magreza acentuada
  (CO_ESTADO_NUTRI_CRIANCA in [1, 2]) entre as acompanhadas no município.
- ``gestante_baixo_peso_pct``: % de gestantes com baixo peso (IMC pré-gestacional)
  (CO_ESTADO_NUTRI_GESTANTE = 1) entre as acompanhadas no município.

Prata: filtra crianças < 5 anos (NU_IDADE_ANO in [0,1,2,3,4]) com estado nutricional válido.
Ouro: % com baixo peso por município; n_amostra = total de crianças acompanhadas (k-anon n≥5).

ASSUNÇÕES a confirmar na 1ª busca real (#0, host s3.sa-east-1.amazonaws.com):
- CSV com separador ";", encoding UTF-8 ou latin-1.
- Colunas: CO_MUNICIPIO_IBGE (7 díg.), NU_IDADE_ANO (int), CO_ESTADO_NUTRI_CRIANCA (int 1–6).
- Código 1 = magreza acentuada, 2 = magreza, 3 = eutrofia, 4+ = sobrepeso/obesidade.
- Cobre apenas beneficiários acompanhados pelo SISVAN/CadÚnico — não é censo populacional.
"""

from __future__ import annotations

import io

import polars as pl

from app.ingestao.adaptadores.base import FetcherFonte, Janela
from app.ingestao.contratos import ContratoFonte

CODIGO_INDICADOR = "alimentacao.nutricao.baixo_peso_pct"

COL_IBGE = "CO_MUNICIPIO_IBGE"
COL_IDADE = "NU_IDADE_ANO"
COL_ESTADO = "CO_ESTADO_NUTRI_CRIANCA"

#: Códigos de baixo peso (magreza acentuada=1 e magreza=2).
_BAIXO_PESO = {1, 2}
#: Crianças < 5 anos (0, 1, 2, 3, 4 anos completos).
_IDADE_MAX = 5

CONTRATO = ContratoFonte(
    fonte="sisvan",
    colunas_obrigatorias=frozenset({COL_IBGE, COL_IDADE, COL_ESTADO}),
)


class AdaptadorSisvan:
    """Isola o formato do CSV SISVAN/MS. Fetcher injetado (testável sem rede)."""

    codigo = "sisvan"

    def __init__(self, fetcher: FetcherFonte) -> None:
        self._fetcher = fetcher

    def baixar_bruto(self, janela: Janela) -> tuple[bytes, str]:
        return self._fetcher.baixar(janela)

    def parse(self, bruto: bytes) -> pl.DataFrame:
        """CSV SISVAN → DataFrame com as 3 colunas de produto."""
        for enc in ("utf-8", "latin-1"):
            try:
                df = pl.read_csv(
                    io.BytesIO(bruto),
                    separator=";",
                    encoding=enc,
                    infer_schema_length=0,
                    ignore_errors=True,
                )
                if COL_IBGE in df.columns:
                    return df.select(
                        pl.col(COL_IBGE).cast(pl.Utf8),
                        pl.col(COL_IDADE).cast(pl.Utf8),
                        pl.col(COL_ESTADO).cast(pl.Utf8),
                    )
            except Exception:  # noqa: BLE001, S112  # nosec B112
                continue
        return pl.DataFrame(
            {
                COL_IBGE: pl.Series([], dtype=pl.Utf8),
                COL_IDADE: pl.Series([], dtype=pl.Utf8),
                COL_ESTADO: pl.Series([], dtype=pl.Utf8),
            }
        )

    def extrair(self, janela: Janela) -> pl.DataFrame:
        bruto, _ = self.baixar_bruto(janela)
        df = self.parse(bruto)
        CONTRATO.validar(df)
        return df

    def transformar_prata(self, df: pl.DataFrame) -> pl.DataFrame:
        """Filtra crianças < 5 anos com estado nutricional válido."""
        return (
            df.with_columns(
                pl.col(COL_IBGE).str.strip_chars().alias("cod_ibge"),
                pl.col(COL_IDADE).cast(pl.Int32, strict=False).alias("idade"),
                pl.col(COL_ESTADO).cast(pl.Int32, strict=False).alias("estado"),
            )
            .filter(
                pl.col("cod_ibge").is_not_null()
                & (pl.col("cod_ibge") != "")
                & pl.col("idade").is_not_null()
                & (pl.col("idade") < _IDADE_MAX)
                & pl.col("estado").is_not_null()
                & (pl.col("estado") >= 1)
                & (pl.col("estado") <= 6)
            )
            .select("cod_ibge", "estado")
        )

    def agregar(self, df_prata: pl.DataFrame) -> pl.DataFrame:
        """% de crianças < 5 com baixo peso por município; n = total acompanhado."""
        return (
            df_prata.with_columns(
                pl.col("estado").is_in(list(_BAIXO_PESO)).cast(pl.Int32).alias("baixo_peso")
            )
            .group_by("cod_ibge")
            .agg(
                pl.len().alias("n_total"),
                pl.col("baixo_peso").sum().alias("n_baixo_peso"),
            )
            .with_columns(
                (pl.col("n_baixo_peso").cast(pl.Float64) / pl.col("n_total") * 100.0).alias(
                    "baixo_peso_pct"
                )
            )
            .sort("cod_ibge")
        )


class FetcherSisvanHTTP:
    """Fetcher real: baixa o CSV de estado nutricional do bucket público do MS.

    Host bloqueado no contêiner (rede Custom) — exercitado apenas com rede aberta.
    """

    _BASE = "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SISVAN"

    def baixar(self, janela: Janela) -> tuple[bytes, str]:  # pragma: no cover - rede
        import urllib.request

        url = f"{self._BASE}/sisvan_estado_nutricional_{janela.ano}.csv"
        with urllib.request.urlopen(url, timeout=300) as resp:  # noqa: S310  # nosec B310
            return resp.read(), url


# ============================================================= Gestantes (SAUDE-03)

CODIGO_INDICADOR_GESTANTE = "saude.materno.gestante_baixo_peso_pct"

COL_PUBLICO = "CO_PUBLICO_ALVO"
COL_ESTADO_GESTANTE = "CO_ESTADO_NUTRI_GESTANTE"
_PUBLICO_GESTANTE = "GESTANTE"
_ESTADOS_VALIDOS_GESTANTE = {1, 2, 3, 4}
_BAIXO_PESO_GESTANTE = {1}

CONTRATO_GESTANTE = ContratoFonte(
    fonte="sisvan",
    colunas_obrigatorias=frozenset({COL_IBGE, COL_PUBLICO, COL_ESTADO_GESTANTE}),
)


class AdaptadorSisvanGestante:
    """Isola o formato do CSV SISVAN/MS para gestantes (SAUDE-03).

    Fetcher injetado (testável sem rede). O CSV de gestantes tem colunas diferentes do de crianças:
    CO_MUNICIPIO_IBGE, CO_PUBLICO_ALVO, CO_ESTADO_NUTRI_GESTANTE.

    ASSUNÇÕES a confirmar na 1ª busca real (#0, host s3.sa-east-1.amazonaws.com):
    - CO_ESTADO_NUTRI_GESTANTE: 1=baixo_peso, 2=adequado, 3=sobrepeso, 4=obesidade.
    - CO_PUBLICO_ALVO = 'GESTANTE' filtra apenas gestantes (arquivo pode conter outros públicos).
    """

    codigo = "sisvan_gestante"

    def __init__(self, fetcher: FetcherFonte) -> None:
        self._fetcher = fetcher

    def baixar_bruto(self, janela: Janela) -> tuple[bytes, str]:
        return self._fetcher.baixar(janela)

    def parse(self, bruto: bytes) -> pl.DataFrame:
        """CSV SISVAN gestante → DataFrame com as 3 colunas de produto."""
        for enc in ("utf-8", "latin-1"):
            try:
                df = pl.read_csv(
                    io.BytesIO(bruto),
                    separator=";",
                    encoding=enc,
                    infer_schema_length=0,
                    ignore_errors=True,
                )
                if COL_IBGE in df.columns and COL_ESTADO_GESTANTE in df.columns:
                    return df.select(
                        pl.col(COL_IBGE).cast(pl.Utf8),
                        pl.col(COL_PUBLICO).cast(pl.Utf8),
                        pl.col(COL_ESTADO_GESTANTE).cast(pl.Utf8),
                    )
            except Exception:  # noqa: BLE001, S112  # nosec B112
                continue
        return pl.DataFrame(
            {
                COL_IBGE: pl.Series([], dtype=pl.Utf8),
                COL_PUBLICO: pl.Series([], dtype=pl.Utf8),
                COL_ESTADO_GESTANTE: pl.Series([], dtype=pl.Utf8),
            }
        )

    def extrair(self, janela: Janela) -> pl.DataFrame:
        bruto, _ = self.baixar_bruto(janela)
        df = self.parse(bruto)
        CONTRATO_GESTANTE.validar(df)
        return df

    def transformar_prata(self, df: pl.DataFrame) -> pl.DataFrame:
        """Filtra gestantes com estado nutricional válido (1–4)."""
        return (
            df.with_columns(
                pl.col(COL_IBGE).str.strip_chars().alias("cod_ibge"),
                pl.col(COL_PUBLICO).str.strip_chars().alias("publico"),
                pl.col(COL_ESTADO_GESTANTE).cast(pl.Int32, strict=False).alias("estado"),
            )
            .filter(
                pl.col("cod_ibge").is_not_null()
                & (pl.col("cod_ibge") != "")
                & (pl.col("publico") == _PUBLICO_GESTANTE)
                & pl.col("estado").is_not_null()
                & pl.col("estado").is_in(list(_ESTADOS_VALIDOS_GESTANTE))
            )
            .select("cod_ibge", "estado")
        )

    def agregar(self, df_prata: pl.DataFrame) -> pl.DataFrame:
        """% de gestantes com baixo peso por município; n = total acompanhado."""
        return (
            df_prata.with_columns(
                pl.col("estado")
                .is_in(list(_BAIXO_PESO_GESTANTE))
                .cast(pl.Int32)
                .alias("baixo_peso")
            )
            .group_by("cod_ibge")
            .agg(
                pl.len().alias("n_total"),
                pl.col("baixo_peso").sum().alias("n_baixo_peso"),
            )
            .with_columns(
                (pl.col("n_baixo_peso").cast(pl.Float64) / pl.col("n_total") * 100.0).alias(
                    "gestante_baixo_peso_pct"
                )
            )
            .sort("cod_ibge")
        )


class FetcherSisvanGestanteHTTP:
    """Fetcher real — forma a confirmar na 1ª busca real (#0, host s3.sa-east-1.amazonaws.com)."""

    _BASE = "https://s3.sa-east-1.amazonaws.com/ckan.saude.gov.br/SISVAN"

    def baixar(self, janela: Janela) -> tuple[bytes, str]:  # pragma: no cover - rede
        import urllib.request

        url = f"{self._BASE}/sisvan_estado_nutricional_gestante_{janela.ano}.csv"
        with urllib.request.urlopen(url, timeout=300) as resp:  # noqa: S310  # nosec B310
            return resp.read(), url
