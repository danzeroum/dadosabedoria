"""HAB-02 CasaViva — investimento público municipal em habitação (SICONFI Função 16).

Pergunta do produto: **quanto o município investe em habitação — e que sinal isso dá
sobre a atenção à moradia popular?**

Usa a despesa liquidada na função 16 (Habitação) do SICONFI Anexo I-E, dividida pela
população municipal, como proxy do compromisso orçamentário com política habitacional.
Déficit habitacional brasileiro estimado em ≥ 8 milhões de unidades (FGV/FJP).

Classificação por valor_por_hab (BRL/habitante/ano):
- ``expressivo`` : ≥ R$ 50/hab/ano
- ``moderado``   : ≥ R$ 10/hab/ano
- ``incipiente`` : > 0 mas < R$ 10/hab/ano, OU zero na função 16 mas SICONFI disponível
- ``sem_dado``   : sem dados SICONFI para o município (retorna 404)

HONESTIDADE:
- Função 16 (Habitação) inclui programas habitacionais municipais — obras, regularização
  fundiária, urbanização de assentamentos — mas NÃO inclui recursos do MCMV/FGTS
  (federais) que não transitam pelo orçamento municipal.
- Municípios metropolitanos podem centralizar o investimento em autarquias (COHABs) cujo
  orçamento pode ou não transitar pela função 16 municipal.
- Empenhar ≠ liquidar ≠ serviço entregue (ADR-0026).
- Lag típico: dados SICONFI do exercício T disponíveis em ~12 meses (março de T+1).
- Dupla face (§17): dado agregado por município — sem identificação de beneficiários
  ou famílias. (HAB-02)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

NivelHabitacao = Literal["expressivo", "moderado", "incipiente", "sem_dado"]

_LIMIAR_EXPRESSIVO = 50.0  # BRL/hab/ano
_LIMIAR_MODERADO = 10.0  # BRL/hab/ano

NOTA_HONESTA = (
    "Despesa liquidada na função 16 (Habitação) do orçamento municipal, por habitante. "
    "Fonte: SICONFI/STN (Anexo I-E — execução orçamentária por função). "
    "Proxy do compromisso municipal com política habitacional. "
    "Não inclui recursos federais (MCMV/FGTS) que não transitam pelo orçamento municipal. "
    "Municípios com COHABs podem apresentar subregistro na função 16. "
    "Empenhar ≠ serviço entregue (ADR-0026). "
    "Lag típico: ~12 meses após o exercício de referência. "
    "Dado agregado por município — sem identificação de beneficiários (HAB-02, dupla face §17)."
)


@dataclass(frozen=True)
class CasaViva:
    """Contrato: investimento municipal em habitação per capita."""

    codigo_ibge: str
    nome: str
    uf: str | None

    populacao: int | None
    ano: int | None
    valor_liquidado: float | None  # BRL — função 16 liquidado total
    valor_por_hab: float | None  # BRL/hab/ano
    nivel: NivelHabitacao


def classificar_nivel(valor_por_hab: float | None) -> NivelHabitacao:
    """Classifica o nível de investimento habitacional."""
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
) -> CasaViva:
    """Computa o CasaViva; degrada graciosamente com dado parcial."""
    por_hab: float | None = None
    if valor_liquidado is not None and populacao and populacao > 0:
        por_hab = round(valor_liquidado / populacao, 2)

    return CasaViva(
        codigo_ibge=codigo_ibge,
        nome=nome,
        uf=uf,
        populacao=populacao,
        ano=ano,
        valor_liquidado=valor_liquidado,
        valor_por_hab=por_hab,
        nivel=classificar_nivel(por_hab),
    )
