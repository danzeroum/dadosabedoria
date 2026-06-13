"""SAUDE-11 Pressão no SUS — investimento público municipal em saúde (SICONFI).

Pergunta do produto: **quanto o município investe em saúde — e que pressão isso exerce
sobre os profissionais do SUS?**

Usa a despesa liquidada na função 10 (Saúde) do SICONFI Anexo I-E, dividida pela
população municipal, como proxy da capacidade financeira do sistema de saúde local.
Baixo financiamento por habitante → estrutura de saúde sobrecarregada → maior risco
de burnout entre profissionais (SAUDE-11, dupla face §17).

Classificação por valor_por_hab (BRL/habitante/ano):
- ``adequado`` : ≥ R$ 500/hab/ano
- ``atenção``  : ≥ R$ 200/hab/ano
- ``crítico``  : > 0 mas < R$ 200/hab/ano, OU zero na função 10 mas SICONFI disponível
- ``sem_dado`` : sem dados SICONFI para o município (retorna 404)

HONESTIDADE:
- Função 10 (Saúde) inclui toda despesa liquidada em saúde pela prefeitura — APS,
  hospitais, vigilância, medicamentos — mas NÃO inclui recursos estaduais/federais
  repassados diretamente a unidades sem trânsito pelo orçamento municipal.
- Dado de burnout real requer CAT/INSS (Comunicação de Acidente de Trabalho) —
  fonte restrita, gate pendente. Este produto é um proxy estrutural.
- Lei 141/2012 obriga municípios a aplicar mínimo 15% da receita em saúde;
  municípios abaixo de R$ 200/hab podem estar em descumprimento.
- Lag típico: dados SICONFI do exercício T disponíveis em ~12 meses (março de T+1).
- Empenhar ≠ liquidar ≠ serviço entregue (ADR-0026).
- Dupla face (§17): dado agregado por município; sem identificação de profissionais.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

NivelPressaoSus = Literal["adequado", "atenção", "crítico", "sem_dado"]

_LIMIAR_ADEQUADO = 500.0  # BRL/hab/ano
_LIMIAR_ATENCAO = 200.0  # BRL/hab/ano

NOTA_HONESTA = (
    "Despesa liquidada na função 10 (Saúde) do orçamento municipal, por habitante. "
    "Fonte: SICONFI/STN (Anexo I-E — execução orçamentária por função). "
    "Proxy de capacidade do SUS local: financiamento baixo → sistema sobrecarregado → "
    "maior risco de burnout entre profissionais. Dado real de burnout requer CAT/INSS "
    "(fonte restrita, gate pendente). "
    "Lei 141/2012 exige mínimo 15% da receita em saúde. "
    "Empenhar ≠ serviço entregue (ADR-0026). "
    "Lag típico: ~12 meses após o exercício de referência. "
    "Dado agregado por município — sem identificação de profissionais (SAUDE-11, dupla face §17)."
)


@dataclass(frozen=True)
class PressaoSus:
    """Contrato: capacidade de financiamento do SUS local."""

    codigo_ibge: str
    nome: str
    uf: str | None

    populacao: int | None
    ano: int | None
    valor_liquidado: float | None  # BRL — função 10 liquidado total
    valor_por_hab: float | None  # BRL/hab/ano
    nivel: NivelPressaoSus


def classificar_nivel(valor_por_hab: float | None) -> NivelPressaoSus:
    """Classifica o nível de pressão/adequação do financiamento."""
    if valor_por_hab is None:
        return "sem_dado"
    if valor_por_hab >= _LIMIAR_ADEQUADO:
        return "adequado"
    if valor_por_hab >= _LIMIAR_ATENCAO:
        return "atenção"
    return "crítico"


def calcular(
    codigo_ibge: str,
    nome: str,
    uf: str | None,
    populacao: int | None,
    *,
    ano: int | None,
    valor_liquidado: float | None,
) -> PressaoSus:
    """Computa o PressaoSus; degrada graciosamente com dado parcial."""
    por_hab: float | None = None
    if valor_liquidado is not None and populacao and populacao > 0:
        por_hab = round(valor_liquidado / populacao, 2)

    return PressaoSus(
        codigo_ibge=codigo_ibge,
        nome=nome,
        uf=uf,
        populacao=populacao,
        ano=ano,
        valor_liquidado=valor_liquidado,
        valor_por_hab=por_hab,
        nivel=classificar_nivel(por_hab),
    )
