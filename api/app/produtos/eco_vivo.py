"""AMB-01 EcoVivo — investimento público municipal em gestão ambiental (SICONFI Função 18).

Pergunta do produto: **quanto o município investe em meio ambiente — e que sinal isso dá
sobre a prioridade dada à proteção ambiental local?**

Usa a despesa liquidada na função 18 (Gestão Ambiental) do SICONFI Anexo I-E, dividida
pela população municipal, como proxy do compromisso orçamentário com políticas ambientais.

Classificação por valor_por_hab (BRL/habitante/ano):
- ``expressivo`` : ≥ R$ 30/hab/ano
- ``moderado``   : ≥ R$ 5/hab/ano
- ``incipiente`` : > 0 mas < R$ 5/hab/ano, OU zero na função 18 mas SICONFI disponível
- ``sem_dado``   : sem dados SICONFI para o município (retorna 404)

HONESTIDADE:
- Função 18 (Gestão Ambiental) inclui licenciamento ambiental municipal, parques/unidades
  de conservação locais, resíduos sólidos e drenagem pluvial sob responsabilidade da
  prefeitura. Não inclui recursos de órgãos estaduais/federais de meio ambiente
  (IBAMA, ICMBio) que não transitam pelo orçamento municipal.
- Municípios com áreas verdes relevantes ou atividade econômica de impacto ambiental
  tendem a ter maior gasto na função 18; compare municípios com perfil semelhante.
- Empenhar ≠ liquidar ≠ serviço entregue (ADR-0026).
- Lag típico: dados SICONFI do exercício T disponíveis em ~12 meses (março de T+1).
- Dupla face (§17): dado agregado por município — sem identificação de pessoas. (AMB-01)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

NivelAmbiental = Literal["expressivo", "moderado", "incipiente", "sem_dado"]

_LIMIAR_EXPRESSIVO = 30.0  # BRL/hab/ano
_LIMIAR_MODERADO = 5.0  # BRL/hab/ano

NOTA_HONESTA = (
    "Despesa liquidada na função 18 (Gestão Ambiental) do orçamento municipal, por habitante. "
    "Fonte: SICONFI/STN (Anexo I-E — execução orçamentária por função). "
    "Proxy do compromisso municipal com proteção ambiental local. "
    "Não inclui recursos federais/estaduais (IBAMA, ICMBio) fora do orçamento municipal. "
    "Empenhar ≠ serviço entregue (ADR-0026). "
    "Lag típico: ~12 meses após o exercício de referência. "
    "Dado agregado por município — sem identificação de pessoas (AMB-01, dupla face §17)."
)


@dataclass(frozen=True)
class EcoVivo:
    """Contrato: investimento municipal em gestão ambiental per capita."""

    codigo_ibge: str
    nome: str
    uf: str | None

    populacao: int | None
    ano: int | None
    valor_liquidado: float | None  # BRL — função 18 liquidado total
    valor_por_hab: float | None  # BRL/hab/ano
    nivel: NivelAmbiental


def classificar_nivel(valor_por_hab: float | None) -> NivelAmbiental:
    """Classifica o nível de investimento em gestão ambiental."""
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
) -> EcoVivo:
    """Computa o EcoVivo; degrada graciosamente com dado parcial."""
    por_hab: float | None = None
    if valor_liquidado is not None and populacao and populacao > 0:
        por_hab = round(valor_liquidado / populacao, 2)

    return EcoVivo(
        codigo_ibge=codigo_ibge,
        nome=nome,
        uf=uf,
        populacao=populacao,
        ano=ano,
        valor_liquidado=valor_liquidado,
        valor_por_hab=por_hab,
        nivel=classificar_nivel(por_hab),
    )
