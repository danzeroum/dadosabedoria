"""Modelos Pydantic dos produtos nomeados: OndeFoi, Pulso Produtivo, Giro Local, Salário Radar,
Bússola Educação-Trabalho (EDU-01), Sentinela Respiratória (SAUDE-01), ObraViva (TRANSP-05),
AguaViva (SANE-01), EsgotoInvisivel (SANE-03), LuzNoMapa (SANE-04), PratoFrio (ALIM-01),
CaçadorArboviroses (SAUDE-02), SentinelaMaterna (SAUDE-03), PressaoSus (SAUDE-11),
CasaViva (HAB-02), ViaViva (MOB-01), EcoVivo (AMB-01),
EscolaViva (EDU-03), SaneFundo (SANE-05),
AssisViva (SOCIAL-01), CulturaViva (CULT-01)."""

from __future__ import annotations

from pydantic import BaseModel

from app.indicadores.modelos import MetaProveniencia
from app.produtos.agua_viva import NivelAcesso
from app.produtos.assis_viva import NivelAssistencia
from app.produtos.bussola_edu_trabalho import NivelEducacao
from app.produtos.cacador_arboviroses import NivelArboviroses
from app.produtos.casa_viva import NivelHabitacao
from app.produtos.cultura_viva import NivelCultura
from app.produtos.eco_vivo import NivelAmbiental
from app.produtos.escola_viva import NivelEducacaoPublica
from app.produtos.esgoto_invisivel import NivelGap
from app.produtos.fome_oculta import NivelFomeOculta
from app.produtos.giro_local import NivelCredito, NivelEmprego
from app.produtos.luz_no_mapa import NivelEnergia
from app.produtos.obra_viva import NivelContratos
from app.produtos.onde_foi import Banda, ExeEstado
from app.produtos.prato_frio import NivelProducao
from app.produtos.pressao_sus import NivelPressaoSus
from app.produtos.pulso_produtivo import Pulso, Tendencia
from app.produtos.radar_evasao import NivelEvasao
from app.produtos.regiao_emprega import NivelRegiao
from app.produtos.rio_em_risco import NivelSeca
from app.produtos.salario_radar import NivelSalario
from app.produtos.sane_fundo import NivelSaneamento
from app.produtos.semeando_transparencia import NivelInvestimento
from app.produtos.sentinela_materna import NOTA_HONESTA as NOTA_SENTINELA_MATERNA
from app.produtos.sentinela_materna import NivelMaterno
from app.produtos.sentinela_resp import NivelSentinela, TendenciaSentinela
from app.produtos.via_viva import NivelTransporte


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


# ----------------------------------------------------------- Radar de Evasão (EDU-02)


class RadarEvasaoOut(BaseModel):
    """Cobertura do ensino fundamental municipal vs. pop. estimada em idade escolar (EDU-02)."""

    codigo_ibge: str
    nome: str
    uf: str | None
    populacao: int | None

    periodo: str | None  # YYYY do Censo Escolar
    matriculas: int | None
    matriculas_por_mil: float | None
    populacao_escolar_estimada: int | None  # populacao × 0,14
    taxa_cobertura: float | None  # %
    nivel: NivelEvasao

    nota: str
    meta: MetaProveniencia | None


# --------------------------------------------------------- ObraViva (TRANSP-05)


class ObraVivaOut(BaseModel):
    """Contratações públicas municipais via PNCP per capita (ObraViva — TRANSP-05)."""

    codigo_ibge: str
    nome: str
    uf: str | None
    populacao: int | None

    periodo: str | None  # YYYY do exercício mais recente
    valor_contratos: int | None  # R$ total dos contratos
    valor_por_hab: float | None  # R$/hab
    nivel: NivelContratos

    nota: str
    meta: MetaProveniencia | None


# --------------------------------------------------------- AguaViva (SANE-01)


class AguaVivaOut(BaseModel):
    """Saneamento básico municipal — SANE-01 AguaViva."""

    codigo_ibge: str
    nome: str
    uf: str | None

    periodo: str | None
    agua_pct: float | None
    esgoto_pct: float | None
    nivel_agua: NivelAcesso
    nivel_esgoto: NivelAcesso

    nota: str
    meta_agua: MetaProveniencia | None
    meta_esgoto: MetaProveniencia | None


# --------------------------------------------------------- EsgotoInvisivel (SANE-03)


class EsgotoInvisivelOut(BaseModel):
    """Gap de saneamento por município — SANE-03 EsgotoInvisível."""

    codigo_ibge: str
    nome: str
    uf: str | None

    periodo: str | None
    agua_pct: float | None
    esgoto_pct: float | None
    gap_pct: float | None  # água_pct − esgoto_pct; None quando esgoto ausente
    nivel_gap: NivelGap

    nota: str
    meta_esgoto: MetaProveniencia | None
    meta_agua: MetaProveniencia | None


# --------------------------------------------------------- LuzNoMapa (SANE-04)


class LuzNoMapaOut(BaseModel):
    """Qualidade do fornecimento de energia elétrica por município — SANE-04 LuzNoMapa."""

    codigo_ibge: str
    nome: str
    uf: str | None

    periodo: str | None
    dec: float | None  # horas de interrupção por consumidor/ano
    fec: float | None  # interrupções por consumidor/ano
    nivel_dec: NivelEnergia
    nivel_fec: NivelEnergia

    nota: str
    meta_dec: MetaProveniencia | None
    meta_fec: MetaProveniencia | None


# --------------------------------------------------------- RioEmRisco (SANE-02)


class RioEmRiscoOut(BaseModel):
    """Risco hídrico de seca por município — SANE-02 RioEmRisco."""

    codigo_ibge: str
    nome: str
    uf: str | None

    periodo: str | None
    seca_indice: float | None  # 0–5: Normal=0, D0=1, D1=2, D2=3, D3=4, D4=5
    nivel: NivelSeca

    nota: str
    meta: MetaProveniencia | None


# --------------------------------------------------------- PratoFrio (ALIM-01)


class PratoFrioOut(BaseModel):
    """Produção agrícola municipal per capita — ALIM-01 PratoFrio."""

    codigo_ibge: str
    nome: str
    uf: str | None
    populacao: int | None

    periodo: str | None  # YYYY do exercício
    valor_total: float | None  # BRL total (soma das lavouras)
    valor_por_hab: float | None  # BRL/hab/ano
    nivel: NivelProducao

    nota: str
    meta: MetaProveniencia | None


# ------------------------------------------------- FomeOculta (ALIM-02)


class FomeOcultaOut(BaseModel):
    """Insegurança nutricional de crianças < 5 anos — ALIM-02 Fome Oculta."""

    codigo_ibge: str
    nome: str
    uf: str | None
    populacao: int | None

    ano: int | None
    n_acompanhadas: int | None  # total de crianças acompanhadas (n_amostra)
    baixo_peso_pct: float | None  # % com magreza/magreza acentuada
    nivel: NivelFomeOculta

    nota: str
    meta: MetaProveniencia | None


# ------------------------------------------------- SemeandoTransparencia (ALIM-05)


class SemeandoTransparenciaOut(BaseModel):
    """Investimento público municipal em agricultura — ALIM-05 SemeandoTransparência."""

    codigo_ibge: str
    nome: str
    uf: str | None
    populacao: int | None

    ano: int | None  # exercício de referência
    valor_liquidado: float | None  # BRL — função 20 liquidado total
    valor_por_hab: float | None  # BRL/hab/ano
    nivel: NivelInvestimento

    nota: str
    meta: MetaProveniencia | None


# ------------------------------------------------- SentinelaMaterna (SAUDE-03)


class SentinelaMaternаOut(BaseModel):
    """Risco nutricional de gestantes — SAUDE-03 Sentinela Materna."""

    codigo_ibge: str
    nome: str
    uf: str | None
    populacao: int | None

    ano: int | None
    n_gestantes: int | None  # total de gestantes acompanhadas (n_amostra)
    gestante_baixo_peso_pct: float | None  # % com baixo peso
    nivel: NivelMaterno

    nota: str = NOTA_SENTINELA_MATERNA
    meta: MetaProveniencia | None


# ------------------------------------------------- CaçadorArboviroses (SAUDE-02)


class CacadorArboviroesOut(BaseModel):
    """Casos confirmados de dengue por 100k hab — SAUDE-02 Caçador de Arboviroses."""

    codigo_ibge: str
    nome: str
    uf: str | None
    populacao: int | None

    ano: int | None  # exercício de referência (ano de notificação)
    casos_confirmados: int | None  # contagem após k-anon (None = suprimido)
    incidencia_100k: float | None  # casos / pop × 100k; None sem população ou suprimido
    nivel: NivelArboviroses

    nota: str
    meta: MetaProveniencia | None


# ------------------------------------------------- PressaoSus (SAUDE-11)


class PressaoSusOut(BaseModel):
    """Capacidade de financiamento do SUS local — SAUDE-11 Pressão no SUS."""

    codigo_ibge: str
    nome: str
    uf: str | None
    populacao: int | None

    ano: int | None
    valor_liquidado: float | None  # BRL — função 10 liquidado total
    valor_por_hab: float | None  # BRL/hab/ano
    nivel: NivelPressaoSus

    nota: str
    meta: MetaProveniencia | None


# ------------------------------------------------- CasaViva (HAB-02)


class CasaVivaOut(BaseModel):
    """Investimento municipal em habitação per capita — HAB-02 CasaViva."""

    codigo_ibge: str
    nome: str
    uf: str | None
    populacao: int | None

    ano: int | None
    valor_liquidado: float | None  # BRL — função 16 liquidado total
    valor_por_hab: float | None  # BRL/hab/ano
    nivel: NivelHabitacao

    nota: str
    meta: MetaProveniencia | None


# ------------------------------------------------- EscolaViva (EDU-03)


class EscolaVivaOut(BaseModel):
    """Investimento municipal em educação per capita — EDU-03 EscolaViva."""

    codigo_ibge: str
    nome: str
    uf: str | None
    populacao: int | None

    ano: int | None
    valor_liquidado: float | None  # BRL — função 12 liquidado total
    valor_por_hab: float | None  # BRL/hab/ano
    nivel: NivelEducacaoPublica

    nota: str
    meta: MetaProveniencia | None


# ------------------------------------------------- SaneFundo (SANE-05)


class SaneFundoOut(BaseModel):
    """Investimento municipal em saneamento per capita — SANE-05 SaneFundo."""

    codigo_ibge: str
    nome: str
    uf: str | None
    populacao: int | None

    ano: int | None
    valor_liquidado: float | None  # BRL — função 17 liquidado total
    valor_por_hab: float | None  # BRL/hab/ano
    nivel: NivelSaneamento

    nota: str
    meta: MetaProveniencia | None


# ------------------------------------------------- ViaViva (MOB-01)


class ViaVivaOut(BaseModel):
    """Investimento municipal em transporte per capita — MOB-01 ViaViva."""

    codigo_ibge: str
    nome: str
    uf: str | None
    populacao: int | None

    ano: int | None
    valor_liquidado: float | None  # BRL — função 26 liquidado total
    valor_por_hab: float | None  # BRL/hab/ano
    nivel: NivelTransporte

    nota: str
    meta: MetaProveniencia | None


# ------------------------------------------------- EcoVivo (AMB-01)


class EcoVivaOut(BaseModel):
    """Investimento municipal em gestão ambiental per capita — AMB-01 EcoVivo."""

    codigo_ibge: str
    nome: str
    uf: str | None
    populacao: int | None

    ano: int | None
    valor_liquidado: float | None  # BRL — função 18 liquidado total
    valor_por_hab: float | None  # BRL/hab/ano
    nivel: NivelAmbiental

    nota: str
    meta: MetaProveniencia | None


# ------------------------------------------------- AssisViva (SOCIAL-01)


class AssisVivaOut(BaseModel):
    """Investimento municipal em assistência social per capita — SOCIAL-01 AssisViva."""

    codigo_ibge: str
    nome: str
    uf: str | None
    populacao: int | None

    ano: int | None
    valor_liquidado: float | None  # BRL — função 08 liquidado total
    valor_por_hab: float | None  # BRL/hab/ano
    nivel: NivelAssistencia

    nota: str
    meta: MetaProveniencia | None


# ------------------------------------------------- CulturaViva (CULT-01)


class CulturaVivaOut(BaseModel):
    """Investimento municipal em cultura per capita — CULT-01 CulturaViva."""

    codigo_ibge: str
    nome: str
    uf: str | None
    populacao: int | None

    ano: int | None
    valor_liquidado: float | None  # BRL — função 13 liquidado total
    valor_por_hab: float | None  # BRL/hab/ano
    nivel: NivelCultura

    nota: str
    meta: MetaProveniencia | None
