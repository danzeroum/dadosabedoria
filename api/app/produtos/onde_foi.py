"""OndeFoi (TRANSP-06) — contrato do indicador de execução por função (ADR-0026).

Lógica **pura** do denominador e da banda — o número que sustenta o produto, sem rede/DB. A
camada de API e a tela consomem isto; a esteira e a validação real no #0 alimentam os dados.

HONESTIDADE (ADR-0026): execução orçamentária (empenho/liquidação), **não** serviço entregue. O
conjunto de estados válido do OndeFoi é ``{"valor", "sem_cobertura"}`` — orçamento por função é
agregado público **sem PII**: ``"suprimido"`` (cadeado de privacidade) só vale com base legal de
sigilo nomeada; senão, função faltante é ``"sem_cobertura"`` (não se finge proteção que não há).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

#: Estado da célula (campo irmão aditivo, ADR-0026). O primitivo carrega os três; **quais são
#: válidos é por indicador** — no OndeFoi, ``{"valor", "sem_cobertura"}``.
ExeEstado = Literal["valor", "suprimido", "sem_cobertura"]
EstadoSemValor = Literal["suprimido", "sem_cobertura"]
Banda = Literal["alta", "parcial", "baixa", "indef"]


def banda(pct: int | None) -> Banda:
    """Banda de execução = sinal de **atenção** ("merece a pergunta"), não veredito (ADR-0026)."""
    if pct is None:
        return "indef"
    if pct >= 80:
        return "alta"  # executou quase tudo — confira se virou serviço
    if pct >= 55:
        return "parcial"
    return "baixa"  # executou pouco do que recebeu — merece a pergunta


@dataclass(frozen=True)
class FuncaoBruta:
    """Entrada por função: recebido + execução (número divulgado, ou um estado sem valor)."""

    funcao: str
    recebido: int  # recurso da função
    exe: int | EstadoSemValor  # número = despesa liquidada divulgada; senão o estado


@dataclass(frozen=True)
class FuncaoExecucao:
    """Recebido × executado de uma função, já com estado e razão resolvidos."""

    funcao: str
    recebido: int
    exe: int | None  # None onde ``exe_estado != "valor"``
    exe_estado: ExeEstado
    pct: int | None  # exe/recebido (None onde não há valor)


@dataclass(frozen=True)
class ExecucaoMunicipio:
    """Resultado do contrato (ADR-0026): % sobre a base divulgada, parcela fora **explícita**."""

    codigo_ibge: str
    nome: str
    uf: str
    recebido_total: int  # contexto — **nunca** o denominador
    recebido_base: int  # denominador do % (só funções divulgadas)
    recebido_fora_base: int  # explícito: total − base (protegido/sem cobertura/não detalhado)
    executado: int  # numerador
    pct: int  # executado / recebido_base
    banda: Banda
    funcoes: tuple[FuncaoExecucao, ...]


def calcular(
    codigo_ibge: str,
    nome: str,
    uf: str,
    recebido_total: int,
    funcoes_brutas: list[FuncaoBruta],
) -> ExecucaoMunicipio:
    """Denominador do ADR-0026: o ``%`` e o ``recebido`` exibido usam a MESMA base divulgada.

    Numerador e denominador somam só as funções com valor divulgado (``exe`` numérico); a parcela
    fora dessa base é exposta em ``recebido_fora_base`` (= total − base), nunca tirada em silêncio.
    """
    funcoes: list[FuncaoExecucao] = []
    executado = 0
    recebido_base = 0
    for fb in funcoes_brutas:
        if isinstance(fb.exe, int):
            executado += fb.exe
            recebido_base += fb.recebido  # só funções divulgadas entram na base
            funcoes.append(
                FuncaoExecucao(
                    funcao=fb.funcao,
                    recebido=fb.recebido,
                    exe=fb.exe,
                    exe_estado="valor",
                    pct=round(fb.exe / fb.recebido * 100) if fb.recebido else None,
                )
            )
        else:
            funcoes.append(
                FuncaoExecucao(
                    funcao=fb.funcao,
                    recebido=fb.recebido,
                    exe=None,
                    exe_estado=fb.exe,
                    pct=None,
                )
            )
    pct = round(executado / recebido_base * 100) if recebido_base else 0
    return ExecucaoMunicipio(
        codigo_ibge=codigo_ibge,
        nome=nome,
        uf=uf,
        recebido_total=recebido_total,
        recebido_base=recebido_base,
        recebido_fora_base=recebido_total - recebido_base,
        executado=executado,
        pct=pct,
        banda=banda(pct),
        funcoes=tuple(funcoes),
    )
