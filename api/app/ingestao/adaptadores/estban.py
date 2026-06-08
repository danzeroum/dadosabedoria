"""Adaptador do BCB/ESTBAN — saldo de operações de crédito por município/mês.

Bronze (parse): lê o CSV ESTBAN municipal (``;``-delimitado). Prata: normaliza CODMUN e o valor da
coluna de crédito (verbete 160 — "Operações de Crédito"). Ouro: soma por município.

Contrato de dados (assunção a confirmar contra arquivo real — ADR-0007): CODMUN é o IBGE de 7
dígitos; o valor do verbete está em **R$ mil** → convertido para reais (×1000).
"""

from __future__ import annotations

import io

import polars as pl

from app.ingestao.adaptadores.base import FetcherFonte, Janela
from app.ingestao.contratos import ContratoFonte

#: Indicador alimentado por este adaptador.
CODIGO_INDICADOR = "credito.operacoes.saldo_total"

COL_CODMUN = "CODMUN"
PADRAO_VERBETE_CREDITO = "160"  # verbete 160 = Operações de Crédito
ESCALA_REAIS = 1000  # ESTBAN em R$ mil → reais

#: Contrato do bruto ESTBAN: CODMUN + ao menos uma coluna do verbete de crédito (dinâmica).
CONTRATO = ContratoFonte(
    fonte="estban",
    colunas_obrigatorias=frozenset({COL_CODMUN}),
    coluna_contendo=PADRAO_VERBETE_CREDITO,
)


class AdaptadorEstban:
    codigo = "estban"

    def __init__(self, fetcher: FetcherFonte, *, skip_rows: int = 0) -> None:
        self._fetcher = fetcher
        self._skip_rows = skip_rows  # arquivos reais têm preâmbulo; fixture não

    def baixar_bruto(self, janela: Janela) -> tuple[bytes, str]:
        return self._fetcher.baixar(janela)

    def parse(self, bruto: bytes) -> pl.DataFrame:
        return pl.read_csv(
            io.BytesIO(bruto),
            separator=";",
            encoding="utf8-lossy",
            infer_schema_length=0,
            skip_rows=self._skip_rows,
            ignore_errors=True,
        )

    def extrair(self, janela: Janela) -> pl.DataFrame:
        bruto, _ = self.baixar_bruto(janela)
        df = self.parse(bruto)
        CONTRATO.validar(df)  # borda bronze: falha claro se o layout do ESTBAN mudar
        return df

    def _coluna_credito(self, df: pl.DataFrame) -> str:
        for nome in df.columns:
            if PADRAO_VERBETE_CREDITO in nome:
                return nome
        raise ValueError("coluna de operações de crédito (verbete 160) não encontrada no ESTBAN")

    def transformar_prata(self, df: pl.DataFrame) -> pl.DataFrame:
        col = self._coluna_credito(df)
        return df.select(
            pl.col(COL_CODMUN).cast(pl.Utf8).str.strip_chars().alias("codmun"),
            # R$ no formato brasileiro: remove separador de milhar (.) e troca vírgula decimal.
            pl.col(col)
            .cast(pl.Utf8)
            .str.replace_all(".", "", literal=True)
            .str.replace(",", ".")
            .cast(pl.Float64, strict=False)
            .alias("credito"),
        ).filter(
            pl.col("codmun").is_not_null()
            & (pl.col("codmun") != "")
            & pl.col("credito").is_not_null()
        )

    def agregar_credito(self, df_prata: pl.DataFrame) -> pl.DataFrame:
        return (
            df_prata.group_by("codmun")
            .agg((pl.col("credito").sum() * ESCALA_REAIS).alias("saldo"))
            .sort("codmun")
        )


class FetcherEstbanHTTP:  # pragma: no cover - rede/zip
    """Fetcher real: baixa o ZIP do ESTBAN municipal do BCB e extrai o CSV.

    **#0 (2026-06-08):** ``www.bcb.gov.br`` e ``dadosabertos.bcb.gov.br`` estão **abertos** (200).
    O antigo ``www4.bcb.gov.br`` dá 404. O BCB migrou para um portal Angular (SPA) — todos os
    caminhos estáticos retornam HTML. A URL binária do ZIP precisa ser descoberta via API backend
    do BCB (``/api/servico/sitebcb/estban/…``) — investigação pendente (ver Lista de desbloqueio).
    Parse/agregação cobertos por fixture até a URL ser confirmada.
    """

    BASE = "https://www.bcb.gov.br/estabilidadefinanceira/docs/estban"

    def baixar(self, janela: Janela) -> tuple[bytes, str]:
        import urllib.request
        import zipfile

        comp = janela.competencia
        # URL a confirmar: o portal BCB migrou de www4 para www.bcb.gov.br (SPA Angular).
        # Tentar o padrão do portal novo — se retornar HTML (SPA) levantar ValueError informativo.
        url = f"{self.BASE}/ESTBAN_MUNICIPIO_{comp}.ZIP"
        with urllib.request.urlopen(url, timeout=120) as resp:  # noqa: S310  # nosec B310
            dados = resp.read()
        if dados[:5] == b"<!doc" or dados[:5] == b"<?xml":  # SPA ou página de erro
            raise ValueError(
                f"BCB ESTBAN: URL {url!r} retornou HTML (SPA Angular). "
                "A URL binária do ZIP precisa ser atualizada — ver List de desbloqueio."
            )
        with zipfile.ZipFile(io.BytesIO(dados)) as z:
            conteudo = z.read(z.namelist()[0])
        return conteudo, url
