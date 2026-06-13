"""URB-01 CidadeViva — investimento público municipal em urbanismo (SICONFI Função 15).

Pergunta do produto: **quanto o município investe em urbanismo — e que sinal isso dá sobre
o compromisso com infraestrutura urbana, pavimentação, parques e iluminação pública?**

Usa a despesa liquidada na função 15 (Urbanismo) do SICONFI Anexo I-E, dividida pela
população municipal, como proxy do esforço orçamentário com o ambiente construído urbano.

Classificação por valor_por_hab (BRL/habitante/ano):
- ``expressivo`` : ≥ R$ 200/hab/ano
- ``moderado``   : ≥ R$ 80/hab/ano
- ``incipiente`` : > 0 mas < R$ 80/hab/ano, OU zero na função 15 mas SICONFI disponível
- ``sem_dado``   : sem dados SICONFI para o município (retorna 404)

HONESTIDADE:
- Função 15 (Urbanismo) inclui pavimentação, drenagem urbana, parques e praças, iluminação
  pública, limpeza urbana e ordenamento territorial sob responsabilidade da prefeitura.
  Não inclui obras estaduais/federais (rodovias, habitação PAC) fora do orçamento municipal.
- Municípios em fase de expansão urbana tendem a ter maior gasto per capita em urbanismo;
  compare com municípios de porte e taxa de crescimento semelhantes.
- Empenhar ≠ liquidar ≠ serviço entregue (ADR-0026).
- Lag típico: dados SICONFI do exercício T disponíveis em ~12 meses (março de T+1).
- Dupla face (§17): dado agregado por município — sem identificação de pessoas. (URB-01)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

NivelUrbanismo = Literal["expressivo", "moderado", "incipiente", "sem_dado"]

_LIMIAR_EXPRESSIVO = 200.0  # BRL/hab/ano
_LIMIAR_MODERADO = 80.0  # BRL/hab/ano

NOTA_HONESTA = (
    "Despesa liquidada na função 15 (Urbanismo) do orçamento municipal, por habitante. "
    "Fonte: SICONFI/STN (Anexo I-E — execução orçamentária por função). "
    "Proxy do compromisso municipal com infraestrutura urbana (pavimentação, parques, "
    "iluminação pública, drenagem e limpeza urbana). "
    "Não inclui obras estaduais/federais (rodovias, PAC) fora do orçamento municipal. "
    "Municípios em expansão urbana tendem a ter maior gasto per capita. "
    "Empenhar ≠ serviço entregue (ADR-0026). "
    "Lag típico: ~12 meses após o exercício de referência. "
    "Dado agregado por município — sem identificação de pessoas (URB-01, dupla face §17)."
)


@dataclass(frozen=True)
class CidadeViva:
    """Contrato: investimento municipal em urbanismo per capita."""

    codigo_ibge: str
    nome: str
    uf: str | None

    populacao: int | None
    ano: int | None
    valor_liquidado: float | None  # BRL — função 15 liquidado total
    valor_por_hab: float | None  # BRL/hab/ano
    nivel: NivelUrbanismo


def classificar_nivel(valor_por_hab: float | None) -> NivelUrbanismo:
    """Classifica o nível de investimento em urbanismo."""
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
) -> CidadeViva:
    """Computa o CidadeViva; degrada graciosamente com dado parcial."""
    por_hab: float | None = None
    if valor_liquidado is not None and populacao and populacao > 0:
        por_hab = round(valor_liquidado / populacao, 2)

    return CidadeViva(
        codigo_ibge=codigo_ibge,
        nome=nome,
        uf=uf,
        populacao=populacao,
        ano=ano,
        valor_liquidado=valor_liquidado,
        valor_por_hab=por_hab,
        nivel=classificar_nivel(por_hab),
    )
