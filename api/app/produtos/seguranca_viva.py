"""SEG-01 SegurançaViva — investimento público municipal em segurança pública (SICONFI Função 06).

Pergunta do produto: **quanto o município investe diretamente em segurança pública — e que sinal
isso dá sobre o compromisso com a guarda civil municipal e a defesa civil local?**

Usa a despesa liquidada na função 06 (Segurança Pública) do SICONFI Anexo I-E, dividida
pela população municipal, como proxy do esforço orçamentário direto com segurança pública.

Classificação por valor_por_hab (BRL/habitante/ano):
- ``expressivo`` : ≥ R$ 100/hab/ano
- ``moderado``   : ≥ R$ 30/hab/ano
- ``incipiente`` : > 0 mas < R$ 30/hab/ano, OU zero na função 06 mas SICONFI disponível
- ``sem_dado``   : sem dados SICONFI para o município (retorna 404)

HONESTIDADE:
- Função 06 (Segurança Pública) cobre gastos municipais com Guarda Civil Municipal (GCM),
  Defesa Civil, policiamento comunitário e sistemas de monitoramento sob responsabilidade
  da prefeitura. Não inclui gastos estaduais com PM/PC nem gastos federais com PF/PRF — a
  maior parte da segurança pública no Brasil é custeada pelos estados, não municípios.
- Municípios com GCM estruturada (SP, Campinas, Guarulhos) tendem a ter gasto muito maior;
  municípios sem GCM podem ter gasto próximo de zero mesmo com boa cobertura estadual.
- Empenhar ≠ liquidar ≠ serviço entregue (ADR-0026).
- Lag típico: dados SICONFI do exercício T disponíveis em ~12 meses (março de T+1).
- Dupla face (§17): dado agregado por município — sem identificação de pessoas. (SEG-01)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

NivelSeguranca = Literal["expressivo", "moderado", "incipiente", "sem_dado"]

_LIMIAR_EXPRESSIVO = 100.0  # BRL/hab/ano
_LIMIAR_MODERADO = 30.0  # BRL/hab/ano

NOTA_HONESTA = (
    "Despesa liquidada na função 06 (Segurança Pública) do orçamento municipal, por habitante. "
    "Fonte: SICONFI/STN (Anexo I-E — execução orçamentária por função). "
    "Proxy do compromisso municipal com GCM, Defesa Civil e monitoramento local. "
    "Não inclui gastos estaduais (PM/PC) nem federais (PF/PRF) — a maior parte da segurança "
    "pública no Brasil é custeada pelos estados. Municípios sem GCM podem ter gasto próximo "
    "de zero mesmo com cobertura policial estadual adequada. "
    "Empenhar ≠ serviço entregue (ADR-0026). "
    "Lag típico: ~12 meses após o exercício de referência. "
    "Dado agregado por município — sem identificação de pessoas (SEG-01, dupla face §17)."
)


@dataclass(frozen=True)
class SegurancaViva:
    """Contrato: investimento municipal em segurança pública per capita."""

    codigo_ibge: str
    nome: str
    uf: str | None

    populacao: int | None
    ano: int | None
    valor_liquidado: float | None  # BRL — função 06 liquidado total
    valor_por_hab: float | None  # BRL/hab/ano
    nivel: NivelSeguranca


def classificar_nivel(valor_por_hab: float | None) -> NivelSeguranca:
    """Classifica o nível de investimento em segurança pública."""
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
) -> SegurancaViva:
    """Computa o SegurançaViva; degrada graciosamente com dado parcial."""
    por_hab: float | None = None
    if valor_liquidado is not None and populacao and populacao > 0:
        por_hab = round(valor_liquidado / populacao, 2)

    return SegurancaViva(
        codigo_ibge=codigo_ibge,
        nome=nome,
        uf=uf,
        populacao=populacao,
        ano=ano,
        valor_liquidado=valor_liquidado,
        valor_por_hab=por_hab,
        nivel=classificar_nivel(por_hab),
    )
