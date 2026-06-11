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

    **#0 (2026-06-08):** ``www.bcb.gov.br`` está acessível mas migrou para SPA Angular —
    caminhos estáticos retornam HTML. A URL binária do ZIP deve ser confirmada via
    ``scripts/diagnostico_estban.py`` (sonda múltiplos padrões com headers de browser).
    Até lá, o parse/agregação estão cobertos pela fixture.

    **Como desblocar:**
    1. No VPS com rede aberta, rode:
       ``docker compose --profile ingestion run --rm worker python scripts/diagnostico_estban.py``
    2. O script imprime a URL que funciona e salva a fixture real.
    3. Atualize ``BASE`` abaixo com a URL encontrada e abra PR.
    """

    BASE = "https://www.bcb.gov.br/estabilidadefinanceira/docs/estban"

    _HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
        ),
        "Accept": "application/octet-stream,application/zip,*/*",
        "Accept-Language": "pt-BR,pt;q=0.9",
        "Referer": "https://www.bcb.gov.br/estabilidadefinanceira/estatisticabancariamunicipios",
    }

    def baixar(self, janela: Janela) -> tuple[bytes, str]:
        import zipfile

        import httpx

        comp = janela.competencia
        url = f"{self.BASE}/ESTBAN_MUNICIPIO_{comp}.ZIP"
        resp = httpx.get(url, headers=self._HEADERS, timeout=120, follow_redirects=True)
        resp.raise_for_status()
        dados = resp.content
        if dados[:2] != b"PK":  # assinatura ZIP (PK magic bytes)
            raise ValueError(
                f"BCB ESTBAN: URL {url!r} retornou conteúdo não-ZIP "
                f"({dados[:80]!r}). "
                "Execute scripts/diagnostico_estban.py no VPS para encontrar a URL correta."
            )
        with zipfile.ZipFile(io.BytesIO(dados)) as z:
            conteudo = z.read(z.namelist()[0])
        return conteudo, url
