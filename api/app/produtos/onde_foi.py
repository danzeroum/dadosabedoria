"""OndeFoi (TRANSP-06) — execução por função, re-ancorado em **Liquidado ÷ Empenhado** (ADR-0029).

Lógica **pura** do denominador e da banda — o número que sustenta o produto, sem rede/DB. A
camada de API e a tela consomem isto; a esteira (`execucao_funcao`) alimenta os dados reais.

RE-ANCORAGEM (ADR-0029, default MODO DEV — aguarda referendo do dono): o #0 (ADR-0028) provou que
"recebido por função" **não existe** na fonte; o SICONFI classifica **despesa** por função (Anexo
I-E: Empenhado→Liquidado→Pago). Então o número é **liquidado/empenhado** por função: *"do que a
prefeitura empenhou (comprometeu) em cada área, quanto liquidou (virou despesa de fato)?"*.

HONESTIDADE (ADR-0026 mantido): **empenhar ≠ liquidar ≠ serviço entregue** — a banda é sinal de
**atenção** ("merece a pergunta"), nunca veredito. O conjunto de estados válido é
``{"valor", "sem_cobertura"}`` — orçamento por função é agregado público **sem PII**: o cadeado
``"suprimido"`` só vale com base legal de sigilo nomeada; senão é ``"sem_cobertura"``.
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
        return "alta"  # liquidou quase tudo que empenhou — confira se virou serviço
    if pct >= 55:
        return "parcial"
    return "baixa"  # liquidou pouco do que empenhou — merece a pergunta


@dataclass(frozen=True)
class FuncaoBruta:
    """Entrada por função: empenhado + liquidado (número divulgado, ou um estado sem valor)."""

    funcao: str
    empenhado: int  # despesa empenhada (comprometida) da função
    liquidado: int | EstadoSemValor  # número = despesa liquidada divulgada; senão o estado


@dataclass(frozen=True)
class FuncaoExecucao:
    """Empenhado × liquidado de uma função, já com estado e razão resolvidos."""

    funcao: str
    empenhado: int
    liquidado: int | None  # None onde ``exe_estado != "valor"``
    exe_estado: ExeEstado
    pct: int | None  # liquidado/empenhado (None onde não há valor)


@dataclass(frozen=True)
class ExecucaoMunicipio:
    """Resultado (ADR-0026/0029): % sobre a base divulgada, parcela fora **explícita**."""

    codigo_ibge: str
    nome: str
    uf: str
    empenhado_total: int  # contexto — **nunca** o denominador
    empenhado_base: int  # denominador do % (só funções com liquidação divulgada)
    empenhado_fora_base: int  # explícito: total − base (sem cobertura / não detalhado por função)
    liquidado: int  # numerador
    pct: int  # liquidado / empenhado_base
    banda: Banda
    funcoes: tuple[FuncaoExecucao, ...]


def calcular(
    codigo_ibge: str,
    nome: str,
    uf: str,
    empenhado_total: int,
    funcoes_brutas: list[FuncaoBruta],
) -> ExecucaoMunicipio:
    """Denominador do ADR-0026/0029: o ``%`` e o ``empenhado`` exibido usam a MESMA base divulgada.

    Numerador e denominador somam só as funções com liquidação divulgada (``liquidado`` numérico); a
    parcela fora dessa base sai em ``empenhado_fora_base`` (= total − base), nunca em silêncio.
    """
    funcoes: list[FuncaoExecucao] = []
    liquidado = 0
    empenhado_base = 0
    for fb in funcoes_brutas:
        if isinstance(fb.liquidado, int):
            liquidado += fb.liquidado
            empenhado_base += fb.empenhado  # só funções divulgadas entram na base
            funcoes.append(
                FuncaoExecucao(
                    funcao=fb.funcao,
                    empenhado=fb.empenhado,
                    liquidado=fb.liquidado,
                    exe_estado="valor",
                    pct=round(fb.liquidado / fb.empenhado * 100) if fb.empenhado else None,
                )
            )
        else:
            funcoes.append(
                FuncaoExecucao(
                    funcao=fb.funcao,
                    empenhado=fb.empenhado,
                    liquidado=None,
                    exe_estado=fb.liquidado,
                    pct=None,
                )
            )
    pct = round(liquidado / empenhado_base * 100) if empenhado_base else 0
    return ExecucaoMunicipio(
        codigo_ibge=codigo_ibge,
        nome=nome,
        uf=uf,
        empenhado_total=empenhado_total,
        empenhado_base=empenhado_base,
        empenhado_fora_base=empenhado_total - empenhado_base,
        liquidado=liquidado,
        pct=pct,
        banda=banda(pct),
        funcoes=tuple(funcoes),
    )
