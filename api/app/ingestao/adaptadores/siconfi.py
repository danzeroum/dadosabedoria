"""Adaptador do SICONFI/STN (Tesouro) — finanças municipais (DCA), domínio ``financas``.

Bronze (parse): lê o JSON da API do SICONFI (lista ``items``) num DataFrame Polars. Prata: filtra a
conta-alvo (Transferências Correntes), normaliza ``cod_ibge`` e o valor. Ouro: soma por município.

Contrato de dados (ASSUNÇÕES a confirmar contra a API real do SICONFI): a DCA (Declaração de Contas
Anuais) é **anual** por exercício; ``cod_ibge`` é o IBGE de 7 dígitos.
Fonte aberta, sem credencial. A carga em ``valor`` é feita pelo ``pipeline`` via ``escrever_ouro``.
"""

from __future__ import annotations

import json

import polars as pl

from app.ingestao.adaptadores.base import FetcherFonte, Janela
from app.ingestao.contratos import ContratoFonte

#: Indicador alimentado por este adaptador.
CODIGO_INDICADOR = "financas.transferencias.correntes"

COL_IBGE = "cod_ibge"
COL_VALOR = "valor"
COL_CONTA = "conta"
CONTA_ALVO = "Transferências Correntes"  # conta da DCA (receita) — "OndeFoi" (TRANSP-06)

#: Contrato do bruto SICONFI: a lista de itens precisa do município, do valor e da conta.
CONTRATO = ContratoFonte(
    fonte="siconfi",
    colunas_obrigatorias=frozenset({COL_IBGE, COL_VALOR, COL_CONTA}),
)


class AdaptadorSiconfi:
    """Padrão Adapter: isola o formato do SICONFI. Fetcher injetado (testável sem rede)."""

    codigo = "siconfi"

    def __init__(self, fetcher: FetcherFonte) -> None:
        self._fetcher = fetcher

    def baixar_bruto(self, janela: Janela) -> tuple[bytes, str]:
        return self._fetcher.baixar(janela)

    def parse(self, bruto: bytes) -> pl.DataFrame:
        # A API devolve {"items": [...]}; polars infere os tipos das chaves (os tipos finais vêm na
        # prata via cast). Resposta vazia → DataFrame vazio com as colunas do contrato.
        itens = json.loads(bruto).get("items", [])
        if not itens:
            return pl.DataFrame({COL_IBGE: [], COL_VALOR: [], COL_CONTA: []})
        return pl.DataFrame(itens)

    def extrair(self, janela: Janela) -> pl.DataFrame:
        bruto, _ = self.baixar_bruto(janela)
        df = self.parse(bruto)
        CONTRATO.validar(df)  # borda bronze: falha claro se o layout do SICONFI mudar
        return df

    def transformar_prata(self, df: pl.DataFrame) -> pl.DataFrame:
        return (
            df.filter(pl.col(COL_CONTA).cast(pl.Utf8).str.strip_chars() == CONTA_ALVO)
            .select(
                pl.col(COL_IBGE).cast(pl.Utf8).str.strip_chars().alias("cod_ibge"),
                pl.col(COL_VALOR).cast(pl.Float64, strict=False).alias("valor"),
            )
            .filter(pl.col("cod_ibge").is_not_null() & pl.col("valor").is_not_null())
        )

    def agregar(self, df_prata: pl.DataFrame) -> pl.DataFrame:
        """Transferências correntes por município (soma das linhas da conta-alvo)."""
        return (
            df_prata.group_by("cod_ibge")
            .agg(pl.col("valor").sum().alias("transferencias"))
            .sort("cod_ibge")
        )


class FetcherSiconfiHTTP:
    """Fetcher real: baixa a DCA do exercício na API do SICONFI (aberta, sem credencial).

    Não exercitado em teste (rede); parse/transformação são cobertos por fixture.
    """

    BASE = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca"

    def baixar(self, janela: Janela) -> tuple[bytes, str]:  # pragma: no cover - rede
        import urllib.request

        # an_exercicio = ano da janela (DCA é anual). URL/params a confirmar contra a API real.
        url = f"{self.BASE}?an_exercicio={janela.ano}&no_anexo=DCA-Anexo I-C"
        with urllib.request.urlopen(url, timeout=60) as resp:  # noqa: S310  # nosec B310 - URL fixa https
            return resp.read(), url
