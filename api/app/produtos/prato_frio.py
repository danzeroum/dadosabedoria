"""PratoFrio (ALIM-01) — produção agrícola municipal por habitante (IBGE PAM).

Pergunta do produto: **quanto o município produz agricolamente por habitante?**

Usa o indicador ``alimentacao.producao.valor_total`` (soma do Valor da Produção das lavouras
temporárias/1612 e permanentes/1613 do IBGE PAM, variável 215, convertido de Mil BRL para BRL).

Classificação por valor_por_hab (BRL/habitante/ano):
- ``alta``      : ≥ R$ 5.000/hab/ano
- ``moderada``  : ≥ R$ 500/hab/ano
- ``baixa``     : < R$ 500/hab/ano
- ``sem_dado``  : sem dado disponível

HONESTIDADE:
- A produção agrícola é fortemente condicionada por geografia, solo e clima — municípios urbanos
  e metropolitanos terão naturalmente valores baixos. Use como CONTEXTO, não ranking.
- PAM cobre lavouras; exclui pecuária (PPM), extrativismo e silvicultura.
- Valor da produção agrícola em R$/hab é contexto de vocação produtiva, não de renda.
- Lag típico de ~12 meses após o exercício de referência.
- Limiares provisórios — a calibrar com a distribuição nacional real.
- Dupla face (§17): variação natural por bioma/clima — não culpa dos moradores. (ALIM-01)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

NivelProducao = Literal["alta", "moderada", "baixa", "sem_dado"]

_LIMIAR_ALTA = 5_000.0  # BRL/hab/ano
_LIMIAR_MODERADA = 500.0  # BRL/hab/ano

NOTA_HONESTA = (
    "Valor total da produção agrícola municipal (lavouras temporárias + permanentes)"
    " por habitante. "
    "Fonte: IBGE PAM (Pesquisa Agrícola Municipal), tabelas 1612 e 1613, variável 215 "
    "(Valor da produção, Mil Reais). "
    "Produção agrícola varia por geografia, solo e clima — municípios urbanos terão"
    " naturalmente valores baixos. Interprete como vocação produtiva do território,"
    " não como indicador de gestão. "
    "Limiares provisórios — a calibrar com a distribuição nacional. "
    "Forma a confirmar na 1ª busca real (ALIM-01, dupla face §17)."
)


@dataclass(frozen=True)
class PratoFrio:
    """Contrato: produção agrícola municipal por habitante."""

    codigo_ibge: str
    nome: str
    uf: str | None

    populacao: int | None
    periodo: str | None  # YYYY do exercício
    valor_total: float | None  # BRL total (soma das lavouras)
    valor_por_hab: float | None  # BRL/hab/ano
    nivel: NivelProducao


def classificar_nivel(valor_por_hab: float | None) -> NivelProducao:
    """Classifica o nível de produção agrícola per capita."""
    if valor_por_hab is None:
        return "sem_dado"
    if valor_por_hab >= _LIMIAR_ALTA:
        return "alta"
    if valor_por_hab >= _LIMIAR_MODERADA:
        return "moderada"
    return "baixa"


def calcular(
    codigo_ibge: str,
    nome: str,
    uf: str | None,
    populacao: int | None,
    *,
    periodo: str | None,
    valor_total: float | None,
) -> PratoFrio:
    """Monta o PratoFrio a partir dos dados disponíveis; degrada graciosamente com dado parcial."""
    por_hab: float | None = None
    if valor_total is not None and populacao and populacao > 0:
        por_hab = round(valor_total / populacao, 2)

    return PratoFrio(
        codigo_ibge=codigo_ibge,
        nome=nome,
        uf=uf,
        populacao=populacao,
        periodo=periodo,
        valor_total=valor_total,
        valor_por_hab=por_hab,
        nivel=classificar_nivel(por_hab),
    )
