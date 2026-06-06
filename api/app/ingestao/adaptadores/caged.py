"""Adaptador do Novo CAGED (MTE/PDET) — saldo de emprego formal por município/mês.

Bronze (extrair/parse): lê o arquivo CAGEDMOV (texto ``;``-delimitado) em um DataFrame Polars.
Prata (transformar_prata): normaliza colunas/tipos e filtra linhas inválidas.
Ouro (agregar_saldo): soma ``saldomovimentação`` (+1 admissão / -1 desligamento) por município.

A carga em ``valor`` é feita pelo ``app.ingestao.pipeline`` via ``escrever_ouro`` (regra única de
supressão + linhagem) — este adaptador não escreve no banco.
"""

from __future__ import annotations

import io

import polars as pl

from app.ingestao.adaptadores.base import FetcherFonte, Janela
from app.ingestao.contratos import ContratoFonte

#: Código do indicador alimentado por este adaptador.
CODIGO_INDICADOR = "trabalho.emprego.saldo_caged"

# Nomes de coluna do layout CAGEDMOV (Novo CAGED).
COL_COMPETENCIA = "competênciamov"
COL_MUNICIPIO = "município"
COL_SALDO = "saldomovimentação"

#: Contrato de dados do bruto CAGEDMOV — checado na borda bronze (extrair).
CONTRATO = ContratoFonte(
    fonte="caged",
    colunas_obrigatorias=frozenset({COL_COMPETENCIA, COL_MUNICIPIO, COL_SALDO}),
)


class AdaptadorCaged:
    """Padrão Adapter: isola o formato do CAGED. Fetcher injetado (testável sem rede)."""

    codigo = "caged"

    def __init__(self, fetcher: FetcherFonte) -> None:
        self._fetcher = fetcher

    def baixar_bruto(self, janela: Janela) -> tuple[bytes, str]:
        return self._fetcher.baixar(janela)

    def parse(self, bruto: bytes) -> pl.DataFrame:
        # Tudo como texto no bronze (infer_schema_length=0); tipos vêm na prata.
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
        CONTRATO.validar(df)  # borda bronze: falha claro se o layout do CAGED mudar
        return df

    def transformar_prata(self, df: pl.DataFrame) -> pl.DataFrame:
        return df.select(
            pl.col(COL_COMPETENCIA).cast(pl.Utf8).str.strip_chars().alias("competencia"),
            pl.col(COL_MUNICIPIO).cast(pl.Utf8).str.strip_chars().alias("municipio"),
            pl.col(COL_SALDO).cast(pl.Int64, strict=False).alias("saldo_mov"),
        ).filter(
            pl.col("municipio").is_not_null()
            & (pl.col("municipio") != "")
            & pl.col("saldo_mov").is_not_null()
        )

    def agregar_saldo(self, df_prata: pl.DataFrame) -> pl.DataFrame:
        """Saldo = soma das movimentações por município (admissões − desligamentos)."""
        return (
            df_prata.group_by("municipio")
            .agg(pl.col("saldo_mov").sum().alias("saldo"))
            .sort("municipio")
        )


class FetcherCagedFTP:
    """Fetcher real: baixa o CAGEDMOV<competência>.7z do FTP do PDET e descompacta.

    Não exercitado em teste (rede + 7z); a lógica de parse/transformação é testada com fixture.
    """

    HOST = "ftp.mtps.gov.br"

    def baixar(self, janela: Janela) -> tuple[bytes, str]:  # pragma: no cover - rede/7z
        # FTP é o canal oficial mandatório do PDET para o CAGED (dado aberto, login anônimo);
        # não há dado sensível nem credencial em trânsito — daí as supressões abaixo.
        import ftplib  # nosec B402

        import py7zr

        comp = janela.competencia
        caminho = f"/pdet/microdados/NOVO CAGED/{janela.ano}/{comp}/"
        nome = f"CAGEDMOV{comp}.7z"
        url = f"ftp://{self.HOST}{caminho}{nome}"

        buf = io.BytesIO()
        with ftplib.FTP(self.HOST, timeout=120) as ftp:  # noqa: S321  # nosec B321
            ftp.login()
            ftp.cwd(caminho)
            ftp.retrbinary(f"RETR {nome}", buf.write)
        buf.seek(0)
        with py7zr.SevenZipFile(buf, mode="r") as z:
            conteudo = z.readall()
        dados = next(iter(conteudo.values())).read()
        return dados, url
