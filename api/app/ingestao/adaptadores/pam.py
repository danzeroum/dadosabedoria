"""Adaptador IBGE PAM (Pesquisa Agrícola Municipal) — domínio ``alimentacao``.

Bronze: consome a API SIDRA v3 do IBGE para as tabelas 1612 (lavouras temporárias) e
1613 (lavouras permanentes), variável 215 (Valor da produção em Mil Reais).

Indicador:
- ``valor_brl``: valor total da produção agrícola municipal (BRL), soma das duas lavouras.

Prata: normaliza cod_ibge (7 díg.), converte Mil BRL → BRL (× 1000), filtra inválidos ("-").
Ouro: soma de valor_brl por município (consolida lavouras temporárias + permanentes).

ASSUNÇÕES a confirmar na 1ª busca real (#0, host ``servicodados.ibge.gov.br``):
- Resposta JSON: lista de objetos com "resultados[].series[].localidade.id" (cod_ibge 7 díg.)
  e "resultados[].series[].serie.<ano>" (valor em Mil Reais como string; "-" = sem dado).
- Tabelas 1612 (lavouras temporárias) e 1613 (lavouras permanentes), variável 215.
- Nível de agregação N6 = municípios.
"""

from __future__ import annotations

import json

import polars as pl

from app.ingestao.adaptadores.base import FetcherFonte, Janela
from app.ingestao.contratos import ContratoFonte

CODIGO_INDICADOR = "alimentacao.producao.valor_total"

COL_IBGE = "cod_ibge"
COL_VALOR = "valor_mil_brl"

CONTRATO = ContratoFonte(
    fonte="ibge_pam",
    colunas_obrigatorias=frozenset({COL_IBGE, COL_VALOR}),
)


class AdaptadorPam:
    """Padrão Adapter: isola o formato IBGE PAM SIDRA. Fetcher injetado (testável sem rede)."""

    codigo = "ibge_pam"

    def __init__(self, fetcher: FetcherFonte) -> None:
        self._fetcher = fetcher

    def baixar_bruto(self, janela: Janela) -> tuple[bytes, str]:
        return self._fetcher.baixar(janela)

    def parse(self, bruto: bytes) -> pl.DataFrame:
        """Converte JSON SIDRA v3 → DataFrame com cod_ibge + valor_mil_brl."""
        dados: list[dict] = json.loads(bruto)
        linhas: list[dict[str, object]] = []
        for tabela in dados:
            ano_str = str(tabela.get("ano", ""))
            for resultado in tabela.get("resultados", []):
                for serie in resultado.get("series", []):
                    localidade = serie.get("localidade", {})
                    cod_ibge = str(localidade.get("id", ""))
                    serie_vals = serie.get("serie", {})
                    valor_raw = None
                    for v in serie_vals.values():
                        valor_raw = v
                        break
                    linhas.append(
                        {
                            COL_IBGE: cod_ibge,
                            COL_VALOR: valor_raw,
                            "_ano": ano_str,
                        }
                    )
        if not linhas:
            return pl.DataFrame(
                {COL_IBGE: pl.Series([], dtype=pl.Utf8), COL_VALOR: pl.Series([], dtype=pl.Utf8)}
            )
        return pl.DataFrame(linhas)

    def extrair(self, janela: Janela) -> pl.DataFrame:
        bruto, _ = self.baixar_bruto(janela)
        df = self.parse(bruto)
        CONTRATO.validar(df)
        return df

    def transformar_prata(self, df: pl.DataFrame) -> pl.DataFrame:
        """Normaliza cod_ibge, converte Mil BRL → BRL (× 1000), filtra inválidos."""
        return (
            df.select(
                pl.col(COL_IBGE).cast(pl.Utf8).str.strip_chars().alias("cod_ibge"),
                pl.col(COL_VALOR).cast(pl.Utf8).str.strip_chars().alias("valor_mil_brl_str"),
            )
            .filter(
                pl.col("cod_ibge").is_not_null()
                & (pl.col("cod_ibge") != "")
                & pl.col("valor_mil_brl_str").is_not_null()
                & (pl.col("valor_mil_brl_str") != "")
                & (pl.col("valor_mil_brl_str") != "-")
            )
            .with_columns(
                (pl.col("valor_mil_brl_str").cast(pl.Float64, strict=False) * 1000.0).alias(
                    "valor_brl"
                )
            )
            .filter(pl.col("valor_brl").is_not_null())
            .select("cod_ibge", "valor_brl")
        )

    def agregar(self, df_prata: pl.DataFrame) -> pl.DataFrame:
        """Soma de valor_brl por município (consolida lavouras temporárias + permanentes)."""
        return (
            df_prata.group_by("cod_ibge")
            .agg(pl.col("valor_brl").sum().alias("valor_brl"))
            .sort("cod_ibge")
        )


class FetcherPamHTTP:
    """Fetcher real: baixa as tabelas 1612 + 1613 da API SIDRA v3 do IBGE.

    URL e parâmetros a confirmar na 1ª busca real (``servicodados.ibge.gov.br``).
    """

    BASE = "https://servicodados.ibge.gov.br/api/v3/agregados"
    _TABELAS = ("1612", "1613")
    # Variável 215 = "Valor da produção" (Mil Reais). Confirmado ao vivo (2026-07-01):
    # a var 762 não existe nos metadados de 1612/1613 e retorna HTTP 500.
    _VAR = "215"

    def baixar(self, janela: Janela) -> tuple[bytes, str]:  # pragma: no cover - rede
        import urllib.request

        _localidades = "N6[all]"
        resultados: list[dict] = []
        url = (
            f"{self.BASE}/{self._TABELAS[0]}/periodos/{janela.ano}"
            f"/variaveis/{self._VAR}?localidades={_localidades}"
        )
        for tabela in self._TABELAS:
            t_url = (
                f"{self.BASE}/{tabela}/periodos/{janela.ano}"
                f"/variaveis/{self._VAR}?localidades={_localidades}"
            )
            with urllib.request.urlopen(t_url, timeout=120) as resp:  # noqa: S310  # nosec B310
                dados = json.loads(resp.read())
                for item in dados:
                    item["_tabela"] = tabela
                    item["ano"] = janela.ano
                resultados.extend(dados)
        return json.dumps(resultados).encode("utf-8"), url
