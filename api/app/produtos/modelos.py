"""Modelos Pydantic dos produtos nomeados: OndeFoi, Pulso Produtivo, Giro Local, Salário Radar,
Bússola Educação-Trabalho (EDU-01), Sentinela Respiratória (SAUDE-01)."""

from __future__ import annotations

from pydantic import BaseModel

from app.indicadores.modelos import MetaProveniencia
from app.produtos.bussola_edu_trabalho import NivelEducacao
from app.produtos.giro_local import NivelCredito, NivelEmprego
from app.produtos.onde_foi import Banda, ExeEstado
from app.produtos.pulso_produtivo import Pulso, Tendencia
from app.produtos.regiao_emprega import NivelRegiao
from app.produtos.salario_radar import NivelSalario
from app.produtos.sentinela_resp import NivelSentinela, TendenciaSentinela


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


# ----------------------------------------------------------------- Salário Radar (TRAB-02)


class SalarioRadarOut(BaseModel):
    """Nível salarial das novas contratações formais (Novo CAGED) por município/mês."""

    codigo_ibge: str
    nome: str
    uf: str | None
    periodo: str | None  # YYYY-MM do último dado disponível
    salario_medio: float | None  # média R$ das admissões; None se sem dado
    nivel: NivelSalario
    nota: str
    meta: MetaProveniencia


# ----------------------------------------------------------------- Região Emprega (TRAB-04)


class MunicipioEmpregoOut(BaseModel):
    """Saldo de emprego formal de um município no período regional."""

    codigo_ibge: str
    nome: str
    populacao: int | None
    saldo: int | None  # None = sem dado
    per_1000: float | None
    nivel: NivelEmprego


class RegiaoEmpregaOut(BaseModel):
    """Retrato regional do emprego formal (Novo CAGED) — TRAB-04."""

    codigo_ibge: str  # código IBGE da UF (ex.: "35" para SP)
    nome: str
    uf: str  # sigla (ex.: "SP")
    periodo: str | None  # YYYY-MM do período agregado
    saldo_total: int
    municipios_criando: int
    municipios_estaveis: int
    municipios_reduzindo: int
    municipios_sem_dado: int
    municipios_total: int
    nivel: NivelRegiao
    municipios: list[MunicipioEmpregoOut]
    nota: str
    meta: MetaProveniencia


# ------------------------------------------------- Bússola Educação-Trabalho (EDU-01)


class BussolaEduTrabOut(BaseModel):
    """Bússola Educação-Trabalho: base educacional (INEP) + mercado de trabalho formal (CAGED)."""

    codigo_ibge: str
    nome: str
    uf: str | None
    populacao: int | None

    # Educação (INEP — anual)
    periodo_educacao: str | None  # YYYY
    matriculas: int | None
    matriculas_por_mil: float | None
    nivel_educacao: NivelEducacao

    # Emprego formal (CAGED — mensal)
    periodo_emprego: str | None  # YYYY-MM
    saldo_emprego: int | None
    nivel_emprego: NivelEmprego

    # Salário médio das admissões (CAGED — mensal)
    salario_medio: float | None
    nivel_salario: NivelSalario

    nota: str
    meta_educacao: MetaProveniencia | None
    meta_emprego: MetaProveniencia | None
    meta_salario: MetaProveniencia | None


# ---------------------------------------------- Sentinela Respiratória (SAUDE-01)


class MesInternacoesOut(BaseModel):
    periodo: str  # YYYY-MM
    internacoes: int | None  # None = suprimido (k-anonimato)
    suprimido: bool


class SentinelaRespOut(BaseModel):
    """Internações respiratórias SUS por município/mês com supressão honesta (SAUDE-01)."""

    codigo_ibge: str
    nome: str
    uf: str | None
    populacao: int | None

    periodo: str | None  # YYYY-MM do dado mais recente
    internacoes: int | None  # None se suprimido ou sem dado
    internacoes_por_100k: float | None  # None se suprimido ou sem população
    suprimido: bool
    nivel: NivelSentinela
    tendencia: TendenciaSentinela | None  # None com < 2 meses reais

    meses: list[MesInternacoesOut]  # série histórica (inclui meses suprimidos)
    nota: str
    meta: MetaProveniencia | None
