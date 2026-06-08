"""Adaptador do SICONFI/STN (Tesouro) — finanças municipais (DCA), domínio ``financas``.

Bronze (parse): lê o JSON da API do SICONFI (lista ``items``) num DataFrame Polars. Prata: filtra a
conta-alvo (Transferências Correntes orçamentárias, pela ``coluna`` realizada) e normaliza
``cod_ibge`` e o valor. Ouro: soma por município.

**Forma confirmada no #0 (2026-06-07, ADR-0028)** contra a API real — corrige o mock antigo:
- ``cod_ibge`` é **int** e ``valor`` é **numérico** (o mock usava strings);
- cada conta vem em **três colunas** (``Receitas Brutas Realizadas`` + duas deduções) → somar só a
  realizada, senão dobra/contamina o valor;
- a conta real é **prefixada por código** (``1.7.0.0.00.0.0 - Transferências Correntes``) e há uma
  homônima **intra**-orçamentária (``7.7...``) → casar por ``cod_conta`` (``RO1.7.0.0.00.0.0``), não
  pelo texto.
A DCA é **anual** por exercício; ``cod_ibge`` é o IBGE de 7 dígitos. Fonte aberta, sem credencial.
"""

from __future__ import annotations

import json
import re

import polars as pl

from app.ingestao.adaptadores.base import FetcherFonte, Janela
from app.ingestao.contratos import ContratoFonte

#: Indicador alimentado por este adaptador.
CODIGO_INDICADOR = "financas.transferencias.correntes"

COL_IBGE = "cod_ibge"
COL_VALOR = "valor"
COL_CONTA = "conta"
COL_COLUNA = "coluna"
COL_COD_CONTA = "cod_conta"

#: Conta-alvo por **código** (não pelo texto): Transferências Correntes ORÇAMENTÁRIAS (Anexo I-C).
#: A homônima intra-orçamentária é ``RI7.7.0.0.00.0.0`` — fora do alvo (confirmado no #0).
CONTA_ALVO_COD = "RO1.7.0.0.00.0.0"
#: Coluna do valor efetivamente arrecadado — as outras (``Deduções - FUNDEB`` etc.) ficam de fora.
COLUNA_REALIZADA = "Receitas Brutas Realizadas"

#: Contrato do bruto SICONFI: itens precisam de município, valor, conta, e — confirmado no #0 — das
#: dimensões ``coluna`` e ``cod_conta`` (sem elas o filtro dobraria/contaminaria o valor).
CONTRATO = ContratoFonte(
    fonte="siconfi",
    colunas_obrigatorias=frozenset({COL_IBGE, COL_VALOR, COL_CONTA, COL_COLUNA, COL_COD_CONTA}),
)

# --- Função orçamentária (Anexo I-E) — vocabulário PROMOVIDO DA FONTE no #0 -----------------------
# A classificação funcional é a Portaria MOG 42/1999, como o SICONFI a rotula. No Anexo I-E a função
# vive no TEXTO ``conta`` ("NN - Nome"); ``cod_conta`` é constante ("TotalDespesas"). Subfunção é
# "NN.NNN - ..."; agregados ("Total Geral...", "Despesas Intraorçamentárias") não casam o padrão.
# `código → nome` exatamente como a fonte devolve (28 funções; 24 observadas nas capturas do #0).
FUNCOES_SICONFI: dict[str, str] = {
    "01": "Legislativa",
    "02": "Judiciária",
    "03": "Essencial à Justiça",
    "04": "Administração",
    "05": "Defesa Nacional",
    "06": "Segurança Pública",
    "07": "Relações Exteriores",
    "08": "Assistência Social",
    "09": "Previdência Social",
    "10": "Saúde",
    "11": "Trabalho",
    "12": "Educação",
    "13": "Cultura",
    "14": "Direitos da Cidadania",
    "15": "Urbanismo",
    "16": "Habitação",
    "17": "Saneamento",
    "18": "Gestão Ambiental",
    "19": "Ciência e Tecnologia",
    "20": "Agricultura",
    "21": "Organização Agrária",
    "22": "Indústria",
    "23": "Comércio e Serviços",
    "24": "Comunicações",
    "25": "Energia",
    "26": "Transporte",
    "27": "Desporto e Lazer",
    "28": "Encargos Especiais",
}

#: Colunas de execução do Anexo I-E (a base do OndeFoi re-ancorado — ADR-0029).
COLUNA_EMPENHADO = "Despesas Empenhadas"
COLUNA_LIQUIDADO = "Despesas Liquidadas"

_RE_FUNCAO = re.compile(r"^(\d{2}) - (.+)$")  # função de 1º nível; subfunção ("NN.NNN - ") não casa


def parse_funcao(conta: str) -> tuple[str, str] | None:
    """``"10 - Saúde"`` → ``("10", "Saúde")``; subfunção/total/agregado → ``None`` (Anexo I-E)."""
    m = _RE_FUNCAO.match(conta.strip())
    return (m.group(1), m.group(2).strip()) if m else None


def e_funcao(conta: str) -> bool:
    """True só para FUNÇÃO de 1º nível ("NN - Nome") — ignora subfunção, total e agregados."""
    return _RE_FUNCAO.match(conta.strip()) is not None


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
            return pl.DataFrame(
                {COL_IBGE: [], COL_VALOR: [], COL_CONTA: [], COL_COLUNA: [], COL_COD_CONTA: []}
            )
        return pl.DataFrame(itens)

    def extrair(self, janela: Janela) -> pl.DataFrame:
        bruto, _ = self.baixar_bruto(janela)
        df = self.parse(bruto)
        CONTRATO.validar(df)  # borda bronze: falha claro se o layout do SICONFI mudar
        return df

    def transformar_prata(self, df: pl.DataFrame) -> pl.DataFrame:
        return (
            df.filter(
                (pl.col(COL_COD_CONTA).cast(pl.Utf8).str.strip_chars() == CONTA_ALVO_COD)
                & (pl.col(COL_COLUNA).cast(pl.Utf8).str.strip_chars() == COLUNA_REALIZADA)
            )
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

    # --- Anexo I-E: execução por função (OndeFoi/TRANSP-06, re-ancorado — ADR-0029) -------------
    def transformar_prata_funcoes(self, df: pl.DataFrame) -> pl.DataFrame:
        """Anexo I-E → linhas por (município, função de 1º nível, coluna), só Empenhado/Liquidado.

        Extrai ``funcao_cod``/``funcao_nome`` do texto ``conta`` (``"NN - Nome"``); subfunção
        (``"NN.NNN - "``), totais e agregados não casam o padrão e caem fora.
        """
        conta = pl.col(COL_CONTA).cast(pl.Utf8).str.strip_chars()
        return (
            df.filter(
                pl.col(COL_COLUNA)
                .cast(pl.Utf8)
                .str.strip_chars()
                .is_in([COLUNA_EMPENHADO, COLUNA_LIQUIDADO])
            )
            .with_columns(
                conta.str.extract(_RE_FUNCAO.pattern, 1).alias("funcao_cod"),
                conta.str.extract(_RE_FUNCAO.pattern, 2).str.strip_chars().alias("funcao_nome"),
            )
            .filter(pl.col("funcao_cod").is_not_null())  # só função de 1º nível
            .select(
                pl.col(COL_IBGE).cast(pl.Utf8).str.strip_chars().alias("cod_ibge"),
                "funcao_cod",
                "funcao_nome",
                pl.col(COL_COLUNA).cast(pl.Utf8).str.strip_chars().alias("coluna"),
                pl.col(COL_VALOR).cast(pl.Float64, strict=False).alias("valor"),
            )
            .filter(pl.col("cod_ibge").is_not_null() & pl.col("valor").is_not_null())
        )

    def agregar_funcoes(self, df_prata: pl.DataFrame) -> pl.DataFrame:
        """Empenhado + Liquidado por (município, função) — a base do OndeFoi (ADR-0029)."""
        return (
            df_prata.group_by(["cod_ibge", "funcao_cod", "funcao_nome"])
            .agg(
                pl.col("valor")
                .filter(pl.col("coluna") == COLUNA_EMPENHADO)
                .sum()
                .alias("empenhado"),
                pl.col("valor")
                .filter(pl.col("coluna") == COLUNA_LIQUIDADO)
                .sum()
                .alias("liquidado"),
            )
            .sort(["cod_ibge", "funcao_cod"])
        )


class FetcherSiconfiHTTP:
    """Fetcher real: baixa a DCA do exercício na API do SICONFI (aberta, sem credencial).

    **Ingestão nacional**: a API exige ``id_ente`` por município (sem ele retorna 0 linhas —
    validado em 2026-06-08, ADR-0032). Estratégia: (1) lista todos os municípios via
    ``/tt/entes``; (2) busca o DCA de cada um com threads (limitadas + backoff).
    URL/params confirmados no #0 (ADR-0028): ``an_exercicio`` + ``no_anexo`` + ``id_ente``.
    """

    BASE = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/dca"
    ENTES = "https://apidatalake.tesouro.gov.br/ords/siconfi/tt/entes"
    ANEXO = (
        "DCA-Anexo I-C"  # receitas (Transferências Correntes); I-E = despesas por função (OndeFoi)
    )
    # Bom-cidadão: 5 threads simultâneas + backoff (invariante 6).
    # ~5.500 entes × 0.1 s de delay → ~11 min; cada thread aguarda antes de cada request.
    _MAX_WORKERS = 5
    _TIMEOUT = 45
    _DELAY = 0.1   # s entre requests por thread (bom-cidadão — invariante 6)
    _MAX_RETRIES = 3

    def _listar_municipios(self, ano: int) -> list[int]:  # pragma: no cover - rede
        import json as _json
        import urllib.request

        municipios: list[int] = []
        offset = 0
        limit = 500
        while True:
            url = f"{self.ENTES}?an_exercicio={ano}&tipo_esfera=M&limit={limit}&offset={offset}"
            with urllib.request.urlopen(url, timeout=60) as resp:  # noqa: S310  # nosec B310
                d = _json.load(resp)
            items = d.get("items", [])
            municipios.extend(int(it["cod_ibge"]) for it in items)
            if not d.get("hasMore"):
                break
            offset += len(items)
        return municipios

    def _baixar_ente(self, ano: int, cod_ibge: int) -> list[dict]:  # pragma: no cover - rede
        import json as _json
        import time
        import urllib.error
        import urllib.parse
        import urllib.request

        query = urllib.parse.urlencode(
            {"an_exercicio": ano, "no_anexo": self.ANEXO, "id_ente": cod_ibge}
        )
        url = f"{self.BASE}?{query}"
        time.sleep(self._DELAY)  # bom-cidadão: pausa antes de cada request (invariante 6)
        for attempt in range(1, self._MAX_RETRIES + 1):
            try:
                with urllib.request.urlopen(url, timeout=self._TIMEOUT) as resp:  # noqa: S310  # nosec B310
                    return _json.load(resp).get("items", [])
            except (urllib.error.URLError, OSError):
                if attempt == self._MAX_RETRIES:
                    raise
                time.sleep(2 ** attempt)  # backoff exponencial: 2s, 4s
        return []  # nunca alcançado; satisfaz o type-checker

    def baixar(self, janela: Janela) -> tuple[bytes, str]:  # pragma: no cover - rede
        import json as _json
        import logging
        from concurrent.futures import ThreadPoolExecutor, as_completed

        log = logging.getLogger(__name__)
        municipios = self._listar_municipios(janela.ano)
        log.info("SICONFI: %d municípios para o exercício %d", len(municipios), janela.ano)
        todos: list[dict] = []
        concluidos = 0
        with ThreadPoolExecutor(max_workers=self._MAX_WORKERS) as ex:
            futures = {ex.submit(self._baixar_ente, janela.ano, cod): cod for cod in municipios}
            for fut in as_completed(futures):
                todos.extend(fut.result())
                concluidos += 1
                if concluidos % 500 == 0 or concluidos == len(municipios):
                    log.info("SICONFI: %d/%d municípios baixados", concluidos, len(municipios))
        url_ref = f"{self.BASE}?an_exercicio={janela.ano}&no_anexo={self.ANEXO}"
        return _json.dumps({"items": todos}).encode(), url_ref


class FetcherSiconfiFuncoesHTTP(FetcherSiconfiHTTP):  # pragma: no cover - rede
    """Fetcher real do **Anexo I-E** (despesas por função) — OndeFoi (ADR-0029).

    Herda a estratégia nacional (lista entes → DCA por município com threads);
    troca só o ``no_anexo``.
    """

    ANEXO = "DCA-Anexo I-E"
