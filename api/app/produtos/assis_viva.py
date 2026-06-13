"""SOCIAL-01 AssisViva — investimento público municipal em assistência social (SICONFI Função 08).

Pergunta do produto: **quanto o município investe diretamente em assistência social — e que sinal
isso dá sobre o compromisso com a população em situação de vulnerabilidade?**

Usa a despesa liquidada na função 08 (Assistência Social) do SICONFI Anexo I-E, dividida
pela população municipal, como proxy do esforço orçamentário direto com políticas de proteção.

Classificação por valor_por_hab (BRL/habitante/ano):
- ``expressivo`` : ≥ R$ 150/hab/ano
- ``moderado``   : ≥ R$ 50/hab/ano
- ``incipiente`` : > 0 mas < R$ 50/hab/ano, OU zero na função 08 mas SICONFI disponível
- ``sem_dado``   : sem dados SICONFI para o município (retorna 404)

HONESTIDADE:
- Função 08 (Assistência Social) inclui CRAS/CREAS, benefícios municipais, ações do SUAS.
  Não inclui transferências federais (Bolsa Família, BPC) que não transitam pelo orçamento
  municipal liquidado — municípios com alto SUAS estadual/federal podem ter gasto municipal baixo.
- Compare municípios de porte e perfil semelhante; cidades-polo de assistência social tendem
  a ter maior gasto per capita por receberem demanda regional.
- Empenhar ≠ liquidar ≠ serviço entregue (ADR-0026).
- Lag típico: dados SICONFI do exercício T disponíveis em ~12 meses (março de T+1).
- Dupla face (§17): dado agregado por município — sem identificação de pessoas. (SOCIAL-01)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

NivelAssistencia = Literal["expressivo", "moderado", "incipiente", "sem_dado"]

_LIMIAR_EXPRESSIVO = 150.0  # BRL/hab/ano
_LIMIAR_MODERADO = 50.0  # BRL/hab/ano

NOTA_HONESTA = (
    "Despesa liquidada na função 08 (Assistência Social) do orçamento municipal, por habitante. "
    "Fonte: SICONFI/STN (Anexo I-E — execução orçamentária por função). "
    "Proxy do compromisso municipal com proteção social básica (CRAS/CREAS/SUAS). "
    "Não inclui transferências federais (Bolsa Família, BPC) fora do orçamento municipal. "
    "Municípios-polo de assistência tendem a ter maior gasto per capita por demanda regional. "
    "Empenhar ≠ serviço entregue (ADR-0026). "
    "Lag típico: ~12 meses após o exercício de referência. "
    "Dado agregado por município — sem identificação de pessoas (SOCIAL-01, dupla face §17)."
)


@dataclass(frozen=True)
class AssisViva:
    """Contrato: investimento municipal em assistência social per capita."""

    codigo_ibge: str
    nome: str
    uf: str | None

    populacao: int | None
    ano: int | None
    valor_liquidado: float | None  # BRL — função 08 liquidado total
    valor_por_hab: float | None  # BRL/hab/ano
    nivel: NivelAssistencia


def classificar_nivel(valor_por_hab: float | None) -> NivelAssistencia:
    """Classifica o nível de investimento em assistência social."""
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
) -> AssisViva:
    """Computa o AssisViva; degrada graciosamente com dado parcial."""
    por_hab: float | None = None
    if valor_liquidado is not None and populacao and populacao > 0:
        por_hab = round(valor_liquidado / populacao, 2)

    return AssisViva(
        codigo_ibge=codigo_ibge,
        nome=nome,
        uf=uf,
        populacao=populacao,
        ano=ano,
        valor_liquidado=valor_liquidado,
        valor_por_hab=por_hab,
        nivel=classificar_nivel(por_hab),
    )
