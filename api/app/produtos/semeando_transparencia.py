"""SemeandoTransparência (ALIM-05) — investimento público municipal em agricultura (SICONFI).

Pergunta do produto: **quanto o município investe em agricultura e política alimentar?**

Usa a despesa liquidada na função 20 (Agricultura) do SICONFI Anexo I-E, dividida pela
população municipal, para classificar o compromisso orçamentário com o setor agrícola.

Classificação por valor_por_hab (BRL/habitante/ano):
- ``alto``     : ≥ R$ 100/hab/ano
- ``moderado`` : ≥ R$ 10/hab/ano
- ``baixo``    : > 0 mas < R$ 10/hab/ano, OU zero na função 20 mas SICONFI disponível
- ``sem_dado`` : sem dados SICONFI para o município (retorna 404)

HONESTIDADE:
- Função 20 (Agricultura) cobre políticas agrícolas municipais; não inclui transferências
  a produtores, subsídios federais ou gastos do estado/União — é o esforço da prefeitura.
- Municipalidades predominantemente urbanas naturalmente investem pouco em função 20.
  Compare municípios com perfil semelhante, não todos contra todos.
- Empenhar ≠ liquidar ≠ serviço entregue — o valor liquidado é compromisso financeiro
  concretizado, não entrega de serviço agrícola (ADR-0026).
- Lag típico: dados SICONFI do exercício T disponíveis em ~12 meses (março de T+1).
- Dupla face (§17): variação natural por vocação agrícola do município. (ALIM-05)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

NivelInvestimento = Literal["alto", "moderado", "baixo", "sem_dado"]

_LIMIAR_ALTO = 100.0  # BRL/hab/ano
_LIMIAR_MODERADO = 10.0  # BRL/hab/ano

NOTA_HONESTA = (
    "Despesa liquidada na função 20 (Agricultura) do orçamento municipal, por habitante. "
    "Fonte: SICONFI/STN (Anexo I-E — execução orçamentária por função). "
    "Função 20 cobre políticas agrícolas municipais; não inclui subsídios federais. "
    "Municípios predominantemente urbanos naturalmente investem menos em agricultura — compare "
    "municípios com perfil semelhante. Empenhar ≠ serviço entregue (ADR-0026). "
    "Dado disponível ~12 meses após o exercício de referência (ALIM-05, dupla face §17)."
)


@dataclass(frozen=True)
class SemeandoTransparencia:
    """Contrato: investimento municipal em agricultura per capita."""

    codigo_ibge: str
    nome: str
    uf: str | None

    populacao: int | None
    ano: int | None  # exercício de referência
    valor_liquidado: float | None  # BRL — função 20 liquidado total
    valor_por_hab: float | None  # BRL/hab/ano
    nivel: NivelInvestimento


def classificar_nivel(valor_por_hab: float | None) -> NivelInvestimento:
    """Classifica o nível de investimento em agricultura."""
    if valor_por_hab is None:
        return "sem_dado"
    if valor_por_hab >= _LIMIAR_ALTO:
        return "alto"
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
) -> SemeandoTransparencia:
    """Computa o SemeandoTransparência; degrada graciosamente com dado parcial."""
    por_hab: float | None = None
    if valor_liquidado is not None and populacao and populacao > 0:
        por_hab = round(valor_liquidado / populacao, 2)

    return SemeandoTransparencia(
        codigo_ibge=codigo_ibge,
        nome=nome,
        uf=uf,
        populacao=populacao,
        ano=ano,
        valor_liquidado=valor_liquidado,
        valor_por_hab=por_hab,
        nivel=classificar_nivel(por_hab),
    )
