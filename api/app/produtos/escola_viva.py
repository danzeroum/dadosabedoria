"""EDU-03 EscolaViva — investimento público municipal em educação (SICONFI Função 12).

Pergunta do produto: **quanto o município investe em educação — e que sinal isso dá
sobre o compromisso orçamentário com o ensino público local?**

Usa a despesa liquidada na função 12 (Educação) do SICONFI Anexo I-E, dividida pela
população municipal, como proxy do esforço orçamentário em educação.

Classificação por valor_por_hab (BRL/habitante/ano):
- ``expressivo`` : ≥ R$ 600/hab/ano
- ``moderado``   : ≥ R$ 200/hab/ano
- ``incipiente`` : > 0 mas < R$ 200/hab/ano, OU zero na função 12 mas SICONFI disponível
- ``sem_dado``   : sem dados SICONFI para o município (retorna 404)

HONESTIDADE:
- Função 12 (Educação) inclui ensino fundamental e médio de responsabilidade municipal,
  alimentação escolar (PNAE), transporte escolar e creches municipais.
  Não inclui recursos federais do FNDE/FUNDEB que são repassados diretamente às escolas
  e não transitam integralmente pelo orçamento municipal liquidado aqui.
- Municípios com rede municipal maior (mais escolas próprias) tendem a ter maior gasto;
  compare com municípios de porte semelhante.
- Empenhar ≠ liquidar ≠ serviço entregue (ADR-0026).
- A Constituição Federal exige mínimo de 25% da receita municipal em educação —
  municípios abaixo do mínimo constitucional devem ser investigados.
- Lag típico: dados SICONFI do exercício T disponíveis em ~12 meses (março de T+1).
- Dupla face (§17): dado agregado por município — sem identificação de pessoas. (EDU-03)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

NivelEducacaoPublica = Literal["expressivo", "moderado", "incipiente", "sem_dado"]

_LIMIAR_EXPRESSIVO = 600.0  # BRL/hab/ano
_LIMIAR_MODERADO = 200.0  # BRL/hab/ano

NOTA_HONESTA = (
    "Despesa liquidada na função 12 (Educação) do orçamento municipal, por habitante. "
    "Fonte: SICONFI/STN (Anexo I-E — execução orçamentária por função). "
    "Proxy do esforço orçamentário municipal com o ensino público. "
    "Não inclui transferências federais (FNDE/FUNDEB) que não transitam pelo liquidado municipal. "
    "Municípios com rede municipal maior tendem a investir mais per capita. "
    "CF/88 exige mínimo de 25% da receita em educação. "
    "Empenhar ≠ serviço entregue (ADR-0026). "
    "Lag típico: ~12 meses após o exercício de referência. "
    "Dado agregado por município — sem identificação de pessoas (EDU-03, dupla face §17)."
)


@dataclass(frozen=True)
class EscolaViva:
    """Contrato: investimento municipal em educação per capita."""

    codigo_ibge: str
    nome: str
    uf: str | None

    populacao: int | None
    ano: int | None
    valor_liquidado: float | None  # BRL — função 12 liquidado total
    valor_por_hab: float | None  # BRL/hab/ano
    nivel: NivelEducacaoPublica


def classificar_nivel(valor_por_hab: float | None) -> NivelEducacaoPublica:
    """Classifica o nível de investimento em educação."""
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
) -> EscolaViva:
    """Computa o EscolaViva; degrada graciosamente com dado parcial."""
    por_hab: float | None = None
    if valor_liquidado is not None and populacao and populacao > 0:
        por_hab = round(valor_liquidado / populacao, 2)

    return EscolaViva(
        codigo_ibge=codigo_ibge,
        nome=nome,
        uf=uf,
        populacao=populacao,
        ano=ano,
        valor_liquidado=valor_liquidado,
        valor_por_hab=por_hab,
        nivel=classificar_nivel(por_hab),
    )
