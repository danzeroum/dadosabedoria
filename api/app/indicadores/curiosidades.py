"""'Você Sabia?' — curiosidades ANCORADAS sobre um território (Bloco 3.2 da auditoria).

Invariante 3 (insight ancorado): cada curiosidade só afirma VALORES RECUPERADOS do acervo, cita a
fonte e **não infere causalidade nem inventa número**. São justaposições factuais de indicadores
co-presentes, enquadradas como convite à exploração (link para o produto), nunca como veredito.
Sem dado → sem curiosidade (não preenche lacuna com suposição).
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class ValorIndicador:
    """Subconjunto mínimo de um indicador recuperado (mantém as regras puras e testáveis)."""

    valor: float
    fonte: str
    periodo: str


@dataclass(frozen=True)
class Curiosidade:
    texto: str  # afirmação factual ancorada — sem causalidade, sem projeção
    fonte: str  # proveniência (fonte do(s) indicador(es) usados)
    produto: str | None  # slug do produto para explorar (ex.: "esgoto-invisivel")


# Limiares conservadores: a curiosidade só dispara quando o fato é nítido (evita alarme falso).
_GAP_AGUA_ESGOTO_PP = 15.0
_SECA_ALERTA = 3.0

_AGUA = "saneamento.agua.atendimento_pct"
_ESGOTO = "saneamento.esgoto.coleta_pct"
_SECA = "saneamento.agua.seca_indice"


def _gap_agua_esgoto(ind: Mapping[str, ValorIndicador]) -> Curiosidade | None:
    """Água tratada bem acima da coleta de esgoto — a mesma fonte (SNIS), fato, não causa."""
    agua = ind.get(_AGUA)
    esgoto = ind.get(_ESGOTO)
    if agua is None or esgoto is None:
        return None
    gap = agua.valor - esgoto.valor
    if gap < _GAP_AGUA_ESGOTO_PP:
        return None
    return Curiosidade(
        texto=(
            f"A água tratada alcança {agua.valor:.0f}% da população, mas a coleta de esgoto, "
            f"{esgoto.valor:.0f}% — uma diferença de {gap:.0f} pontos."
        ),
        fonte=agua.fonte,
        produto="esgoto-invisivel",
    )


def _seca(ind: Mapping[str, ValorIndicador]) -> Curiosidade | None:
    """Índice de seca em patamar de alerta no pior mês — fato recuperado (ANA)."""
    seca = ind.get(_SECA)
    if seca is None or seca.valor < _SECA_ALERTA:
        return None
    return Curiosidade(
        texto=f"O índice de seca chegou a {seca.valor:.1f} (escala 0–5) no pior mês do exercício.",
        fonte=seca.fonte,
        produto="rio-em-risco",
    )


# Registro de regras (extensível). Cada regra é pura: Mapping -> Curiosidade | None.
_REGRAS: tuple[Callable[[Mapping[str, ValorIndicador]], Curiosidade | None], ...] = (
    _gap_agua_esgoto,
    _seca,
)


def montar_curiosidades(indicadores: Mapping[str, ValorIndicador]) -> list[Curiosidade]:
    """Aplica as regras ancoradas; devolve só as que disparam, na ordem do registro."""
    out: list[Curiosidade] = []
    for regra in _REGRAS:
        c = regra(indicadores)
        if c is not None:
            out.append(c)
    return out
