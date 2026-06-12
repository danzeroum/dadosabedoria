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

Pipeline nacional: ``FetcherDatasusFTP.baixar()`` baixa as 27 UFs sequencialmente e concatena.
Política de falha (ADR-0024 §grain-v2):
  - Erro **transitório** (conexão/timeout): aborta antes de gravar — sem subcontagem.
  - Erro **550/arquivo-não-encontrado**: UF ainda não publicou a competência; NÃO é subcontagem
    (via MUNIC_RES a única perda seria residente da UF ausente internado nela mesma — desprezível
    para AC/RR). Ingere as UFs disponíveis; registra as ausentes na proveniência; NÃO faz retry.
"""

from __future__ import annotations

import io
import logging

import polars as pl

from app.ingestao.adaptadores.base import FetcherFonte, Janela
from app.ingestao.contratos import ContratoFonte

logger = logging.getLogger(__name__)

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

#: Colunas selecionadas do RD antes de concatenar as 27 UFs — os ~108 campos restantes
#: (incluindo CPF_AUT, GESTOR_CPF, NASC etc.) são descartados imediatamente para economizar
#: memória e não persistir quasi-identificadores no bronze.
_COLUNAS_PRODUTO = (COL_MUNICIPIO, "MUNIC_MOV", COL_DIAG, COL_DATA, "ANO_CMPT", "MES_CMPT")


class UFNaoPublicadaError(Exception):
    """UF retornou 550 file-not-found: competência ainda não publicada no FTP do DATASUS.

    Não é erro transitório — retry é inútil. Ingere as demais UFs disponíveis.
    """


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
    """Fetcher nacional: baixa RD<UF><AAMM>.dbc das 27 UFs sequencialmente e concatena.

    Não exercitado em teste (rede/DBC); parse/transformação são cobertos por fixture.
    Decoder: ``datasus_dbc.decompress`` (Rust wheel) + dbfread → polars.

    Política de falha (ADR-0024 §grain-v2):
      - Erro transitório (conexão/timeout/etc.): aborta, lança RuntimeError — sem subcontagem.
      - 550 file-not-found (UFNaoPublicadaError): competência não publicada pela UF; ingere as
        demais e registra as ausentes na string de proveniência. NÃO faz retry (550 é permanente
        até a UF publicar). A mensagem orienta a usar competência anterior ou aguardar.
    Apenas as colunas de produto são mantidas em memória (os ~108 campos restantes, incluindo
    quasi-identificadores CPF_AUT/GESTOR_CPF/NASC, são descartados na hora — ADR-0004).
    """

    HOST = "ftp.datasus.gov.br"
    CAMINHO = "/dissemin/publicos/SIHSUS/200801_/Dados/"

    #: 27 UFs do Brasil (ordem alfabética; DF incluído).
    UFS_BR: tuple[str, ...] = (
        "AC",
        "AL",
        "AP",
        "AM",
        "BA",
        "CE",
        "DF",
        "ES",
        "GO",
        "MA",
        "MT",
        "MS",
        "MG",
        "PA",
        "PB",
        "PR",
        "PE",
        "PI",
        "RJ",
        "RN",
        "RS",
        "RO",
        "RR",
        "SC",
        "SP",
        "SE",
        "TO",
    )

    def baixar(self, janela: Janela) -> tuple[bytes, str]:  # pragma: no cover - rede/dbc
        import ftplib  # nosec B402
        import os
        import tempfile

        from datasus_dbc import decompress
        from dbfread import DBF

        comp = f"{janela.ano % 100:02d}{janela.mes:02d}"

        def _baixar_uf(uf: str) -> pl.DataFrame:
            """Download + decode de uma UF; retorna apenas as colunas do produto (string).

            Lança UFNaoPublicadaError se o FTP retornar 550 (arquivo inexistente).
            Qualquer outro erro propaga como exceção transitória.
            """
            nome = f"RD{uf}{comp}.dbc"
            fd, tmp_dbc = tempfile.mkstemp(suffix=".dbc")
            os.close(fd)
            tmp_dbf = tmp_dbc[:-4] + ".dbf"
            try:
                with ftplib.FTP(self.HOST, timeout=180) as ftp:  # noqa: S321  # nosec B321
                    ftp.login()
                    ftp.set_pasv(True)
                    ftp.cwd(self.CAMINHO)
                    try:
                        with open(tmp_dbc, "wb") as f:
                            ftp.retrbinary(f"RETR {nome}", f.write)
                    except ftplib.error_perm as exc:
                        if "550" in str(exc):
                            raise UFNaoPublicadaError(uf) from exc
                        raise
                decompress(tmp_dbc, tmp_dbf)
                raw = pl.DataFrame(list(DBF(tmp_dbf, encoding="latin-1")))
            finally:
                for p in (tmp_dbc, tmp_dbf):
                    try:
                        os.unlink(p)
                    except OSError:
                        pass
            # Descartar todos os campos além das 6 colunas do produto imediatamente.
            cols = [c for c in _COLUNAS_PRODUTO if c in raw.columns]
            return raw.select(pl.col(c).cast(pl.Utf8) for c in cols)

        frames: list[pl.DataFrame] = []
        ufs_ausentes: list[str] = []  # 550: competência não publicada — não é subcontagem
        ufs_falha: list[str] = []  # erro transitório: aborta tudo
        for uf in self.UFS_BR:
            try:
                frames.append(_baixar_uf(uf))
            except UFNaoPublicadaError:
                ufs_ausentes.append(uf)
            except Exception as exc:  # noqa: BLE001
                ufs_falha.append(f"{uf}({exc!s:.80})")

        if ufs_falha:
            raise RuntimeError(
                f"DATASUS {comp}: {len(ufs_falha)} UF(s) com erro transitório — "
                f"abortando para evitar subcontagem (ADR-0024); verifique conexão: "
                f"{'; '.join(ufs_falha)}"
            )

        if not frames:
            raise RuntimeError(
                f"DATASUS {comp}: nenhuma UF disponível no FTP — todas as UFs retornaram 550. "
                f"Competência provavelmente ainda não publicada: {', '.join(ufs_ausentes)}. "
                f"Use a competência anterior ou aguarde a publicação."
            )

        if ufs_ausentes:
            logger.warning(
                "DATASUS %s: %d UF(s) ainda não publicaram esta competência (550): %s. "
                "Ingerindo as %d UFs disponíveis (ADR-0024 §grain-v2).",
                comp,
                len(ufs_ausentes),
                ", ".join(ufs_ausentes),
                len(frames),
            )

        df_nacional = pl.concat(frames, how="diagonal_relaxed")
        ausentes_nota = (
            f"; UFs ainda não publicadas: {', '.join(ufs_ausentes)}" if ufs_ausentes else ""
        )
        url = (
            f"ftp://{self.HOST}{self.CAMINHO}RD*{comp}.dbc "
            f"({len(frames)}/{len(self.UFS_BR)} UFs{ausentes_nota})"
        )
        return df_nacional.write_csv().encode("utf-8"), url
