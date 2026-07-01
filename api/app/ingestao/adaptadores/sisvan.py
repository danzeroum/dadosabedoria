"""Adaptador SISVAN — estado nutricional de crianças < 5 anos e gestantes, domínio saúde.

Bronze: **API pública de Dados Abertos do Ministério da Saúde** (JSON), endpoint
``/sisvan/estado-nutricional`` em ``apidadosabertos.saude.gov.br``. O antigo CSV no bucket S3
(``ckan.saude.gov.br/SISVAN``) foi desativado (403 AccessDenied) e a fonte migrou para esta API.

Indicadores:
- ``baixo_peso_pct``: % de crianças < 5 anos com **magreza** ou **magreza acentuada**
  (``crianca_imc_x_idade``) entre as acompanhadas no município.
- ``gestante_baixo_peso_pct``: % de gestantes com **baixo peso**
  (``codigo_estado_nutricional_imc_gestante``) entre as acompanhadas no município.

Prata: filtra crianças < 5 anos com classificação IMC-x-idade válida (não nula).
Ouro: % com baixo peso por município; n_amostra = total acompanhado (k-anon n≥5).

FORMA REAL confirmada ao vivo (2026-07-01, host ``apidadosabertos.saude.gov.br``):
- JSON ``{"estados_nutricionais": [ {...}, ... ]}``.
- ``codigo_municipio`` = IBGE de **6 dígitos** (sem dígito verificador; ex. 355030).
- ``idade`` = int (anos completos).
- ``crianca_imc_x_idade`` = **texto** (não código): "Magreza acentuada", "Magreza", "Eutrofia",
  "Risco de sobrepeso", "Sobrepeso", "Obesidade", "Obesidade grave" — nulo p/ não-criança.
- ``codigo_estado_nutricional_imc_gestante`` = **texto** (apesar do nome "codigo"):
  "Baixo peso", "Adequado ou eutrófico", "Sobrepeso", "Obesidade" — nulo fora de gestante.
- ``ano_mes_competencia`` = "YYYYMM" (filtro incremental — invariante 6).

RESSALVA de ingestão nacional (ver ``pendencias.md``): a API entrega no máximo ~20 registros por
resposta (paginação por ``offset``), o que torna o bulk nacional lento. A esteira/forma abaixo
está correta; a fonte definitiva do bulk nacional é decisão do dono do ambiente.
"""

from __future__ import annotations

import json
import unicodedata

import polars as pl

from app.ingestao.adaptadores.base import FetcherFonte, Janela
from app.ingestao.contratos import ContratoFonte

CODIGO_INDICADOR = "alimentacao.nutricao.baixo_peso_pct"

COL_IBGE = "codigo_municipio"
COL_IDADE = "idade"
COL_ESTADO = "crianca_imc_x_idade"

#: Crianças < 5 anos (0, 1, 2, 3, 4 anos completos).
_IDADE_MAX = 5


def _normalizar(texto: str) -> str:
    """Minúsculas sem acento, para casar a classificação textual de forma robusta."""
    sem_acento = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode("ascii")
    return sem_acento.strip().lower()


#: Classificações de baixo peso infantil (IMC-x-idade), normalizadas.
_BAIXO_PESO = frozenset({"magreza acentuada", "magreza"})

CONTRATO = ContratoFonte(
    fonte="sisvan",
    colunas_obrigatorias=frozenset({COL_IBGE, COL_IDADE, COL_ESTADO}),
)


def _parse_json(bruto: bytes, colunas: list[str]) -> pl.DataFrame:
    """JSON SISVAN → DataFrame só com as ``colunas`` de interesse (tudo como texto)."""
    try:
        dados = json.loads(bruto)
    except (json.JSONDecodeError, ValueError):
        return pl.DataFrame({c: pl.Series([], dtype=pl.Utf8) for c in colunas})
    registros = dados.get("estados_nutricionais", []) if isinstance(dados, dict) else []
    linhas = [
        {c: (None if r.get(c) is None else str(r.get(c))) for c in colunas} for r in registros
    ]
    if not linhas:
        return pl.DataFrame({c: pl.Series([], dtype=pl.Utf8) for c in colunas})
    return pl.DataFrame(linhas, schema=dict.fromkeys(colunas, pl.Utf8))


class AdaptadorSisvan:
    """Isola o formato da API SISVAN/MS (crianças). Fetcher injetado (testável sem rede)."""

    codigo = "sisvan"

    def __init__(self, fetcher: FetcherFonte) -> None:
        self._fetcher = fetcher

    def baixar_bruto(self, janela: Janela) -> tuple[bytes, str]:
        return self._fetcher.baixar(janela)

    def parse(self, bruto: bytes) -> pl.DataFrame:
        """JSON SISVAN → DataFrame com as 3 colunas de produto."""
        return _parse_json(bruto, [COL_IBGE, COL_IDADE, COL_ESTADO])

    def extrair(self, janela: Janela) -> pl.DataFrame:
        bruto, _ = self.baixar_bruto(janela)
        df = self.parse(bruto)
        CONTRATO.validar(df)
        return df

    def transformar_prata(self, df: pl.DataFrame) -> pl.DataFrame:
        """Filtra crianças < 5 anos com classificação válida; marca baixo peso (0/1)."""
        baixo = list(_BAIXO_PESO)
        return (
            df.with_columns(
                pl.col(COL_IBGE).str.strip_chars().alias("cod_ibge"),
                pl.col(COL_IDADE).cast(pl.Int32, strict=False).alias("idade"),
                pl.col(COL_ESTADO)
                .map_elements(
                    lambda v: _normalizar(v) if v is not None else None, return_dtype=pl.Utf8
                )
                .alias("estado_norm"),
            )
            .filter(
                pl.col("cod_ibge").is_not_null()
                & (pl.col("cod_ibge") != "")
                & pl.col("idade").is_not_null()
                & (pl.col("idade") < _IDADE_MAX)
                & pl.col("estado_norm").is_not_null()
                & (pl.col("estado_norm") != "")
            )
            .with_columns(pl.col("estado_norm").is_in(baixo).cast(pl.Int32).alias("baixo_peso"))
            .select("cod_ibge", "baixo_peso")
        )

    def agregar(self, df_prata: pl.DataFrame) -> pl.DataFrame:
        """% de crianças < 5 com baixo peso por município; n = total acompanhado."""
        return (
            df_prata.group_by("cod_ibge")
            .agg(
                pl.len().alias("n_total"),
                pl.col("baixo_peso").sum().alias("n_baixo_peso"),
            )
            .with_columns(
                (pl.col("n_baixo_peso").cast(pl.Float64) / pl.col("n_total") * 100.0).alias(
                    "baixo_peso_pct"
                )
            )
            .sort("cod_ibge")
        )


class _FetcherSisvanApiBase:
    """Fetcher real: pagina o endpoint JSON da API de Dados Abertos do MS por competência.

    A API responde no máximo ~20 registros por página → itera ``offset`` até esvaziar (bom-cidadão,
    invariante 6). Host bloqueado no contêiner github-only — exercitado só com rede aberta/VPS.
    """

    _BASE = "https://apidadosabertos.saude.gov.br/sisvan/estado-nutricional"
    _LIMIT = 1000  # a API ignora acima de ~20; mantemos alto para o dia em que aumentarem
    _TIMEOUT = 120

    def _baixar_paginado(self, janela: Janela) -> tuple[bytes, str]:  # pragma: no cover - rede
        import urllib.parse
        import urllib.request

        comp = janela.competencia
        registros: list[dict] = []
        offset = 0
        url_ref = f"{self._BASE}?ano_mes_competencia={comp}"
        while True:
            query = urllib.parse.urlencode(
                {"ano_mes_competencia": comp, "limit": self._LIMIT, "offset": offset}
            )
            url = f"{self._BASE}?{query}"
            with urllib.request.urlopen(url, timeout=self._TIMEOUT) as resp:  # noqa: S310  # nosec B310
                pagina = json.loads(resp.read()).get("estados_nutricionais", [])
            if not pagina:
                break
            registros.extend(pagina)
            offset += len(pagina)
        return json.dumps({"estados_nutricionais": registros}).encode("utf-8"), url_ref


class FetcherSisvanHTTP(_FetcherSisvanApiBase):
    """Fetcher real de crianças (mesma API; o parser seleciona as colunas)."""

    def baixar(self, janela: Janela) -> tuple[bytes, str]:  # pragma: no cover - rede
        return self._baixar_paginado(janela)


# ============================================================= Gestantes (SAUDE-03)

CODIGO_INDICADOR_GESTANTE = "saude.materno.gestante_baixo_peso_pct"

COL_ESTADO_GESTANTE = "codigo_estado_nutricional_imc_gestante"
#: Classificação de baixo peso gestacional (texto), normalizada.
_BAIXO_PESO_GESTANTE = frozenset({"baixo peso"})

CONTRATO_GESTANTE = ContratoFonte(
    fonte="sisvan",
    colunas_obrigatorias=frozenset({COL_IBGE, COL_ESTADO_GESTANTE}),
)


class AdaptadorSisvanGestante:
    """Isola o formato da API SISVAN/MS para gestantes (SAUDE-03).

    A gestante é identificada pela presença da classificação
    ``codigo_estado_nutricional_imc_gestante`` (só gestantes têm IMC gestacional na fonte).
    """

    codigo = "sisvan_gestante"

    def __init__(self, fetcher: FetcherFonte) -> None:
        self._fetcher = fetcher

    def baixar_bruto(self, janela: Janela) -> tuple[bytes, str]:
        return self._fetcher.baixar(janela)

    def parse(self, bruto: bytes) -> pl.DataFrame:
        """JSON SISVAN → DataFrame com cod_ibge + classificação gestacional."""
        return _parse_json(bruto, [COL_IBGE, COL_ESTADO_GESTANTE])

    def extrair(self, janela: Janela) -> pl.DataFrame:
        bruto, _ = self.baixar_bruto(janela)
        df = self.parse(bruto)
        CONTRATO_GESTANTE.validar(df)
        return df

    def transformar_prata(self, df: pl.DataFrame) -> pl.DataFrame:
        """Filtra gestantes (classificação não nula); marca baixo peso (0/1)."""
        baixo = list(_BAIXO_PESO_GESTANTE)
        return (
            df.with_columns(
                pl.col(COL_IBGE).str.strip_chars().alias("cod_ibge"),
                pl.col(COL_ESTADO_GESTANTE)
                .map_elements(
                    lambda v: _normalizar(v) if v is not None else None, return_dtype=pl.Utf8
                )
                .alias("estado_norm"),
            )
            .filter(
                pl.col("cod_ibge").is_not_null()
                & (pl.col("cod_ibge") != "")
                & pl.col("estado_norm").is_not_null()
                & (pl.col("estado_norm") != "")
            )
            .with_columns(pl.col("estado_norm").is_in(baixo).cast(pl.Int32).alias("baixo_peso"))
            .select("cod_ibge", "baixo_peso")
        )

    def agregar(self, df_prata: pl.DataFrame) -> pl.DataFrame:
        """% de gestantes com baixo peso por município; n = total acompanhado."""
        return (
            df_prata.group_by("cod_ibge")
            .agg(
                pl.len().alias("n_total"),
                pl.col("baixo_peso").sum().alias("n_baixo_peso"),
            )
            .with_columns(
                (pl.col("n_baixo_peso").cast(pl.Float64) / pl.col("n_total") * 100.0).alias(
                    "gestante_baixo_peso_pct"
                )
            )
            .sort("cod_ibge")
        )


class FetcherSisvanGestanteHTTP(_FetcherSisvanApiBase):
    """Fetcher real de gestantes — mesma API/competência; o parser seleciona a coluna."""

    def baixar(self, janela: Janela) -> tuple[bytes, str]:  # pragma: no cover - rede
        return self._baixar_paginado(janela)
