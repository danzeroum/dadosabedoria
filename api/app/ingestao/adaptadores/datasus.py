"""Adaptador do DATASUS/SIH — internações respiratórias por município/mês, domínio ``saude``.

Forma confirmada no ADR-0024 (2026-06-11, RDRO2604):
  - ``MUNIC_RES``: município de RESIDÊNCIA (6 dígitos DATASUS; mapa 6→7 no pipeline).
  - ``DIAG_PRINC``: diagnóstico principal (CID-10 J00–J99 = respiratório).
  - ``DT_INTER``: data de internação (YYYY-MM-DD após DBF→polars→CSV). Determina o mês do evento.
    **Não usar ANO_CMPT/MES_CMPT**: é competência de faturamento e mistura meses.

Prata: filtra DIAG_PRINC 'J%', deriva ``mes_internacao`` do 1.º dia do mês de DT_INTER.
Ouro: conta AIH por (município, mês) — a contagem é também o ``n_amostra`` da supressão k-anon.

Origem **sensível** (saúde): a contagem entra pelo caminho ouro, onde o k-anonimato com
``n_minimo=5`` suprime células abaixo do piso antes de gravar (ADR-0004).
"""

from __future__ import annotations

import io

import polars as pl

from app.ingestao.adaptadores.base import FetcherFonte, Janela
from app.ingestao.contratos import ContratoFonte

#: Indicador alimentado por este adaptador (origem sensível — k-anon no caminho ouro).
CODIGO_INDICADOR = "saude.resp.internacoes_j"

COL_MUNICIPIO = "MUNIC_RES"  # residência do paciente (NÃO MUNIC_MOV = local da internação)
COL_DIAG = "DIAG_PRINC"
COL_DATA = "DT_INTER"  # data de internação → mês do evento
GRUPO_RESPIRATORIO = "J"  # CID-10 J00–J99

#: Contrato do bruto SIH-RD: forma real confirmada no ADR-0024 (RDRO2604, 2026-06-11).
CONTRATO = ContratoFonte(
    fonte="datasus_sih",
    colunas_obrigatorias=frozenset({COL_MUNICIPIO, COL_DIAG, COL_DATA}),
)


class AdaptadorDatasus:
    """Padrão Adapter: isola o formato do SIH-RD. Fetcher injetado (testável sem rede)."""

    codigo = "datasus_sih"

    def __init__(self, fetcher: FetcherFonte) -> None:
        self._fetcher = fetcher

    def baixar_bruto(self, janela: Janela) -> tuple[bytes, str]:
        return self._fetcher.baixar(janela)

    def parse(self, bruto: bytes) -> pl.DataFrame:
        # Tudo como texto no bronze (infer_schema_length=0); a contagem vem no ouro.
        return pl.read_csv(io.BytesIO(bruto), infer_schema_length=0, ignore_errors=True)

    def extrair(self, janela: Janela) -> pl.DataFrame:
        bruto, _ = self.baixar_bruto(janela)
        df = self.parse(bruto)
        CONTRATO.validar(df)  # borda bronze: falha claro se o layout do SIH mudar
        return df

    def transformar_prata(self, df: pl.DataFrame) -> pl.DataFrame:
        # DT_INTER → "YYYY-MM-DD" após DBF→polars→CSV; slice primeiros 7 chars = "YYYY-MM".
        # Concatena "-01" para obter "YYYY-MM-01" e parseia como date (1.º dia do mês).
        return df.select(
            pl.col(COL_MUNICIPIO).cast(pl.Utf8).str.strip_chars().alias("cod_munres"),
            pl.col(COL_DIAG).cast(pl.Utf8).str.strip_chars().alias("diag"),
            pl.concat_str(
                pl.col(COL_DATA).cast(pl.Utf8).str.slice(0, 7),
                pl.lit("-01"),
            )
            .str.to_date(format="%Y-%m-%d", strict=False)
            .alias("mes_internacao"),
        ).filter(
            pl.col("cod_munres").is_not_null()
            & (pl.col("cod_munres") != "")
            & pl.col("diag").str.starts_with(GRUPO_RESPIRATORIO)
            & pl.col("mes_internacao").is_not_null()
        )

    def agregar(self, df_prata: pl.DataFrame) -> pl.DataFrame:
        """AIH respiratórias = contagem por (município, mês de internação) — o n_amostra."""
        return (
            df_prata.group_by("cod_munres", "mes_internacao")
            .agg(pl.len().alias("internacoes"))
            .sort("cod_munres", "mes_internacao")
        )


class FetcherDatasusFTP:
    """Fetcher real: baixa o RD<UF><AAMM>.dbc do FTP do DATASUS e decodifica DBC→tabular.

    Não exercitado em teste (rede/DBC); parse/transformação são cobertos por fixture.
    Decoder: datasus_dbc (Rust wheel) — ``decompress(src, dst)`` — + dbfread → polars.
    """

    HOST = "ftp.datasus.gov.br"
    CAMINHO = "/dissemin/publicos/SIHSUS/200801_/Dados/"
    UF = "SP"  # UF da extração (exemplo); a parametrizar quando o pipeline ligar

    def baixar(self, janela: Janela) -> tuple[bytes, str]:  # pragma: no cover - rede/dbc
        import ftplib  # nosec B402
        import os
        import tempfile

        from datasus_dbc import decompress
        from dbfread import DBF

        comp = f"{janela.ano % 100:02d}{janela.mes:02d}"
        nome = f"RD{self.UF}{comp}.dbc"
        url = f"ftp://{self.HOST}{self.CAMINHO}{nome}"
        fd, tmp_dbc = tempfile.mkstemp(suffix=".dbc")
        os.close(fd)
        tmp_dbf = tmp_dbc[:-4] + ".dbf"
        try:
            with ftplib.FTP(self.HOST, timeout=180) as ftp:  # noqa: S321  # nosec B321
                ftp.login()
                ftp.set_pasv(True)  # modo passivo obrigatório em containers (NAT/firewall)
                ftp.cwd(self.CAMINHO)
                with open(tmp_dbc, "wb") as f:
                    ftp.retrbinary(f"RETR {nome}", f.write)
            decompress(tmp_dbc, tmp_dbf)
            df = pl.DataFrame(list(DBF(tmp_dbf, encoding="latin-1")))
        finally:
            for p in (tmp_dbc, tmp_dbf):
                try:
                    os.unlink(p)
                except OSError:
                    pass
        return df.write_csv().encode("utf-8"), url
