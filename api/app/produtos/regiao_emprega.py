"""Região Emprega (TRAB-04) — retrato do emprego formal por estado/região.

Pergunta do produto: **como está o emprego formal na região? É um problema local ou generalizado?**

Agrega os saldos CAGED de todos os municípios de uma UF no último mês disponível e classifica a
região por nível de criação de empregos. Permite ao usuário contextualizar o resultado do próprio
município — se todos os municípios estão reduzindo, o problema é regional, não local.

HONESTIDADE:
- Cobre apenas o emprego **formal** (CAGED): não capta informal (~40% da força de trabalho).
- O saldo é **líquido** (admissões − desligamentos): município com saldo zero pode ter tido
  alta rotatividade, não necessariamente estabilidade real.
- Municípios sem dado no período ficam fora do cálculo agregado (transparência, não omissão).
- Lag típico do CAGED: ~40 dias após a competência.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

from app.produtos.giro_local import NivelEmprego, classificar_nivel_emprego

#: Nível agregado de criação de empregos da região no período.
NivelRegiao = Literal["criando", "estavel", "reduzindo", "sem_dado"]

NOTA_HONESTA = (
    "Região Emprega agrega os saldos do Novo CAGED (admissões − desligamentos) de todos os "
    "municípios do estado no último mês disponível. Um resultado negativo pode refletir "
    "sazonalidade ou reestruturação setorial regional — não é veredito sobre gestão. "
    "Emprego formal não capta "
    "trabalho informal (~40% da força de trabalho). Municípios sem dado no período ficam fora do "
    "cálculo e são listados como 'sem dado'. Lag típico do CAGED: ~40 dias após a competência."
)


@dataclass(frozen=True)
class MunicipioEmprego:
    """Saldo de emprego formal de um município no período regional."""

    codigo_ibge: str
    nome: str
    populacao: int | None
    saldo: int | None  # None = sem dado no período
    per_1000: float | None
    nivel: NivelEmprego


@dataclass(frozen=True)
class RegiaoEmprega:
    """Retrato regional do emprego formal (Novo CAGED) no último período disponível."""

    codigo_ibge: str  # código IBGE da UF (ex.: "35" para SP)
    nome: str  # nome da UF (ex.: "São Paulo")
    uf: str  # sigla (ex.: "SP")
    periodo: str | None  # YYYY-MM do período agregado

    saldo_total: int  # soma dos saldos de todos os municípios com dado
    municipios_criando: int  # count com saldo > 0
    municipios_estaveis: int  # count com saldo == 0
    municipios_reduzindo: int  # count com saldo < 0
    municipios_sem_dado: int  # count sem dado no período
    municipios_total: int  # count total de municípios da UF (com + sem dado)

    nivel: NivelRegiao
    municipios: list[MunicipioEmprego] = field(default_factory=list)


def classificar_nivel_regiao(saldo_total: int, n_com_dado: int) -> NivelRegiao:
    """Nível regional: sinal do saldo agregado dos municípios com dado."""
    if n_com_dado == 0:
        return "sem_dado"
    if saldo_total > 0:
        return "criando"
    if saldo_total < 0:
        return "reduzindo"
    return "estavel"


def calcular(
    codigo_ibge: str,
    nome: str,
    uf: str,
    *,
    periodo: str | None,
    municipios_raw: list[tuple[str, str, int | None, int | None]],
) -> RegiaoEmprega:
    """Monta a Região Emprega a partir dos dados dos municípios.

    ``municipios_raw`` é uma lista de ``(codigo_ibge, nome, populacao, saldo_ou_None)``.
    Saldo ``None`` = município sem dado no período.
    """
    municipios: list[MunicipioEmprego] = []
    saldo_total = 0
    criando = estavel = reduzindo = sem_dado = 0

    for cod, nom, pop, saldo in municipios_raw:
        if saldo is None:
            sem_dado += 1
            municipios.append(
                MunicipioEmprego(
                    codigo_ibge=cod,
                    nome=nom,
                    populacao=pop,
                    saldo=None,
                    per_1000=None,
                    nivel="sem_dado",
                )
            )
            continue

        # Per 1000 hab
        if pop and pop > 0:
            per_1000 = round(saldo / pop * 1000, 2)
        else:
            per_1000 = None

        nivel: NivelEmprego
        if per_1000 is not None:
            nivel = classificar_nivel_emprego(per_1000)
        else:
            nivel = classificar_nivel_emprego(float(saldo))

        saldo_total += saldo
        if saldo > 0:
            criando += 1
        elif saldo < 0:
            reduzindo += 1
        else:
            estavel += 1

        municipios.append(
            MunicipioEmprego(
                codigo_ibge=cod,
                nome=nom,
                populacao=pop,
                saldo=saldo,
                per_1000=per_1000,
                nivel=nivel,
            )
        )

    n_com_dado = criando + estavel + reduzindo
    nivel_regiao = classificar_nivel_regiao(saldo_total, n_com_dado)

    return RegiaoEmprega(
        codigo_ibge=codigo_ibge,
        nome=nome,
        uf=uf,
        periodo=periodo,
        saldo_total=saldo_total,
        municipios_criando=criando,
        municipios_estaveis=estavel,
        municipios_reduzindo=reduzindo,
        municipios_sem_dado=sem_dado,
        municipios_total=len(municipios_raw),
        nivel=nivel_regiao,
        municipios=municipios,
    )
