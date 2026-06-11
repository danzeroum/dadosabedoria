"""Adaptador do DATASUS/SIH — internações respiratórias por município, domínio ``saude``.

Bronze (parse): lê o tabular do SIH-RD (uma linha por AIH) num DataFrame Polars. Prata: filtra o
diagnóstico principal do grupo J (CID-10 respiratório) e normaliza ``MUNIC_RES`` (IBGE de 6 dígitos
do DATASUS). Ouro: conta as AIH por município — a contagem é também o ``n_amostra`` da supressão.

Origem **sensível** (saúde): a contagem entra pelo caminho ouro, onde a regra de k-anonimato suprime
células abaixo do piso (ADR-0004). Contrato (ASSUNÇÕES a confirmar contra o RD real do SIH): o
arquivo traz ``MUNIC_RES`` e ``DIAG_PRINC``. Fonte aberta (dado já anonimizado), sem credencial.
O IBGE do SIH tem 6 dígitos (sem dígito verificador); o mapa 6→7 é responsabilidade do pipeline.
"""

from __future__ import annotations

import io

import polars as pl

from app.ingestao.adaptadores.base import FetcherFonte, Janela
from app.ingestao.contratos import ContratoFonte

#: Indicador alimentado por este adaptador (origem sensível — k-anon no caminho ouro).
CODIGO_INDICADOR = "saude.resp.internacoes_j"

COL_MUNICIPIO = "MUNIC_RES"
COL_DIAG = "DIAG_PRINC"
GRUPO_RESPIRATORIO = "J"  # CID-10 J00–J99 (doenças do aparelho respiratório)

#: Contrato do bruto SIH-RD: cada AIH precisa do município de residência e do diagnóstico principal.
CONTRATO = ContratoFonte(
    fonte="datasus_sih",
    colunas_obrigatorias=frozenset({COL_MUNICIPIO, COL_DIAG}),
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
        return df.select(
            pl.col(COL_MUNICIPIO).cast(pl.Utf8).str.strip_chars().alias("cod_munres"),
            pl.col(COL_DIAG).cast(pl.Utf8).str.strip_chars().alias("diag"),
        ).filter(
            pl.col("cod_munres").is_not_null()
            & (pl.col("cod_munres") != "")
            & pl.col("diag").str.starts_with(GRUPO_RESPIRATORIO)
        )

    def agregar(self, df_prata: pl.DataFrame) -> pl.DataFrame:
        """Internações respiratórias = contagem de AIH (grupo J) por município (= n_amostra)."""
        return df_prata.group_by("cod_munres").agg(pl.len().alias("internacoes")).sort("cod_munres")


class FetcherDatasusFTP:
    """Fetcher real: baixa o RD<UF><AAMM>.dbc do FTP do DATASUS e decodifica DBC→tabular.

    Não exercitado em teste (rede/DBC); parse/transformação são cobertos por fixture.
    Decoder: datasus_dbc (Rust wheel, sem pyarrow) + dbfread → polars.
    """

    HOST = "ftp.datasus.gov.br"
    CAMINHO = "/dissemin/publicos/SIHSUS/200801_/Dados/"
    UF = "SP"  # UF da extração (exemplo); a parametrizar quando o pipeline ligar

    def baixar(self, janela: Janela) -> tuple[bytes, str]:  # pragma: no cover - rede/dbc
        import ftplib  # nosec B402
        import os
        import tempfile

        from datasus_dbc import expand_dbc_to_dbf  # type: ignore[attr-defined]
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
            expand_dbc_to_dbf(tmp_dbc, tmp_dbf)
            df = pl.DataFrame(list(DBF(tmp_dbf, encoding="latin-1")))
        finally:
            for p in (tmp_dbc, tmp_dbf):
                try:
                    os.unlink(p)
                except OSError:
                    pass
        return df.write_csv().encode("utf-8"), url
