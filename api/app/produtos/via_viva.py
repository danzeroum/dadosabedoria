"""MOB-01 ViaViva — investimento público municipal em transporte (SICONFI Função 26).

Pergunta do produto: **quanto o município investe em transporte e mobilidade urbana?**

Usa a despesa liquidada na função 26 (Transporte) do SICONFI Anexo I-E, dividida pela
população municipal, como proxy do compromisso orçamentário com infraestrutura de
transporte e mobilidade.

Classificação por valor_por_hab (BRL/habitante/ano):
- ``elevado``  : ≥ R$ 300/hab/ano
- ``moderado`` : ≥ R$ 80/hab/ano
- ``baixo``    : > 0 mas < R$ 80/hab/ano, OU zero na função 26 mas SICONFI disponível
- ``sem_dado`` : sem dados SICONFI para o município (retorna 404)

HONESTIDADE:
- Função 26 (Transporte) inclui estradas municipais, pontes, sinalização e apoio ao
  transporte público de responsabilidade da prefeitura. Não inclui obras estaduais/federais
  (rodovias, metrôs) custeadas fora do orçamento municipal.
- Municípios pequenos e rurais tendem a ter maior investimento per capita em manutenção de
  estradas vicinais; municípios urbanos concentram gasto em mobilidade/trânsito.
  Compare municípios com perfil semelhante, não todos contra todos.
- Empenhar ≠ liquidar ≠ serviço entregue (ADR-0026).
- Lag típico: dados SICONFI do exercício T disponíveis em ~12 meses (março de T+1).
- Dupla face (§17): dado agregado por município — sem identificação de beneficiários. (MOB-01)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

NivelTransporte = Literal["elevado", "moderado", "baixo", "sem_dado"]

_LIMIAR_ELEVADO = 300.0  # BRL/hab/ano
_LIMIAR_MODERADO = 80.0  # BRL/hab/ano

NOTA_HONESTA = (
    "Despesa liquidada na função 26 (Transporte) do orçamento municipal, por habitante. "
    "Fonte: SICONFI/STN (Anexo I-E — execução orçamentária por função). "
    "Proxy do compromisso municipal com infraestrutura de transporte e mobilidade. "
    "Não inclui obras estaduais/federais (rodovias, metrôs) fora do orçamento municipal. "
    "Municípios rurais tendem a investir mais per capita em estradas vicinais — compare "
    "municípios de perfil semelhante. Empenhar ≠ serviço entregue (ADR-0026). "
    "Lag típico: ~12 meses após o exercício de referência. "
    "Dado agregado por município — sem identificação de beneficiários (MOB-01, dupla face §17)."
)


@dataclass(frozen=True)
class ViaViva:
    """Contrato: investimento municipal em transporte per capita."""

    codigo_ibge: str
    nome: str
    uf: str | None

    populacao: int | None
    ano: int | None
    valor_liquidado: float | None  # BRL — função 26 liquidado total
    valor_por_hab: float | None  # BRL/hab/ano
    nivel: NivelTransporte


def classificar_nivel(valor_por_hab: float | None) -> NivelTransporte:
    """Classifica o nível de investimento em transporte."""
    if valor_por_hab is None:
        return "sem_dado"
    if valor_por_hab >= _LIMIAR_ELEVADO:
        return "elevado"
    if valor_por_hab >= _LIMIAR_MODERADO:
        return "moderado"
    return "baixo"


def calcular(
    codigo_ibge: str,
    nome: str,
    uf: str | None,
    populacao: int | None,
    *,
    ano: int | None,
    valor_liquidado: float | None,
) -> ViaViva:
    """Computa o ViaViva; degrada graciosamente com dado parcial."""
    por_hab: float | None = None
    if valor_liquidado is not None and populacao and populacao > 0:
        por_hab = round(valor_liquidado / populacao, 2)

    return ViaViva(
        codigo_ibge=codigo_ibge,
        nome=nome,
        uf=uf,
        populacao=populacao,
        ano=ano,
        valor_liquidado=valor_liquidado,
        valor_por_hab=por_hab,
        nivel=classificar_nivel(por_hab),
    )
