"""Modelos Pydantic dos produtos nomeados: OndeFoi, Pulso Produtivo e Giro Local."""

from __future__ import annotations

from pydantic import BaseModel

from app.indicadores.modelos import MetaProveniencia
from app.produtos.giro_local import NivelCredito, NivelEmprego
from app.produtos.onde_foi import Banda, ExeEstado
from app.produtos.pulso_produtivo import Pulso, Tendencia


class FuncaoOut(BaseModel):
    funcao: str
    empenhado: int
    liquidado: int | None  # None onde exe_estado != "valor"
    exe_estado: ExeEstado
    pct: int | None


class FonteOut(BaseModel):
    sigla: str
    nome: str
    orgao: str
    dominio: str
    ate: str
    atraso: str  # descrição do atraso por fonte (ex.: "~75 dias após o bimestre")


class MetaOndeFoi(BaseModel):
    metodologia: str  # "execução orçamentária, NÃO serviço entregue" (ADR-0026)
    versao_metodologia: str
    periodo: str
    periodo_rotulo: str  # "exercício X" — selo de frescor derivado daqui (não hardcoded)
    atraso_dias: int
    licenca: str  # licença/atribuição da fonte (selo de confiança)
    fontes: list[FonteOut]


class OndeFoiOut(BaseModel):
    """Liquidado ÷ empenhado por função (ADR-0029); % sobre a base divulgada, fora explícito."""

    codigo_ibge: str
    nome: str
    uf: str
    empenhado_total: int  # contexto — nunca o denominador
    empenhado_base: int  # denominador do %
    empenhado_fora_base: int  # explícito: total − base
    liquidado: int
    pct: int
    banda: Banda
    funcoes: list[FuncaoOut]
    meta: MetaOndeFoi


class OndeFoiResumo(BaseModel):
    """Resumo por município para o diretório (lista) do OndeFoi — sem detalhe por função."""

    codigo_ibge: str
    nome: str
    uf: str
    pct: int
    banda: Banda


class OndeFoiLista(BaseModel):
    """Diretório de municípios do OndeFoi, ordenado por NOME (não ranking de execução).

    Dupla-face §17: nada de leaderboard — dados reais da fato ``execucao_funcao``."""

    dados: list[OndeFoiResumo]
    meta: MetaOndeFoi


# ----------------------------------------------------------------- Pulso Produtivo (TRAB-01)


class MesSaldoOut(BaseModel):
    periodo: str  # YYYY-MM
    saldo: int


class PulsoProdutivoOut(BaseModel):
    """Pulso do emprego formal (Novo CAGED): a batida atual + o momento + a janela como contexto."""

    codigo_ibge: str
    nome: str
    uf: str | None
    periodo: str  # último mês (YYYY-MM)
    saldo_mes: int  # batida atual
    saldo_acumulado: int  # contexto — soma da janela, NÃO veredito
    pulso: Pulso
    tendencia: Tendencia | None
    meses_positivos: int
    meses_negativos: int
    meses: list[MesSaldoOut]
    nota: str  # enquadramento honesto do produto (formal, fluxo volátil, merece a pergunta)
    meta: MetaProveniencia


# ----------------------------------------------------------------- Giro Local (TRAB-03)


class GiroLocalOut(BaseModel):
    """Dinamismo econômico local per capita: emprego formal (CAGED) + crédito bancário (ESTBAN)."""

    codigo_ibge: str
    nome: str
    uf: str | None
    populacao: int | None

    # Emprego formal (CAGED)
    periodo_emprego: str | None  # YYYY-MM do último saldo disponível
    saldo_emprego: int | None
    saldo_emprego_per_1000: float | None
    nivel_emprego: NivelEmprego

    # Crédito bancário (ESTBAN)
    periodo_credito: str | None
    saldo_credito: int | None
    saldo_credito_per_hab: float | None
    nivel_credito: NivelCredito

    nota: str
    meta_emprego: MetaProveniencia | None
    meta_credito: MetaProveniencia | None
