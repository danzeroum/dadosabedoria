"""Giro Local (TRAB-03) — dinamismo econômico local per capita: emprego formal + crédito bancário.

Pergunta do produto: **como está a atividade econômica local em relação ao tamanho do município?**

Combina dois sinais complementares:
- **Saldo CAGED per 1000 hab** (fluxo): criação/destruição de emprego formal por residente.
- **Crédito ESTBAN per hab** (estoque): volume de crédito bancário em circulação por residente.

Juntos revelam o "giro" — municípios que criam empregos E têm crédito circulando têm maior
dinamismo local. A normalização per capita permite comparar cidades de portes diferentes,
ao contrário do Pulso Produtivo (que é temporal, dentro do próprio município).

HONESTIDADE:
- Emprego **formal** (CAGED): não capta informal (~40% da força de trabalho) nem autônomo.
- Crédito **bancário** (ESTBAN): não capta microcrédito informal, poupança ou capital próprio.
- Per capita usa a **população estimada** pelo IBGE: pode estar desatualizada.
- CAGED e ESTBAN têm **lags distintos** (~2 e ~3 meses): os períodos podem diferir.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

#: Nível de criação de emprego formal per 1000 hab (saldo CAGED do período).
NivelEmprego = Literal["criando", "estavel", "reduzindo", "sem_dado"]
#: Nível de crédito bancário per habitante (saldo ESTBAN do período).
NivelCredito = Literal["alto", "medio", "baixo", "sem_dado"]

# Referências de classificação do crédito (R$ por habitante).
_CREDITO_ALTO = 10_000.0  # acima de R$ 10k/hab → mercado financeiro desenvolvido
_CREDITO_BAIXO = 1_000.0  # abaixo de R$ 1k/hab → baixo acesso a crédito

NOTA_HONESTA = (
    "Giro Local combina emprego formal (Novo CAGED: admissões − desligamentos) e crédito bancário "
    "(ESTBAN/BCB: saldo de operações de crédito), ambos per capita. Emprego formal não capta "
    "trabalho informal nem autônomo. Crédito bancário não capta toda a atividade econômica "
    "(microcrédito informal, capital próprio). O per capita usa a população estimada pelo IBGE. "
    "CAGED e ESTBAN têm lags distintos (~2 e ~3 meses): os períodos podem diferir."
)


@dataclass(frozen=True)
class GiroLocal:
    """Contrato do Giro Local: dois sinais per capita que revelam o dinamismo econômico local."""

    codigo_ibge: str
    nome: str
    uf: str | None
    populacao: int | None

    # Emprego formal (CAGED)
    periodo_emprego: str | None  # YYYY-MM do último saldo disponível
    saldo_emprego: int | None  # admissões − desligamentos (fluxo mensal)
    saldo_emprego_per_1000: float | None  # saldo / populacao × 1000 (None se sem populacao)
    nivel_emprego: NivelEmprego

    # Crédito bancário (ESTBAN)
    periodo_credito: str | None  # YYYY-MM do último saldo disponível
    saldo_credito: int | None  # saldo total em R$ (None se sem dado)
    saldo_credito_per_hab: float | None  # saldo / populacao (None se sem populacao ou sem dado)
    nivel_credito: NivelCredito


def classificar_nivel_emprego(per_1000: float | None) -> NivelEmprego:
    """Nível de criação de emprego formal: sinal do fluxo per 1000 hab."""
    if per_1000 is None:
        return "sem_dado"
    if per_1000 > 0:
        return "criando"
    if per_1000 < 0:
        return "reduzindo"
    return "estavel"


def classificar_nivel_credito(per_hab: float | None) -> NivelCredito:
    """Nível de crédito bancário: estoque per capita vs. referências nacionais."""
    if per_hab is None:
        return "sem_dado"
    if per_hab >= _CREDITO_ALTO:
        return "alto"
    if per_hab >= _CREDITO_BAIXO:
        return "medio"
    return "baixo"


def calcular(
    codigo_ibge: str,
    nome: str,
    uf: str | None,
    populacao: int | None,
    *,
    periodo_emprego: str | None,
    saldo_emprego: int | None,
    periodo_credito: str | None,
    saldo_credito: int | None,
) -> GiroLocal:
    """Monta o Giro Local a partir dos dados disponíveis.

    Funciona com um componente só (sem dado de crédito → nível_credito='sem_dado').
    Não exige população — degrada para níveis em valor absoluto quando ausente.
    """
    # Per capita de emprego
    if saldo_emprego is not None and populacao and populacao > 0:
        emp_per_1000 = saldo_emprego / populacao * 1000
    else:
        emp_per_1000 = None

    # Nível de emprego: usa per capita quando possível; fallback no sinal absoluto
    if emp_per_1000 is not None:
        nivel_emprego = classificar_nivel_emprego(emp_per_1000)
    elif saldo_emprego is not None:
        nivel_emprego = classificar_nivel_emprego(float(saldo_emprego))
    else:
        nivel_emprego = "sem_dado"

    # Per capita de crédito
    if saldo_credito is not None and populacao and populacao > 0:
        cred_per_hab = saldo_credito / populacao
    else:
        cred_per_hab = None

    nivel_credito = classificar_nivel_credito(cred_per_hab)

    return GiroLocal(
        codigo_ibge=codigo_ibge,
        nome=nome,
        uf=uf,
        populacao=populacao,
        periodo_emprego=periodo_emprego,
        saldo_emprego=saldo_emprego,
        saldo_emprego_per_1000=round(emp_per_1000, 2) if emp_per_1000 is not None else None,
        nivel_emprego=nivel_emprego,
        periodo_credito=periodo_credito,
        saldo_credito=saldo_credito,
        saldo_credito_per_hab=round(cred_per_hab, 0) if cred_per_hab is not None else None,
        nivel_credito=nivel_credito,
    )
