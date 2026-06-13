"""Rotas dos produtos nomeados: OndeFoi, Pulso Produtivo (TRAB-01), Giro Local (TRAB-03),
Salário Radar (TRAB-02), Região Emprega (TRAB-04), Bússola Educação-Trabalho (EDU-01),
Sentinela Respiratória (SAUDE-01), ObraViva (TRANSP-05), AguaViva (SANE-01),
EsgotoInvisível (SANE-03), LuzNoMapa (SANE-04), RioEmRisco (SANE-02), PratoFrio (ALIM-01),
SemeandoTransparência (ALIM-05), FomeOculta (ALIM-02), SentinelaMaterna (SAUDE-03),
CaçadorArboviroses (SAUDE-02), PressaoSus (SAUDE-11), CasaViva (HAB-02),
ViaViva (MOB-01), EcoVivo (AMB-01), EscolaViva (EDU-03), SaneFundo (SANE-05),
AssisViva (SOCIAL-01), CulturaViva (CULT-01)."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_session
from app.produtos.facade import (
    AguaVivaFacade,
    AssisVivaFacade,
    BussolaEduTrabFacade,
    CacadorArbovirosesFacade,
    CasaVivaFacade,
    CulturaVivaFacade,
    EcoVivaFacade,
    EscolaVivaFacade,
    EsgotoInvisivelFacade,
    FomeOcultaFacade,
    GiroLocalFacade,
    LuzNoMapaFacade,
    ObraVivaFacade,
    PratoFrioFacade,
    PressaoSusFacade,
    PulsoProdutivoFacade,
    RadarEvasaoFacade,
    RegiaoEmpregaFacade,
    RioEmRiscoFacade,
    SalarioRadarFacade,
    SaneFundoFacade,
    SemeandoTransparenciaFacade,
    SentinelaMaternаFacade,
    SentinelaRespFacade,
    ViaVivaFacade,
)
from app.produtos.modelos import (
    AguaVivaOut,
    AssisVivaOut,
    BussolaEduTrabOut,
    CacadorArboviroesOut,
    CasaVivaOut,
    CulturaVivaOut,
    EcoVivaOut,
    EscolaVivaOut,
    EsgotoInvisivelOut,
    FomeOcultaOut,
    GiroLocalOut,
    LuzNoMapaOut,
    ObraVivaOut,
    OndeFoiLista,
    OndeFoiOut,
    PratoFrioOut,
    PressaoSusOut,
    PulsoProdutivoOut,
    RadarEvasaoOut,
    RegiaoEmpregaOut,
    RioEmRiscoOut,
    SalarioRadarOut,
    SaneFundoOut,
    SemeandoTransparenciaOut,
    SentinelaMaternаOut,
    SentinelaRespOut,
    ViaVivaOut,
)
from app.produtos.repositorio_onde_foi import RepositorioOndeFoi

router = APIRouter(prefix="/v1", tags=["produtos"])

_repo_onde_foi = RepositorioOndeFoi()


@router.get("/onde-foi", response_model=OndeFoiLista)
async def onde_foi_lista(session: AsyncSession = Depends(get_session)) -> OndeFoiLista:
    """Diretório dos municípios do OndeFoi — ordenado por nome (dupla-face §17, não ranking).

    Lista os municípios com dado real na fato ``execucao_funcao`` (SICONFI/Anexo I-E). Retorna
    lista vazia quando nenhum dado foi ingerido ainda.
    """
    return await _repo_onde_foi.listar(session)


@router.get("/onde-foi/{codigo_ibge}", response_model=OndeFoiOut)
async def onde_foi(codigo_ibge: str, session: AsyncSession = Depends(get_session)) -> OndeFoiOut:
    """Do que a prefeitura empenhou por função, quanto liquidou? (Liquidado÷Empenhado — ADR-0029).

    ``meta.metodologia`` enquadra: é execução **orçamentária** (empenhar≠liquidar≠serviço
    entregue). 404 quando não há dado para o município.
    """
    return await _repo_onde_foi.obter(session, codigo_ibge=codigo_ibge)


@router.get("/pulso-produtivo/{codigo_ibge}", response_model=PulsoProdutivoOut)
async def pulso_produtivo(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> PulsoProdutivoOut:
    """Como está o pulso do emprego formal no município? Saldo CAGED (admissões − desligamentos).

    Dado **real** do acervo (mesmo Repository de ``/v1/valores``). ``nota``/``meta`` enquadram:
    emprego **formal**, fluxo volátil/sazonal — saldo negativo merece a pergunta, não é veredito.
    """
    return await PulsoProdutivoFacade(session).pulso_produtivo(codigo_ibge=codigo_ibge)


@router.get("/giro-local/{codigo_ibge}", response_model=GiroLocalOut)
async def giro_local(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> GiroLocalOut:
    """Dinamismo econômico local per capita: criação de emprego formal + crédito bancário.

    Combina CAGED (saldo/1000 hab) e ESTBAN (crédito/hab) para comparação entre municípios de
    portes diferentes. 404 quando não há nenhum dado disponível para o município.
    """
    return await GiroLocalFacade(session).giro_local(codigo_ibge=codigo_ibge)


@router.get("/salario-radar/{codigo_ibge}", response_model=SalarioRadarOut)
async def salario_radar(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> SalarioRadarOut:
    """Nível salarial das novas contratações formais no município (Salário Radar — TRAB-02).

    Salário médio declarado nas admissões do Novo CAGED do último mês disponível. Revela o
    patamar salarial da demanda por trabalho formal local — não o salário médio da população.
    404 quando não há dado para o município.
    """
    return await SalarioRadarFacade(session).salario_radar(codigo_ibge=codigo_ibge)


@router.get("/regiao-emprega/{codigo_ibge}", response_model=RegiaoEmpregaOut)
async def regiao_emprega(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> RegiaoEmpregaOut:
    """Retrato do emprego formal de toda a UF no último mês disponível (Região Emprega — TRAB-04).

    Aceita o código IBGE de uma UF (ex.: ``35`` para SP) ou de um município (ex.: ``3550308``).
    Agrega o saldo CAGED de todos os municípios da UF no mesmo período, revelando se a criação ou
    destruição de empregos é local ou regional. 404 quando não há dado para a UF.
    """
    return await RegiaoEmpregaFacade(session).regiao_emprega(codigo_ibge=codigo_ibge)


@router.get("/bussola-edu-trabalho/{codigo_ibge}", response_model=BussolaEduTrabOut)
async def bussola_edu_trabalho(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> BussolaEduTrabOut:
    """Base educacional e mercado de trabalho formal do município (Bússola EDU-01).

    Combina matrículas do ensino fundamental (INEP/Censo Escolar, anual) com o saldo de emprego
    formal e o salário médio das admissões (CAGED, mensal). A relação é de CONTEXTO, não causal.
    404 quando não há nenhum dado disponível para o município.
    """
    return await BussolaEduTrabFacade(session).bussola_edu_trabalho(codigo_ibge=codigo_ibge)


@router.get("/sentinela-resp/{codigo_ibge}", response_model=SentinelaRespOut)
async def sentinela_resp(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> SentinelaRespOut:
    """Internações respiratórias SUS do município por mês (Sentinela Respiratória — SAUDE-01).

    Contagem de AIH com diagnóstico no grupo J do CID-10 (J00–J99) no SIH/SUS. Dado de
    **origem sensível**: células abaixo de 5 internações são protegidas pelo k-anonimato
    (ADR-0004) — aparecem com ``suprimido=true`` e ``internacoes=null``, nunca como zero.
    404 quando não há nenhum dado disponível para o município.
    """
    return await SentinelaRespFacade(session).sentinela_resp(codigo_ibge=codigo_ibge)


@router.get("/radar-evasao/{codigo_ibge}", response_model=RadarEvasaoOut)
async def radar_evasao(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> RadarEvasaoOut:
    """Cobertura do ensino fundamental vs. estimativa de crianças em idade escolar (EDU-02).

    Matrículas do Censo Escolar/INEP divididas por 14 % da pop. municipal (proxy faixa 6–14 anos).
    Taxa > 100 % indica polo de atração escolar — classifica como "adequada", não erro.
    Só cobre o fundamental formal (não EJA, creche, pré-escola).
    404 quando não há dado de matrículas para o município.
    """
    return await RadarEvasaoFacade(session).radar_evasao(codigo_ibge=codigo_ibge)


@router.get("/obra-viva/{codigo_ibge}", response_model=ObraVivaOut)
async def obra_viva(codigo_ibge: str, session: AsyncSession = Depends(get_session)) -> ObraVivaOut:
    """Contratações públicas municipais via PNCP per capita (ObraViva — TRANSP-05).

    Soma do valor global de contratos publicados no PNCP pelo município no exercício. Cobre
    todos os tipos (obras, serviços, bens) — uso como contexto de intensidade de contratação.
    Nota: PNCP ainda não tem adesão universal — ausência ≠ ausência de contratação.
    404 quando não há dado de contratos para o município.
    """
    return await ObraVivaFacade(session).obra_viva(codigo_ibge=codigo_ibge)


@router.get("/agua-viva/{codigo_ibge}", response_model=AguaVivaOut)
async def agua_viva(codigo_ibge: str, session: AsyncSession = Depends(get_session)) -> AguaVivaOut:
    """Acesso a água tratada e coleta de esgoto por município (AguaViva — SANE-01).

    Indicadores IN023_AE (água) e IN015_AE (esgoto) do SNIS.
    404 quando não há dado SNIS para o município.
    """
    return await AguaVivaFacade(session).agua_viva(codigo_ibge=codigo_ibge)


@router.get("/esgoto-invisivel/{codigo_ibge}", response_model=EsgotoInvisivelOut)
async def esgoto_invisivel(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> EsgotoInvisivelOut:
    """Gap entre cobertura de água e esgoto por município (EsgotoInvisível — SANE-03).

    Onde a água chega mas o esgoto some — mede o efluente não coletado (IN015_AE do SNIS).
    Níveis: adequado (≥ 70 %), atenção (40–69 %), crítico (< 40 %).
    404 quando não há dado SNIS de esgoto para o município.
    """
    return await EsgotoInvisivelFacade(session).esgoto_invisivel(codigo_ibge=codigo_ibge)


@router.get("/luz-no-mapa/{codigo_ibge}", response_model=LuzNoMapaOut)
async def luz_no_mapa(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> LuzNoMapaOut:
    """Qualidade do fornecimento de energia elétrica no município (LuzNoMapa — SANE-04).

    Indicadores DEC (horas de interrupção por consumidor/ano) e FEC (interrupções/consumidor/ano)
    da ANEEL. Menor é melhor. 404 quando não há dado ANEEL para o município.
    """
    return await LuzNoMapaFacade(session).luz_no_mapa(codigo_ibge=codigo_ibge)


@router.get("/rio-em-risco/{codigo_ibge}", response_model=RioEmRiscoOut)
async def rio_em_risco(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> RioEmRiscoOut:
    """Risco hídrico de seca por município — ANA Monitor de Secas (RioEmRisco — SANE-02).

    Índice de seca (0–5: Normal=0, D0=1, D1=2, D2=3, D3=4, D4=5), pior mês do exercício.
    Níveis: normal (< D0), atencao (D0–D1), critico (D2–D4).
    404 quando não há dado ANA para o município.
    """
    return await RioEmRiscoFacade(session).rio_em_risco(codigo_ibge=codigo_ibge)


@router.get("/prato-frio/{codigo_ibge}", response_model=PratoFrioOut)
async def prato_frio(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> PratoFrioOut:
    """Produção agrícola municipal per capita — IBGE PAM (PratoFrio — ALIM-01).

    Valor total da produção (lavouras temporárias + permanentes, variável 762) em BRL por habitante.
    Níveis: alta (≥ R$ 5.000/hab/ano), moderada (≥ R$ 500/hab/ano), baixa (< R$ 500/hab/ano).
    Produção varia por bioma/clima — use como contexto, não ranking. Forma a confirmar na 1ª busca
    real (servicodados.ibge.gov.br). 404 quando não há dado PAM para o município.
    """
    return await PratoFrioFacade(session).prato_frio(codigo_ibge=codigo_ibge)


@router.get("/semeando-transparencia/{codigo_ibge}", response_model=SemeandoTransparenciaOut)
async def semeando_transparencia(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> SemeandoTransparenciaOut:
    """Investimento municipal em agricultura — SICONFI Função 20 (ALIM-05).

    Despesa liquidada na função 20 por habitante. Níveis: alto (≥ R$100/hab/ano),
    moderado (≥ R$10), baixo (< R$10). 404 quando não há dado SICONFI.
    """
    return await SemeandoTransparenciaFacade(session).semeando_transparencia(
        codigo_ibge=codigo_ibge
    )


@router.get("/fome-oculta/{codigo_ibge}", response_model=FomeOcultaOut)
async def fome_oculta(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> FomeOcultaOut:
    """Insegurança nutricional de crianças < 5 anos — SISVAN/MS (ALIM-02).

    % de crianças < 5 com magreza ou magreza acentuada acompanhadas pelo SISVAN.
    Níveis: crítico (≥ 10%), elevado (≥ 5%), moderado (≥ 2%), baixo (< 2%).
    404 quando não há dado SISVAN para o município.
    """
    return await FomeOcultaFacade(session).fome_oculta(codigo_ibge=codigo_ibge)


@router.get("/sentinela-materna/{codigo_ibge}", response_model=SentinelaMaternаOut)
async def sentinela_materna(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> SentinelaMaternаOut:
    """Risco nutricional de gestantes acompanhadas pelo SISVAN/MS (SAUDE-03).

    % de gestantes com baixo peso (IMC pré-gestacional) acompanhadas pelo SISVAN.
    Níveis: crítico (≥ 30%), elevado (≥ 20%), moderado (≥ 10%), baixo (< 10%).
    Dado de origem sensível: células abaixo de 5 gestantes são suprimidas (k-anonimato).
    404 quando não há dado SISVAN gestante para o município.
    """
    return await SentinelaMaternаFacade(session).sentinela_materna(codigo_ibge=codigo_ibge)


@router.get("/cacador-arboviroses/{codigo_ibge}", response_model=CacadorArboviroesOut)
async def cacador_arboviroses(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> CacadorArboviroesOut:
    """Casos confirmados de dengue/100k hab. 404 quando não há dado SINAN.

    Incidência de dengue confirmada (CLASSI_FIN 1-3) do SINAN/MS por município/ano.
    Níveis: crítico (≥ 300/100k → epidemia), elevado (≥ 100/100k → alto risco),
    moderado (≥ 20/100k), baixo (< 20/100k).
    Inclui k-anonimato (n_minimo=5) — municípios com < 5 casos têm dado suprimido.
    """
    return await CacadorArbovirosesFacade(session).cacador_arboviroses(codigo_ibge=codigo_ibge)


@router.get("/pressao-sus/{codigo_ibge}", response_model=PressaoSusOut)
async def pressao_sus(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> PressaoSusOut:
    """Capacidade de financiamento do SUS local — SICONFI Função 10 (SAUDE-11).

    Despesa liquidada na função 10 (Saúde) por habitante. Proxy estrutural de pressão
    sobre profissionais de saúde: financiamento insuficiente → sistema sobrecarregado.
    Níveis: adequado (≥ R$500/hab/ano), atenção (≥ R$200), crítico (< R$200).
    404 quando não há dado SICONFI para o município.
    """
    return await PressaoSusFacade(session).pressao_sus(codigo_ibge=codigo_ibge)


@router.get("/casa-viva/{codigo_ibge}", response_model=CasaVivaOut)
async def casa_viva(codigo_ibge: str, session: AsyncSession = Depends(get_session)) -> CasaVivaOut:
    """Investimento municipal em habitação — SICONFI Função 16 (HAB-02).

    Despesa liquidada na função 16 (Habitação) por habitante. Proxy do compromisso
    orçamentário com política habitacional. Não inclui recursos federais (MCMV/FGTS)
    que não transitam pelo orçamento municipal.
    Níveis: expressivo (≥ R$50/hab/ano), moderado (≥ R$10), incipiente (< R$10).
    404 quando não há dado SICONFI para o município.
    """
    return await CasaVivaFacade(session).casa_viva(codigo_ibge=codigo_ibge)


@router.get("/via-viva/{codigo_ibge}", response_model=ViaVivaOut)
async def via_viva(codigo_ibge: str, session: AsyncSession = Depends(get_session)) -> ViaVivaOut:
    """Investimento municipal em transporte — SICONFI Função 26 (MOB-01).

    Despesa liquidada na função 26 (Transporte) por habitante. Proxy do compromisso
    orçamentário com infraestrutura de transporte e mobilidade urbana. Não inclui obras
    estaduais/federais (rodovias, metrôs) fora do orçamento municipal.
    Níveis: elevado (≥ R$300/hab/ano), moderado (≥ R$80), baixo (< R$80).
    404 quando não há dado SICONFI para o município.
    """
    return await ViaVivaFacade(session).via_viva(codigo_ibge=codigo_ibge)


@router.get("/eco-vivo/{codigo_ibge}", response_model=EcoVivaOut)
async def eco_vivo(codigo_ibge: str, session: AsyncSession = Depends(get_session)) -> EcoVivaOut:
    """Investimento municipal em gestão ambiental — SICONFI Função 18 (AMB-01).

    Despesa liquidada na função 18 (Gestão Ambiental) por habitante. Proxy do compromisso
    orçamentário com proteção ambiental local. Não inclui recursos federais/estaduais
    (IBAMA, ICMBio) fora do orçamento municipal.
    Níveis: expressivo (≥ R$30/hab/ano), moderado (≥ R$5), incipiente (< R$5).
    404 quando não há dado SICONFI para o município.
    """
    return await EcoVivaFacade(session).eco_vivo(codigo_ibge=codigo_ibge)


@router.get("/escola-viva/{codigo_ibge}", response_model=EscolaVivaOut)
async def escola_viva(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> EscolaVivaOut:
    """Investimento municipal em educação — SICONFI Função 12 (EDU-03).

    Despesa liquidada na função 12 (Educação) por habitante. Proxy do esforço orçamentário
    com o ensino público municipal. Não inclui repasses diretos do FNDE/FUNDEB fora do
    liquidado municipal. CF/88 exige mínimo de 25% da receita em educação.
    Níveis: expressivo (≥ R$600/hab/ano), moderado (≥ R$200), incipiente (< R$200).
    404 quando não há dado SICONFI para o município.
    """
    return await EscolaVivaFacade(session).escola_viva(codigo_ibge=codigo_ibge)


@router.get("/sane-fundo/{codigo_ibge}", response_model=SaneFundoOut)
async def sane_fundo(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> SaneFundoOut:
    """Investimento municipal em saneamento — SICONFI Função 17 (SANE-05).

    Despesa liquidada na função 17 (Saneamento) por habitante. Proxy do esforço orçamentário
    direto com saneamento básico. Em municípios com concessão estadual (SABESP, COPASA),
    o gasto municipal pode ser próximo de zero mesmo com boa cobertura.
    Use em conjunto com AguaViva (SANE-01) para contexto real de cobertura.
    Níveis: expressivo (≥ R$60/hab/ano), moderado (≥ R$15), incipiente (< R$15).
    404 quando não há dado SICONFI para o município.
    """
    return await SaneFundoFacade(session).sane_fundo(codigo_ibge=codigo_ibge)


@router.get("/assis-viva/{codigo_ibge}", response_model=AssisVivaOut)
async def assis_viva(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> AssisVivaOut:
    """Investimento municipal em assistência social — SICONFI Função 08 (SOCIAL-01).

    Despesa liquidada na função 08 (Assistência Social) por habitante. Proxy do esforço
    orçamentário com CRAS/CREAS e benefícios municipais do SUAS. Não inclui transferências
    federais (Bolsa Família, BPC) que não transitam pelo liquidado municipal.
    Níveis: expressivo (≥ R$150/hab/ano), moderado (≥ R$50), incipiente (< R$50).
    404 quando não há dado SICONFI para o município.
    """
    return await AssisVivaFacade(session).assis_viva(codigo_ibge=codigo_ibge)


@router.get("/cultura-viva/{codigo_ibge}", response_model=CulturaVivaOut)
async def cultura_viva(
    codigo_ibge: str, session: AsyncSession = Depends(get_session)
) -> CulturaVivaOut:
    """Investimento municipal em cultura — SICONFI Função 13 (CULT-01).

    Despesa liquidada na função 13 (Cultura) por habitante. Proxy do compromisso orçamentário
    com equipamentos e políticas culturais locais (bibliotecas, museus, teatros). Não inclui
    recursos da Lei Rouanet nem fundos estaduais/federais fora do orçamento municipal.
    Níveis: expressivo (≥ R$30/hab/ano), moderado (≥ R$10), incipiente (< R$10).
    404 quando não há dado SICONFI para o município.
    """
    return await CulturaVivaFacade(session).cultura_viva(codigo_ibge=codigo_ibge)
