"""Adaptador do PNCP — valor de contratos públicos por município, domínio ``compras``.

Bronze (parse): lê o JSON da API de consulta do PNCP (lista ``data``) num DataFrame Polars; o
município vem **aninhado** em ``unidadeOrgao.codigoIbge`` (Struct). Prata: extrai o IBGE aninhado e
normaliza o ``valorGlobal``. Ouro: soma o valor dos contratos por município.

Contrato de dados (ASSUNÇÕES a confirmar contra a API real do PNCP): a consulta de contratos é
paginada (lista ``data``); cada item traz ``valorGlobal`` e ``unidadeOrgao`` (com ``codigoIbge`` de
7 dígitos). Fonte aberta, sem credencial. A carga em ``valor`` é feita pelo ``pipeline`` via
``escrever_ouro``.
"""

from __future__ import annotations

import json

import polars as pl

from app.ingestao.adaptadores.base import FetcherFonte, Janela
from app.ingestao.contratos import ContratoFonte

#: Indicador alimentado por este adaptador.
CODIGO_INDICADOR = "compras.contratos.valor_total"

COL_VALOR = "valorGlobal"
COL_UNIDADE = "unidadeOrgao"  # struct aninhado com o IBGE do órgão contratante
COL_IBGE_ANINHADO = "codigoIbge"

#: Contrato do bruto PNCP: cada contrato precisa do valor e da unidade (que carrega o município).
CONTRATO = ContratoFonte(
    fonte="pncp",
    colunas_obrigatorias=frozenset({COL_VALOR, COL_UNIDADE}),
)


class AdaptadorPncp:
    """Padrão Adapter: isola o formato do PNCP. Fetcher injetado (testável sem rede)."""

    codigo = "pncp"

    def __init__(self, fetcher: FetcherFonte) -> None:
        self._fetcher = fetcher

    def baixar_bruto(self, janela: Janela) -> tuple[bytes, str]:
        return self._fetcher.baixar(janela)

    def parse(self, bruto: bytes) -> pl.DataFrame:
        # A API devolve {"data": [...]}; o município vem aninhado em unidadeOrgao (Struct). Resposta
        # vazia → DataFrame vazio tipado (o contrato reprova em min_linhas, com mensagem clara).
        data = json.loads(bruto).get("data", [])
        if not data:
            return pl.DataFrame(
                schema={COL_VALOR: pl.Float64, COL_UNIDADE: pl.Struct({COL_IBGE_ANINHADO: pl.Utf8})}
            )
        return pl.DataFrame(data)

    def extrair(self, janela: Janela) -> pl.DataFrame:
        bruto, _ = self.baixar_bruto(janela)
        df = self.parse(bruto)
        CONTRATO.validar(df)  # borda bronze: falha claro se o layout do PNCP mudar
        return df

    def transformar_prata(self, df: pl.DataFrame) -> pl.DataFrame:
        return df.select(
            pl.col(COL_UNIDADE)
            .struct.field(COL_IBGE_ANINHADO)
            .cast(pl.Utf8)
            .str.strip_chars()
            .alias("cod_ibge"),
            pl.col(COL_VALOR).cast(pl.Float64, strict=False).alias("valor"),
        ).filter(
            pl.col("cod_ibge").is_not_null()
            & (pl.col("cod_ibge") != "")
            & pl.col("valor").is_not_null()
        )

    def agregar(self, df_prata: pl.DataFrame) -> pl.DataFrame:
        """Valor de contratos por município (soma do ``valorGlobal``)."""
        return (
            df_prata.group_by("cod_ibge")
            .agg(pl.col("valor").sum().alias("valor_contratos"))
            .sort("cod_ibge")
        )


class FetcherPncpHTTP:
    """Fetcher real: consulta os contratos do exercício na API aberta do PNCP (sem credencial).

    Não exercitado em teste (rede); parse/transformação são cobertos por fixture.
    """

    BASE = "https://pncp.gov.br/api/consulta/v1/contratos"

    def baixar(self, janela: Janela) -> tuple[bytes, str]:  # pragma: no cover - rede
        import urllib.request

        # Janela anual → intervalo [ano-01-01, ano-12-31]. URL/params a confirmar contra a API real.
        url = f"{self.BASE}?dataInicial={janela.ano}0101&dataFinal={janela.ano}1231&pagina=1"
        with urllib.request.urlopen(url, timeout=120) as resp:  # noqa: S310  # nosec B310
            return resp.read(), url
