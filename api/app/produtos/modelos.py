"""Modelos Pydantic dos produtos nomeados: OndeFoi (``/v1/onde-foi``) e Pulso Produtivo
(``/v1/pulso-produtivo``)."""

from __future__ import annotations

from pydantic import BaseModel

from app.indicadores.modelos import MetaProveniencia
from app.produtos.onde_foi import Banda, ExeEstado
from app.produtos.pulso_produtivo import Pulso, Tendencia


class FuncaoOut(BaseModel):
    funcao: str
    recebido: int
    exe: int | None  # None onde exe_estado != "valor"
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
    """Recebido × execução por função. % sobre a base divulgada; parcela fora explícita."""

    codigo_ibge: str
    nome: str
    uf: str
    recebido_total: int  # contexto — nunca o denominador
    recebido_base: int  # denominador do %
    recebido_fora_base: int  # explícito: total − base
    executado: int
    pct: int
    banda: Banda
    funcoes: list[FuncaoOut]
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
