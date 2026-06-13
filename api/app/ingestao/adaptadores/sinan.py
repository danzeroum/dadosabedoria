"""Adaptador SINAN — casos confirmados de dengue por município/ano, domínio ``saude``.

SINAN (Sistema de Informação de Agravos de Notificação) — dengue:
  - Arquivo: ``DENGBR{YY}.dbc`` no FTP do DATASUS.
  - Forma (ASSUNÇÃO — confirmar na 1ª busca real via #0):
      - ``ID_MUNICIP``: município de residência do paciente (IBGE 6 dígitos).
      - ``NU_ANO``: ano de notificação.
      - ``CLASSI_FIN``: classificação final:
          1=Dengue clássica, 2=Dengue com sinais de alarme, 3=Dengue grave,
          5=Descartado, 8=Inconclusivo.
          Confirmados: CLASSI_FIN ∈ {1, 2, 3}.

Prata: filtra linhas com CLASSI_FIN ∈ {1, 2, 3} e ID_MUNICIP não-nulo/vazio.
Ouro: contagem de casos por (cod_mun6, ano) — o n_amostra (k-anon n_minimo=5, saúde sensível).

Origem **SENSÍVEL** (saúde, ADR-0004): a contagem é o n_amostra → k-anonimato suprime células
abaixo de 5 casos antes de gravar. Campos além dos três de produto (ID_MUNICIP/NU_ANO/CLASSI_FIN)
são descartados imediatamente para não persistir quasi-identificadores.

FTP: ``ftp.datasus.gov.br/dissemin/publicos/SINAN/DADOS/FINAIS/DENGBR{YY}.dbc``
Vivo-pronto: forma a confirmar na 1ª busca real (#0, host ftp.datasus.gov.br).
"""

from __future__ import annotations

import io
import logging

import polars as pl

from app.ingestao.adaptadores.base import FetcherFonte, Janela
from app.ingestao.contratos import ContratoFonte

logger = logging.getLogger(__name__)

#: Indicador alimentado por este adaptador (origem sensível — k-anon no caminho ouro).
CODIGO_INDICADOR = "saude.arboviroses.dengue_casos"

COL_MUNICIPIO = "ID_MUNICIP"  # município de residência (IBGE 6 dígitos)
COL_ANO = "NU_ANO"  # ano de notificação
COL_CLASSI = "CLASSI_FIN"  # classificação final: 1=clássica,2=alarme,3=grave,5=desc.,8=inconcl.

#: Classificações confirmadas de dengue (CLASSI_FIN ∈ {1, 2, 3}).
_CLASSI_CONFIRMADA = {1, 2, 3}

#: Contrato do bruto SINAN-Dengue (ASSUNÇÃO — confirmar na 1ª busca real).
CONTRATO = ContratoFonte(
    fonte="sinan",
    colunas_obrigatorias=frozenset({COL_MUNICIPIO, COL_ANO, COL_CLASSI}),
)


class AdaptadorSinan:
    """Isola o formato do SINAN-Dengue. Fetcher injetado (testável sem rede).

    Apenas as 3 colunas de produto (ID_MUNICIP, NU_ANO, CLASSI_FIN) são mantidas após o parse;
    todos os demais campos — incluindo quasi-identificadores de pacientes — são descartados
    imediatamente (ADR-0004).
    """

    codigo = "sinan"

    def __init__(self, fetcher: FetcherFonte) -> None:
        self._fetcher = fetcher

    def baixar_bruto(self, janela: Janela) -> tuple[bytes, str]:
        return self._fetcher.baixar(janela)

    def parse(self, bruto: bytes) -> pl.DataFrame:
        """CSV SINAN-Dengue → DataFrame com apenas as 3 colunas de produto (string).

        Todas as colunas além de ID_MUNICIP/NU_ANO/CLASSI_FIN são descartadas aqui —
        não persistir quasi-identificadores de notificação de doença (ADR-0004).
        """
        df = pl.read_csv(io.BytesIO(bruto), infer_schema_length=0, ignore_errors=True)
        # Normalizar nomes para UPPERCASE (alguns decoders DBF retornam minúsculas).
        df = df.rename({c: c.strip().upper() for c in df.columns})
        cols = [c for c in (COL_MUNICIPIO, COL_ANO, COL_CLASSI) if c in df.columns]
        return df.select(pl.col(c).cast(pl.Utf8) for c in cols)

    def extrair(self, janela: Janela) -> pl.DataFrame:
        bruto, _ = self.baixar_bruto(janela)
        df = self.parse(bruto)
        CONTRATO.validar(df)
        return df

    def transformar_prata(self, df: pl.DataFrame) -> pl.DataFrame:
        """Filtra casos confirmados (CLASSI_FIN ∈ {1,2,3}) com município válido.

        ID_MUNICIP: código IBGE 6 dígitos (ex.: "355030" = São Paulo).
        Triple-cast Float64→Int64→Utf8 para normalizar "355030.0" → "355030" em DBFs numéricos.
        NU_ANO: cast para Int32; CLASSI_FIN: cast para Int32 para filtragem.
        """
        return (
            df.with_columns(
                pl.col(COL_MUNICIPIO)
                .cast(pl.Float64, strict=False)
                .cast(pl.Int64, strict=False)
                .cast(pl.Utf8)
                .str.strip_chars()
                .alias("cod_mun6"),
                pl.col(COL_ANO).cast(pl.Int32, strict=False).alias("ano"),
                pl.col(COL_CLASSI).cast(pl.Int32, strict=False).alias("classi"),
            )
            .filter(
                pl.col("cod_mun6").is_not_null()
                & (pl.col("cod_mun6") != "")
                & pl.col("classi").is_not_null()
                & pl.col("classi").is_in(list(_CLASSI_CONFIRMADA))
                & pl.col("ano").is_not_null()
            )
            .select("cod_mun6", "ano")
        )

    def agregar(self, df_prata: pl.DataFrame) -> pl.DataFrame:
        """Conta casos confirmados por (município, ano) — o n_amostra."""
        return (
            df_prata.group_by("cod_mun6", "ano")
            .agg(pl.len().alias("casos"))
            .sort("cod_mun6", "ano")
        )


class FetcherSinanFTP:
    """Fetcher real: baixa DENGBR{YY}.dbc do FTP do DATASUS e converte para CSV.

    Host bloqueado no contêiner (rede Custom) — exercitado apenas com rede aberta.
    Decoder: ``datasus_dbc.decompress`` (Rust wheel) + dbfread → polars.
    """

    HOST = "ftp.datasus.gov.br"
    CAMINHO = "/dissemin/publicos/SINAN/DADOS/FINAIS/"

    def baixar(self, janela: Janela) -> tuple[bytes, str]:  # pragma: no cover - rede/dbc
        import ftplib  # nosec B402
        import os
        import tempfile

        from datasus_dbc import decompress
        from dbfread import DBF

        yy = f"{janela.ano % 100:02d}"
        nome = f"DENGBR{yy}.dbc"
        fd, tmp_dbc = tempfile.mkstemp(suffix=".dbc")
        os.close(fd)
        tmp_dbf = tmp_dbc[:-4] + ".dbf"
        try:
            with ftplib.FTP(self.HOST, timeout=300) as ftp:  # noqa: S321  # nosec B321
                ftp.login()
                ftp.set_pasv(True)
                ftp.cwd(self.CAMINHO)
                with open(tmp_dbc, "wb") as f:
                    ftp.retrbinary(f"RETR {nome}", f.write)
            decompress(tmp_dbc, tmp_dbf)
            raw = pl.DataFrame(list(DBF(tmp_dbf, encoding="latin-1")))
        finally:
            for p in (tmp_dbc, tmp_dbf):
                try:
                    os.unlink(p)
                except OSError:
                    pass

        # Normalizar nomes de coluna UPPERCASE.
        raw = raw.rename({c: c.strip().upper() for c in raw.columns})

        # Descartar TUDO exceto as 3 colunas de produto — não persistir campos de notificação.
        cols = [c for c in (COL_MUNICIPIO, COL_ANO, COL_CLASSI) if c in raw.columns]

        def _cast_col(c: str) -> pl.Expr:
            dtype = raw.schema[c]
            if dtype in (pl.Float32, pl.Float64):
                return pl.col(c).cast(pl.Int64, strict=False).cast(pl.Utf8).alias(c)
            return pl.col(c).cast(pl.Utf8).alias(c)

        raw = raw.select(_cast_col(c) for c in cols)

        logger.info(
            "SINAN DENGBR%s: %d linhas, cols=%s",
            yy,
            raw.height,
            raw.columns,
        )

        url = f"ftp://{self.HOST}{self.CAMINHO}{nome}"
        return raw.write_csv().encode("utf-8"), url
