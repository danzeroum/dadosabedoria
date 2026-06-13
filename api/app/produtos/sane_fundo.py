"""SANE-05 SaneFundo — investimento público municipal em saneamento (SICONFI Função 17).

Pergunta do produto: **quanto o município investe diretamente em saneamento — e que sinal
isso dá sobre o compromisso orçamentário local com água e esgoto?**

Usa a despesa liquidada na função 17 (Saneamento) do SICONFI Anexo I-E, dividida pela
população municipal, como proxy do esforço orçamentário em saneamento básico.

Classificação por valor_por_hab (BRL/habitante/ano):
- ``expressivo`` : ≥ R$ 60/hab/ano
- ``moderado``   : ≥ R$ 15/hab/ano
- ``incipiente`` : > 0 mas < R$ 15/hab/ano, OU zero na função 17 mas SICONFI disponível
- ``sem_dado``   : sem dados SICONFI para o município (retorna 404)

HONESTIDADE:
- Função 17 (Saneamento) inclui obras de água, esgoto e resíduos sólidos urbanos de
  responsabilidade direta da prefeitura. Não inclui investimentos de concessionárias
  estaduais (SABESP, COPASA etc.) nem do Programa de Aceleração do Crescimento (PAC)
  que transitam fora do orçamento municipal.
- Em municípios com concessão a empresa estadual, o gasto municipal na função 17 pode
  ser próximo de zero mesmo com boa cobertura — use em conjunto com AguaViva (SANE-01).
- Empenhar ≠ liquidar ≠ serviço entregue (ADR-0026).
- Lag típico: dados SICONFI do exercício T disponíveis em ~12 meses (março de T+1).
- Dupla face (§17): dado agregado por município — sem identificação de pessoas. (SANE-05)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

NivelSaneamento = Literal["expressivo", "moderado", "incipiente", "sem_dado"]

_LIMIAR_EXPRESSIVO = 60.0  # BRL/hab/ano
_LIMIAR_MODERADO = 15.0  # BRL/hab/ano

NOTA_HONESTA = (
    "Despesa liquidada na função 17 (Saneamento) do orçamento municipal, por habitante. "
    "Fonte: SICONFI/STN (Anexo I-E — execução orçamentária por função). "
    "Proxy do esforço orçamentário municipal direto com saneamento básico. "
    "Não inclui investimentos de concessionárias estaduais (SABESP, COPASA) nem do PAC "
    "fora do orçamento municipal — municípios concedidos podem ter gasto próximo de zero. "
    "Use em conjunto com AguaViva (SANE-01) para contexto de cobertura real. "
    "Empenhar ≠ serviço entregue (ADR-0026). "
    "Lag típico: ~12 meses após o exercício de referência. "
    "Dado agregado por município — sem identificação de pessoas (SANE-05, dupla face §17)."
)


@dataclass(frozen=True)
class SaneFundo:
    """Contrato: investimento municipal em saneamento per capita."""

    codigo_ibge: str
    nome: str
    uf: str | None

    populacao: int | None
    ano: int | None
    valor_liquidado: float | None  # BRL — função 17 liquidado total
    valor_por_hab: float | None  # BRL/hab/ano
    nivel: NivelSaneamento


def classificar_nivel(valor_por_hab: float | None) -> NivelSaneamento:
    """Classifica o nível de investimento em saneamento."""
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
) -> SaneFundo:
    """Computa o SaneFundo; degrada graciosamente com dado parcial."""
    por_hab: float | None = None
    if valor_liquidado is not None and populacao and populacao > 0:
        por_hab = round(valor_liquidado / populacao, 2)

    return SaneFundo(
        codigo_ibge=codigo_ibge,
        nome=nome,
        uf=uf,
        populacao=populacao,
        ano=ano,
        valor_liquidado=valor_liquidado,
        valor_por_hab=por_hab,
        nivel=classificar_nivel(por_hab),
    )
