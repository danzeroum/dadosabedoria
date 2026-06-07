"""Pulso Produtivo (TRAB-01) — leitura honesta do saldo de emprego formal (Novo CAGED).

Pergunta do produto: **como está o pulso do emprego formal no meu município?** O sinal é o
``saldo`` mensal do Novo CAGED (admissões − desligamentos com carteira). Lógica **pura** — o número
que sustenta o produto, sem rede/DB; a API alimenta com a série já no ar via ``/v1/valores``.

HONESTIDADE (mesma régua do OndeFoi, ADR-0026):
- É emprego **formal** (carteira): **não** capta trabalho informal nem autônomo.
- Fluxo mensal **volátil e sazonal**: uma batida não é veredito — saldo negativo **merece a
  pergunta**, não é diagnóstico.
- Saldo é **fluxo** (não normalizado ao estoque de empregos): compara melhor no tempo dentro do
  município do que entre municípios de portes diferentes.
- Saldo CAGED é agregado público sem PII (``n_minimo=0``): **sem cadeado de privacidade** — todo mês
  divulgado é ``valor`` (não se finge proteção que não há).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

#: Nível do pulso = sinal da batida atual (saldo do último mês). Não é veredito (ver módulo).
Pulso = Literal["aquecido", "estavel", "esfriando"]
#: Momento = o último mês comparado ao anterior (acelera/desacelera). ``None`` com 1 só mês.
Tendencia = Literal["melhorando", "estavel", "piorando"]

#: Enquadramento honesto exibido com o produto (ver docstring do módulo).
NOTA_HONESTA = (
    "Saldo do emprego formal (carteira, Novo CAGED): admissões − desligamentos. Não capta trabalho "
    "informal nem autônomo. É um fluxo mensal volátil e sazonal — uma batida não é veredito; saldo "
    "negativo merece a pergunta, não é diagnóstico. Por ser fluxo (não normalizado ao estoque de "
    "empregos), compara melhor no tempo dentro do município do que entre municípios de portes "
    "diferentes."
)


@dataclass(frozen=True)
class MesSaldo:
    """Uma batida: o saldo divulgado de um mês."""

    periodo: str  # YYYY-MM
    saldo: int  # admissões − desligamentos no mês


@dataclass(frozen=True)
class PulsoMunicipio:
    """Resultado do contrato: a batida atual + o momento + a janela como contexto explícito."""

    codigo_ibge: str
    nome: str
    uf: str | None
    periodo: str  # último mês (YYYY-MM)
    saldo_mes: int  # saldo do último mês = a batida atual
    saldo_acumulado: int  # soma da janela disponível (contexto, NÃO veredito)
    pulso: Pulso  # nível: sinal do saldo do mês
    tendencia: Tendencia | None  # momento: mês vs mês anterior (None se só 1 mês)
    meses_positivos: int
    meses_negativos: int
    meses: tuple[MesSaldo, ...]  # a série, para o usuário ver a volatilidade (não esconder)


def classificar_pulso(saldo_mes: int) -> Pulso:
    """Nível da batida atual: positivo aquece, negativo esfria, zero é estável."""
    if saldo_mes > 0:
        return "aquecido"
    if saldo_mes < 0:
        return "esfriando"
    return "estavel"


def classificar_tendencia(saldo_mes: int, saldo_anterior: int) -> Tendencia:
    """Momento: a batida atual comparada à anterior (pode esfriar **e** melhorar — desacelerar)."""
    if saldo_mes > saldo_anterior:
        return "melhorando"
    if saldo_mes < saldo_anterior:
        return "piorando"
    return "estavel"


def calcular(
    codigo_ibge: str,
    nome: str,
    uf: str | None,
    meses: list[MesSaldo],
) -> PulsoMunicipio:
    """Monta o pulso a partir da série de meses divulgados (ordenada por período, não-vazia).

    A rota garante ≥1 mês (senão 404). O nível vem do último mês; o momento, do último vs o
    penúltimo; a janela inteira é devolvida como contexto — a volatilidade não é escondida.
    """
    if not meses:  # guarda defensiva; a rota não deve chamar sem dado.
        raise ValueError("pulso requer ao menos um mês divulgado")
    ultimo = meses[-1]
    saldo_acumulado = sum(m.saldo for m in meses)
    tendencia = classificar_tendencia(ultimo.saldo, meses[-2].saldo) if len(meses) >= 2 else None
    return PulsoMunicipio(
        codigo_ibge=codigo_ibge,
        nome=nome,
        uf=uf,
        periodo=ultimo.periodo,
        saldo_mes=ultimo.saldo,
        saldo_acumulado=saldo_acumulado,
        pulso=classificar_pulso(ultimo.saldo),
        tendencia=tendencia,
        meses_positivos=sum(1 for m in meses if m.saldo > 0),
        meses_negativos=sum(1 for m in meses if m.saldo < 0),
        meses=tuple(meses),
    )
