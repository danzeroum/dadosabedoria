"""EsgotoInvisível (SANE-03) — gap entre cobertura de água e esgoto por município (SNIS/MDR).

Pergunta do produto: **onde a água chega mas o esgoto some?**

No Brasil, a cobertura de abastecimento de água é sistematicamente superior à de coleta de
esgoto. O "esgoto invisível" é o efluente que vai para rios, solo e corpos d'água sem
tratamento — invisível nas estatísticas porque não é coletado, não porque não existe.

Usa ``saneamento.agua.atendimento_pct`` (IN023_AE) e ``saneamento.esgoto.coleta_pct``
(IN015_AE) do SNIS. Lógica **pura** — sem rede/DB.

HONESTIDADE:
- Gap = água_pct − esgoto_pct; onde apenas esgoto estiver disponível, gap = 0.
- IN015_AE mede **coleta**, não tratamento — esgoto coletado pode não ser tratado.
- Municípios sem prestador declarante ao SNIS aparecem sem dado.
- Dado anual com lag típico de 12–18 meses.
- Dupla face (§17): indicador estrutural de vulnerabilidade ambiental e de saúde —
  não ranking de gestão municipal. (SANE-03)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

NivelGap = Literal["adequado", "atencao", "critico", "sem_dado"]

# Limiar de alerta para cobertura de esgoto (%).
# Abaixo disso, grande parte do efluente vai para o ambiente sem coleta.
_LIMIAR_ADEQUADO_ESGOTO = 70.0  # ≥ 70 %: coleta satisfatória
_LIMIAR_ATENCAO_ESGOTO = 40.0  # 40–69 %: déficit expressivo
# < 40 %: crítico — maioria do efluente não coletada

NOTA_HONESTA = (
    "Gap de saneamento = cobertura de água (IN023_AE) menos coleta de esgoto (IN015_AE) "
    "do SNIS (MDR). Mede onde a água chega mas o esgoto não é coletado — o 'esgoto "
    "invisível' que vai para rios e solo sem tratamento. IN015_AE mede coleta, não "
    "tratamento; o impacto real pode ser ainda maior. Municípios sem prestador declarante "
    "ao SNIS aparecem sem dado. Dado anual com lag típico de 12–18 meses. "
    "Indicador estrutural — não reflete gestão individual. (SANE-03, dupla face §17)."
)


@dataclass(frozen=True)
class EsgotoInvisivel:
    """Contrato: gap de saneamento por município."""

    codigo_ibge: str
    nome: str
    uf: str | None

    periodo: str | None
    agua_pct: float | None  # IN023_AE, 0–100 %
    esgoto_pct: float | None  # IN015_AE, 0–100 %
    gap_pct: float | None  # água_pct − esgoto_pct (≥ 0 quando ambos disponíveis)
    nivel_gap: NivelGap


def calcular_gap(agua_pct: float | None, esgoto_pct: float | None) -> float | None:
    """Calcula o gap entre água e esgoto (diferença percentual)."""
    if esgoto_pct is None:
        return None
    if agua_pct is None:
        return max(0.0, -esgoto_pct)  # não faz sentido; retorna 0 na prática
    return max(0.0, agua_pct - esgoto_pct)


def classificar_nivel(esgoto_pct: float | None) -> NivelGap:
    """Classifica o nível do gap com base na cobertura de esgoto."""
    if esgoto_pct is None:
        return "sem_dado"
    if esgoto_pct >= _LIMIAR_ADEQUADO_ESGOTO:
        return "adequado"
    if esgoto_pct >= _LIMIAR_ATENCAO_ESGOTO:
        return "atencao"
    return "critico"


def calcular(
    codigo_ibge: str,
    nome: str,
    uf: str | None,
    *,
    periodo: str | None,
    agua_pct: float | None,
    esgoto_pct: float | None,
) -> EsgotoInvisivel:
    """Monta o EsgotoInvisivel; degrada graciosamente sem dado parcial."""
    return EsgotoInvisivel(
        codigo_ibge=codigo_ibge,
        nome=nome,
        uf=uf,
        periodo=periodo,
        agua_pct=agua_pct,
        esgoto_pct=esgoto_pct,
        gap_pct=calcular_gap(agua_pct, esgoto_pct),
        nivel_gap=classificar_nivel(esgoto_pct),
    )
