"""LuzNoMapa (SANE-04) — qualidade do fornecimento de energia elétrica por município (ANEEL).

Pergunta do produto: **o fornecimento de energia no município é confiável?**

Usa os indicadores ``energia.qualidade.dec`` (DEC — Duração Equivalente por Consumidor,
em horas) e ``energia.qualidade.fec`` (FEC — Frequência Equivalente por Consumidor,
interrupções/ano) da ANEEL. Lógica **pura** — sem rede/DB.

HONESTIDADE:
- DEC e FEC medem o serviço das distribuidoras cadastradas na ANEEL — não cobre energia
  informal, geradores próprios ou microgeração distribuída.
- Cobre os consumidores da rede de distribuição (baixa/média tensão). Grandes industriais
  (alta tensão, ANEEL direta) podem ter perfil diferente.
- Valores são médias anuais por distribuidora/município — não capturam eventos pontuais
  (tempestades, obras) fora do padrão histórico.
- Municípios sem distribuidora cadastrada na ANEEL aparecem sem dado.
- Dado anual com lag típico de ~12 meses (exercício anterior).
- Dupla face (§17): indicador de infraestrutura — estrutural, não culpa dos moradores;
  uso como contexto de vulnerabilidade energética. (SANE-04)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

NivelEnergia = Literal["confiavel", "regular", "fragil", "sem_dado"]

# Limiares baseados no perfil nacional das distribuidoras brasileiras.
# ANEEL define metas por distribuidora; usamos percentis do setor como referência.
# DEC (horas/consumidor/ano): melhores distribuidoras: ~4–6 h; piores: > 25 h.
_DEC_CONFIAVEL = 8.0  # ≤ 8 h: distribuição confiável
_DEC_REGULAR = 20.0  # 8–20 h: regular; > 20 h: frágil

# FEC (interrupções/consumidor/ano): melhores distribuidoras: ~4–6; piores > 15.
_FEC_CONFIAVEL = 6.0
_FEC_REGULAR = 15.0

NOTA_HONESTA = (
    "DEC (Duração Equivalente de Interrupção por Consumidor, horas/ano) e FEC "
    "(Frequência Equivalente de Interrupção por Consumidor, interrupções/ano) da ANEEL "
    "(Agência Nacional de Energia Elétrica). Cobre distribuidoras reguladas — não inclui "
    "energia informal, geradores próprios ou microgeração. Municípios sem distribuidora "
    "cadastrada aparecem sem dado. Dado anual com lag típico de ~12 meses. "
    "Limiares DEC: confiável ≤ 8 h, regular 8–20 h, frágil > 20 h. "
    "Limiares FEC: confiável ≤ 6/ano, regular 6–15/ano, frágil > 15/ano. "
    "Indicador estrutural de vulnerabilidade — não reflete culpa dos moradores. "
    "Forma a confirmar na 1ª busca real (ANEEL dados abertos — SANE-04, dupla face §17)."
)


@dataclass(frozen=True)
class LuzNoMapa:
    """Contrato: qualidade do fornecimento de energia elétrica por município."""

    codigo_ibge: str
    nome: str
    uf: str | None

    periodo: str | None  # YYYY do exercício mais recente com dado
    dec: float | None  # horas de interrupção por consumidor/ano
    fec: float | None  # interrupções por consumidor/ano
    nivel_dec: NivelEnergia
    nivel_fec: NivelEnergia


def classificar_nivel_energia(
    valor: float | None, *, limiar_confiavel: float, limiar_regular: float
) -> NivelEnergia:
    """Classifica o nível de qualidade de energia (DEC ou FEC — menor = melhor)."""
    if valor is None:
        return "sem_dado"
    if valor <= limiar_confiavel:
        return "confiavel"
    if valor <= limiar_regular:
        return "regular"
    return "fragil"


def classificar_dec(dec: float | None) -> NivelEnergia:
    return classificar_nivel_energia(
        dec, limiar_confiavel=_DEC_CONFIAVEL, limiar_regular=_DEC_REGULAR
    )


def classificar_fec(fec: float | None) -> NivelEnergia:
    return classificar_nivel_energia(
        fec, limiar_confiavel=_FEC_CONFIAVEL, limiar_regular=_FEC_REGULAR
    )


def calcular(
    codigo_ibge: str,
    nome: str,
    uf: str | None,
    *,
    periodo: str | None,
    dec: float | None,
    fec: float | None,
) -> LuzNoMapa:
    """Monta o LuzNoMapa a partir dos dados disponíveis; degrada graciosamente."""
    return LuzNoMapa(
        codigo_ibge=codigo_ibge,
        nome=nome,
        uf=uf,
        periodo=periodo,
        dec=dec,
        fec=fec,
        nivel_dec=classificar_dec(dec),
        nivel_fec=classificar_fec(fec),
    )
