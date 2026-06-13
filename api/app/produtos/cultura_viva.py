"""CULT-01 CulturaViva — investimento público municipal em cultura (SICONFI Função 13).

Pergunta do produto: **quanto o município investe em cultura — e que sinal isso dá sobre o
compromisso com a vida cultural local?**

Usa a despesa liquidada na função 13 (Cultura) do SICONFI Anexo I-E, dividida pela população
municipal, como proxy do esforço orçamentário com equipamentos e políticas culturais.

Classificação por valor_por_hab (BRL/habitante/ano):
- ``expressivo`` : ≥ R$ 30/hab/ano
- ``moderado``   : ≥ R$ 10/hab/ano
- ``incipiente`` : > 0 mas < R$ 10/hab/ano, OU zero na função 13 mas SICONFI disponível
- ``sem_dado``   : sem dados SICONFI para o município (retorna 404)

HONESTIDADE:
- Função 13 (Cultura) inclui bibliotecas, museus, teatros, centros culturais, eventos e
  patrimônio histórico sob responsabilidade da prefeitura. Não inclui patrocínios de empresas
  estatais, recursos da Lei Rouanet nem fundos estaduais/federais fora do orçamento municipal.
- Municípios turísticos ou com equipamentos culturais relevantes tendem a investir mais
  per capita; compare municípios de perfil semelhante.
- Empenhar ≠ liquidar ≠ serviço entregue (ADR-0026).
- Lag típico: dados SICONFI do exercício T disponíveis em ~12 meses (março de T+1).
- Dupla face (§17): dado agregado por município — sem identificação de pessoas. (CULT-01)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

NivelCultura = Literal["expressivo", "moderado", "incipiente", "sem_dado"]

_LIMIAR_EXPRESSIVO = 30.0  # BRL/hab/ano
_LIMIAR_MODERADO = 10.0  # BRL/hab/ano

NOTA_HONESTA = (
    "Despesa liquidada na função 13 (Cultura) do orçamento municipal, por habitante. "
    "Fonte: SICONFI/STN (Anexo I-E — execução orçamentária por função). "
    "Proxy do compromisso municipal com equipamentos e políticas culturais locais. "
    "Não inclui recursos da Lei Rouanet nem fundos estaduais/federais fora do orçamento municipal. "
    "Municípios turísticos ou com equipamentos culturais relevantes tendem a investir mais. "
    "Empenhar ≠ serviço entregue (ADR-0026). "
    "Lag típico: ~12 meses após o exercício de referência. "
    "Dado agregado por município — sem identificação de pessoas (CULT-01, dupla face §17)."
)


@dataclass(frozen=True)
class CulturaViva:
    """Contrato: investimento municipal em cultura per capita."""

    codigo_ibge: str
    nome: str
    uf: str | None

    populacao: int | None
    ano: int | None
    valor_liquidado: float | None  # BRL — função 13 liquidado total
    valor_por_hab: float | None  # BRL/hab/ano
    nivel: NivelCultura


def classificar_nivel(valor_por_hab: float | None) -> NivelCultura:
    """Classifica o nível de investimento em cultura."""
    if valor_por_hab is None:
        return "sem_dado"
    if valor_por_hab >= _LIMIAR_EXPRESSIVO:
        return "expressivo"
    if valor_por_hab >= _LIMIAR_MODERADO:
        return "moderado"
    return "incipiente"


def calcular(
    codigo_ibge: str,
    nome: str,
    uf: str | None,
    populacao: int | None,
    *,
    ano: int | None,
    valor_liquidado: float | None,
) -> CulturaViva:
    """Computa o CulturaViva; degrada graciosamente com dado parcial."""
    por_hab: float | None = None
    if valor_liquidado is not None and populacao and populacao > 0:
        por_hab = round(valor_liquidado / populacao, 2)

    return CulturaViva(
        codigo_ibge=codigo_ibge,
        nome=nome,
        uf=uf,
        populacao=populacao,
        ano=ano,
        valor_liquidado=valor_liquidado,
        valor_por_hab=por_hab,
        nivel=classificar_nivel(por_hab),
    )
